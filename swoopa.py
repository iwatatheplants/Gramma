#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  GRAMMA — Swoopa Pipeline v3                            ║
║  Two-Stage: Fast pre-screen → Full multi-source comps          ║
║  Photos in every notification                                  ║
╚══════════════════════════════════════════════════════════════════╝

SPEED:
  Stage 1 — Haiku pre-screen (1-2s): filters junk instantly
  Stage 2 — Sonnet + web search (10-20s): only on promising items
  ~80% of alerts filtered in 1-2 seconds

SETUP:
  pip install requests beautifulsoup4
  Gmail App Password: myaccount.google.com → Security → App passwords
  Set CONFIG below, run: python3 swoopa_pipeline.py
"""

import imaplib, email, requests, json, time, re, os, sys, logging, hashlib
from email.header import decode_header
from datetime import datetime, timedelta
from pathlib import Path

CONFIG = {
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE"),
    "gmail_address": "YOUR_EMAIL@gmail.com",
    "gmail_app_password": "YOUR_APP_PASSWORD_HERE",
    "swoopa_sender_patterns": ["swoopa","getswoopa","noreply@getswoopa.com","alerts@getswoopa.com"],
    "ntfy_topic": "gramma-CHANGEME",
    "poll_interval_seconds": 10,
    "notify_verdicts": ["STRONG BUY", "BUY"],
    "max_eval_price": 600,
    "mark_as_read": True,
    "data_dir": "scout_data",
}

PRESCREEN_PROMPT = """You are a vintage furniture/clothing arbitrage pre-screener. Quickly decide if a listing is worth full evaluation.

Respond with ONLY valid JSON: {"pass": true/false, "reason": "one sentence"}

pass=true (skip): Generic mass-market (IKEA, Target, Ashley), clearly damaged, baby/mattress/appliance, fast-fashion.
pass=false (evaluate): ANY mention of vintage/MCM/Danish/teak/walnut, ANY designer brand, FREE real furniture, "moving"/"estate sale"/"must go", suspiciously low price, ambiguous but possibly valuable.

WHEN IN DOUBT → pass=false. Missing a deal is worse than a wasted API call. ONLY JSON."""

FULL_PROMPT = """You are Gramma, a warm but sharp AI vintage appraiser for SF Bay Area.

Use web search for REAL prices from MULTIPLE sources:
a) eBay sold - "[brand] [model] sold"
b) 1stDibs - "1stdibs [brand] [model]"
c) Chairish - "chairish [brand] [model]"
d) Clothing: "poshmark [brand] [item] sold"

Respond ONLY with valid JSON:
{
  "identified": boolean, "confidence": "high"|"medium"|"low",
  "brand_or_designer": "string", "specific_model": "string or null",
  "item_type": "string", "era": "string",
  "market_data": {
    "ebay_sold": [{"title":"str","price":num}],
    "firstdibs_active": [{"title":"str","price":num}],
    "chairish_active": [{"title":"str","price":num}],
    "poshmark_sold": [{"title":"str","price":num}],
    "data_quality_note": "str"
  },
  "estimated_resale_low": num, "estimated_resale_high": num, "resale_ceiling": num,
  "profit_score": 1-10,
  "verdict": "STRONG BUY"|"BUY"|"MAYBE"|"PASS",
  "verdict_reason": "cite specific comp prices as evidence",
  "what_to_check": "str", "comp_search_terms": "str",
  "flip_time_estimate": "str", "negotiation_tip": "str",
  "ai_price_assessment": "underpriced"|"fair"|"overpriced"|"unknown"
}

Search 2-3+ sources. eBay=floor, 1stDibs=ceiling, Chairish=mid.
STRONG BUY=3x+. BUY=2x+. FREE+brand=STRONG BUY. Cite prices. ONLY JSON."""


def extract_images_from_email(msg):
    """Extract image URLs from Swoopa alert email HTML."""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                pl = part.get_payload(decode=True)
                if pl: html_body = pl.decode("utf-8","replace")
    else:
        pl = msg.get_payload(decode=True)
        if pl and msg.get_content_type() == "text/html":
            html_body = pl.decode("utf-8","replace")

    if not html_body:
        return None

    # Look for listing images in the email (Swoopa typically includes thumbnails)
    img_patterns = [
        # Facebook Marketplace CDN images
        r'(https?://scontent[^"\'<>\s]+\.(?:jpg|jpeg|png|webp)[^"\'<>\s]*)',
        # OfferUp images
        r'(https?://(?:images|photos)\.offerup\.com/[^"\'<>\s]+)',
        # Generic listing images (not tracking pixels or logos)
        r'<img[^>]+src=["\']?(https?://[^"\'<>\s]+\.(?:jpg|jpeg|png|webp)[^"\'<>\s]*)["\']?',
    ]

    for pattern in img_patterns:
        matches = re.findall(pattern, html_body, re.IGNORECASE)
        for url in matches:
            # Skip tiny tracking pixels and Swoopa branding
            if any(skip in url.lower() for skip in ["pixel","track","logo","swoopa","icon","badge","1x1","spacer","email"]):
                continue
            return url

    return None


def fetch_og_image(url):
    """Fetch og:image from a listing page."""
    if not url: return None
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            m = re.search(r'<meta\s+(?:property|name)=["\']og:image["\']\s+content=["\']([^"\']+)["\']', r.text, re.I)
            if m: return m.group(1)
            m = re.search(r'content=["\']([^"\']+)["\']\s+(?:property|name)=["\']og:image["\']', r.text, re.I)
            if m: return m.group(1)
    except: pass
    return None


def parse_email(msg):
    """Parse Swoopa alert email into listing data."""
    subj = " ".join(p.decode(e or "utf-8","replace") if isinstance(p,bytes) else p for p,e in decode_header(msg.get("Subject","")))

    html_b = txt_b = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct=part.get_content_type(); pl=part.get_payload(decode=True)
            if pl:
                if ct=="text/html": html_b=pl.decode("utf-8","replace")
                elif ct=="text/plain": txt_b=pl.decode("utf-8","replace")
    else:
        pl=msg.get_payload(decode=True)
        if pl:
            t=pl.decode("utf-8","replace")
            if msg.get_content_type()=="text/html": html_b=t
            else: txt_b=t

    body = txt_b or re.sub(r'<[^>]+>',' ',html_b).strip() if html_b else ""

    title = re.sub(r'^(New listing|Alert|Swoopa|New match|Deal alert)[:\s-]*','',subj,flags=re.I).strip()
    if len(title)<10:
        for l in body.split("\n")[:10]:
            l=l.strip()
            if len(l)>15 and not l.startswith("http"): title=l[:200]; break

    price=None
    for pat in [r'\$(\d{1,3}(?:,\d{3})*)',r'Price:\s*\$?(\d[\d,]*)',r'Asking\s*\$?(\d[\d,]*)']:
        m=re.search(pat,subj+" "+body)
        if m:
            try: price=int(m.group(1).replace(",","")); break
            except: continue
    if price is None and re.search(r'\bfree\b',subj+" "+body,re.I): price=0

    url=None
    for pat in [r'(https?://(?:www\.)?facebook\.com/marketplace/item/\d+[^\s<"\']*)',
        r'(https?://(?:\w+\.)?craigslist\.org/[^\s<"\']+)',
        r'(https?://(?:www\.)?offerup\.com/item/[^\s<"\']+)',
        r'(https?://(?:www\.)?nextdoor\.com/[^\s<"\']*)',]:
        m=re.search(pat, html_b or body)
        if m: url=re.sub(r'[)\]}>.,;]+$','',m.group(1)); break
    if not url:
        for u in re.findall(r'(https?://[^\s<"\']+)', html_b or body):
            if "swoopa" not in u.lower() and "unsubscribe" not in u.lower():
                url=re.sub(r'[)\]}>.,;]+$','',u); break

    plat="Unknown"
    cb=(subj+" "+body).lower()
    for kw,nm in [("facebook","Facebook Marketplace"),("craigslist","Craigslist"),("offerup","OfferUp"),("nextdoor","Nextdoor")]:
        if kw in cb: plat=nm; break

    # Extract image from email
    image_url = extract_images_from_email(msg)
    # If no image in email, try fetching from listing page
    if not image_url and url:
        image_url = fetch_og_image(url)

    desc_lines=[]
    for l in body.split("\n"):
        l=l.strip()
        if not l or any(s in l.lower() for s in ["unsubscribe","manage pref","swoopa","©","privacy"]): continue
        if len(l)>10: desc_lines.append(l)
        if len(desc_lines)>=8: break

    return {"subject":subj,"title":title,"price":price,"url":url,"platform":plat,
            "description":" ".join(desc_lines)[:500],"image_url":image_url}


class Pipeline:
    def __init__(self):
        self.dd=Path(CONFIG["data_dir"]); self.dd.mkdir(exist_ok=True)
        self.lf=self.dd/"swoopa_log.jsonl"; self.sf=self.dd/"swoopa_seen.json"
        self.seen=self._load(); self.mail=None; self.connected=False
        self.stats={"proc":0,"prescreened":0,"filtered":0,"strong":0,"buys":0,"maybes":0,"passes":0,"errors":0}
        logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler(self.dd/"swoopa.log")])
        self.log=logging.getLogger("Swoopa")

    def _load(self):
        if self.sf.exists():
            try:
                d=json.loads(self.sf.read_text()); cut=(datetime.now()-timedelta(days=7)).isoformat()
                return {k:v for k,v in d.items() if v.get("ts","")>cut}
            except: return {}
        return {}
    def _save(self): self.sf.write_text(json.dumps(self.seen,indent=2))

    def connect(self):
        a,p=CONFIG["gmail_address"],CONFIG["gmail_app_password"]
        if a=="YOUR_EMAIL@gmail.com": raise ValueError("Set Gmail credentials!")
        self.mail=imaplib.IMAP4_SSL("imap.gmail.com",993)
        self.mail.login(a,p); self.mail.select("INBOX"); self.connected=True

    def reconnect(self):
        try: self.mail.noop(); return
        except: pass
        try: self.mail.logout()
        except: pass
        self.connected=False; self.connect()

    def search_emails(self):
        if not self.connected: self.reconnect()
        ids=[]
        try:
            for pat in CONFIG["swoopa_sender_patterns"]:
                _,mi=self.mail.search(None,f'(UNSEEN FROM "{pat}")')
                if mi[0]: ids.extend(mi[0].split())
            return list(set(ids))
        except: self.reconnect(); return []

    def api_call(self, model, system, prompt, web_search=False, timeout=15):
        k=CONFIG["anthropic_api_key"]
        if k=="YOUR_API_KEY_HERE": return None
        body={"model":model,"max_tokens":2000 if web_search else 300,"system":system,
            "messages":[{"role":"user","content":prompt}]}
        if web_search: body["tools"]=[{"type":"web_search_20250305","name":"web_search"}]
        try:
            r=requests.post("https://api.anthropic.com/v1/messages",
                headers={"Content-Type":"application/json","x-api-key":k,"anthropic-version":"2023-06-01"},
                json=body,timeout=timeout)
            r.raise_for_status()
            txt="".join(b["text"] for b in r.json()["content"] if b["type"]=="text")
            m=re.search(r'\{[\s\S]*\}',txt.replace("```json","").replace("```","").strip())
            return json.loads(m.group(0)) if m else None
        except Exception as e: self.log.error(f"API ({model}): {e}"); return None

    def notify(self, listing, ev):
        topic=CONFIG["ntfy_topic"]
        if topic=="gramma-CHANGEME": return
        v=ev.get("verdict","?"); brand=ev.get("brand_or_designer","?")
        rl,rh=ev.get("estimated_resale_low",0),ev.get("estimated_resale_high",0)
        p=listing.get("price"); ceil=ev.get("resale_ceiling",0); md=ev.get("market_data",{})

        if p and p>0: prof=f"+${int((rl+rh)/2-p)} ({int(((rl+rh)/2/p-1)*100)}%)"
        elif p==0: prof=f"FREE → ${rl}-${rh}"
        else: prof=f"${rl}-${rh}"

        comps=[]
        for c in (md.get("ebay_sold") or [])[:2]: comps.append(f"eBay: ${c.get('price','?')}")
        for c in (md.get("firstdibs_active") or [])[:1]: comps.append(f"1stDibs: ${c.get('price','?')}")
        for c in (md.get("chairish_active") or [])[:1]: comps.append(f"Chairish: ${c.get('price','?')}")

        title_str=f"{'⚡' if v=='STRONG BUY' else '✓'} {v}: {brand}"
        body=(f"📍 {listing.get('platform','?')}\n{listing.get('title','?')}\n\n"
            f"💰 Ask: {'FREE' if p==0 else f'${p}' if p else '?'}\n"
            f"📈 Resale: ${rl}-${rh}{f' (ceil ${ceil})' if ceil else ''}\n"
            f"🔥 {prof}\n📊 Score: {ev.get('profit_score','?')}/10\n\n"
            f"📊 COMPS:\n"+("\n".join(comps) if comps else "None")+"\n\n"
            f"👁 {ev.get('what_to_check','')[:100]}")

        headers={"Title":title_str,"Priority":"5" if v=="STRONG BUY" else "4",
            "Tags":"moneybag" if v=="STRONG BUY" else "chart_with_upwards_trend"}
        if listing.get("url"):
            headers["Click"]=listing["url"]
            headers["Actions"]=f"view, Open Listing, {listing['url']}"
        # ── PHOTO ATTACHMENT ──
        if listing.get("image_url"):
            headers["Attach"] = listing["image_url"]

        try:
            requests.post(f"https://ntfy.sh/{topic}",data=body.encode("utf-8"),headers=headers,timeout=10)
            self.log.info(f"📱 {title_str}" + (" 📷" if listing.get("image_url") else ""))
        except Exception as e: self.log.error(f"ntfy: {e}")

    def process_email(self, mid):
        try: _,d=self.mail.fetch(mid,"(RFC822)"); msg=email.message_from_bytes(d[0][1])
        except: return
        listing = parse_email(msg)

        lid=hashlib.md5((listing.get("title","")+str(listing.get("price",""))).encode()).hexdigest()
        if lid in self.seen:
            if CONFIG["mark_as_read"]: self.mail.store(mid,"+FLAGS","\\Seen")
            return
        self.seen[lid]={"ts":datetime.now().isoformat(),"title":listing.get("title","")[:100]}

        if listing.get("price") is not None and listing["price"]>CONFIG["max_eval_price"]:
            if CONFIG["mark_as_read"]: self.mail.store(mid,"+FLAGS","\\Seen")
            return

        # ── STAGE 1: Pre-screen (~1-2s) ──
        self.stats["prescreened"]+=1
        price_str = f"${listing['price']}" if listing.get('price') is not None else "?"
        prompt=f"Title: {listing.get('title','?')}\nPrice: {price_str}\nPlatform: {listing.get('platform','?')}"
        ps = self.api_call("claude-haiku-4-5-20251001", PRESCREEN_PROMPT, prompt, web_search=False, timeout=10)
        if ps and ps.get("pass")==True:
            self.stats["filtered"]+=1
            self.log.debug(f"  ⏭ Skip: {listing.get('title','?')[:50]}")
            if CONFIG["mark_as_read"]: self.mail.store(mid,"+FLAGS","\\Seen")
            return

        price_display = "FREE" if listing.get("price") == 0 else f"${listing.get('price', '?')}"
        self.log.info(f"🔍 Stage 2: {listing.get('title','?')[:55]} — "
            f"{price_display} "
            f"[{listing.get('platform','?')}]"
            + (" 📷" if listing.get("image_url") else ""))

        # ── STAGE 2: Full eval (~10-20s) ──
        price_prompt = f"${listing['price']}" if listing.get('price') is not None else "?"
        free_tag = " (FREE)" if listing.get('price') == 0 else ""
        prompt2=(f"Evaluate this listing:\nTitle: {listing.get('title','?')}\n"
            f"Price: {price_prompt}{free_tag}\n"
            f"Platform: {listing.get('platform','?')}\nDescription: {listing.get('description','')[:500]}\n"
            f"Location: SF Bay Area")
        ev = self.api_call("claude-sonnet-4-20250514", FULL_PROMPT, prompt2, web_search=True, timeout=45)

        if not ev: self.stats["errors"]+=1; self.mail.store(mid,"+FLAGS","\\Seen") if CONFIG["mark_as_read"] else None; return

        v=ev.get("verdict","PASS"); md=ev.get("market_data",{})
        nc=sum(len(md.get(k,[]) or []) for k in ["ebay_sold","firstdibs_active","chairish_active","poshmark_sold"])
        self.stats["proc"]+=1; self.stats[{"STRONG BUY":"strong","BUY":"buys","MAYBE":"maybes"}.get(v,"passes")]+=1

        ic={"STRONG BUY":"⚡","BUY":"✓","MAYBE":"?","PASS":"✕"}.get(v,"·")
        self.log.info(f"  {ic} {v} | {ev.get('brand_or_designer','?')} | ${ev.get('estimated_resale_low',0)}-${ev.get('estimated_resale_high',0)} | {nc} comps")

        with open(self.lf,"a") as f: f.write(json.dumps({"ts":datetime.now().isoformat(),"listing":{k:v2 for k,v2 in listing.items()},"eval":ev})+"\n")
        if v in CONFIG["notify_verdicts"]: self.notify(listing,ev)
        if CONFIG["mark_as_read"]: self.mail.store(mid,"+FLAGS","\\Seen")

    def cycle(self):
        ids=self.search_emails()
        if ids: self.log.info(f"📬 {len(ids)} new Swoopa alert(s)")
        for mid in ids:
            try: self.process_email(mid); time.sleep(0.3)
            except Exception as e: self.log.error(f"Email: {e}"); self.stats["errors"]+=1
        self._save(); return len(ids)

    def run(self):
        print("\n"+"="*62)
        print("  ◈  GRAMMA — Swoopa Pipeline v3")
        print("     Two-Stage: Haiku pre-screen → Sonnet full analysis")
        print("     Photos in notifications · Multi-source comps")
        print(f"     Gmail: {CONFIG['gmail_address']}")
        print(f"     Poll: every {CONFIG['poll_interval_seconds']}s")
        print("="*62+"\n")
        if CONFIG["anthropic_api_key"]=="YOUR_API_KEY_HERE": print("❌ Set ANTHROPIC_API_KEY"); sys.exit(1)
        self.log.info("Connecting to Gmail...")
        try: self.connect(); self.log.info("✅ Gmail connected")
        except Exception as e: print(f"❌ {e}"); sys.exit(1)
        c=0
        try:
            while True:
                c+=1
                try: self.cycle()
                except Exception as e: self.log.error(f"Cycle: {e}")
                if c%60==0:
                    s=self.stats
                    filt=f"{s['filtered']/max(s['prescreened'],1)*100:.0f}%" if s['prescreened'] else "0%"
                    self.log.info(f"💓 #{c} | Pre: {s['prescreened']} ({filt} filtered) | Eval: {s['proc']} | ⚡{s['strong']} ✓{s['buys']}")
                    self.reconnect()
                time.sleep(CONFIG["poll_interval_seconds"])
        except KeyboardInterrupt:
            s=self.stats; print(f"\n🛑 Pre: {s['prescreened']} | Filtered: {s['filtered']} | Eval: {s['proc']}"); self._save()

def review(vf=None):
    lf=Path(CONFIG["data_dir"])/"swoopa_log.jsonl"
    if not lf.exists(): print("No log."); return
    entries=[json.loads(l) for l in lf.read_text().strip().split("\n") if l.strip()]
    if vf: entries=[e for e in entries if e.get("eval",{}).get("verdict")==vf.upper()]
    print(f"\n{'='*80}\n  SWOOPA LOG — {len(entries)} entries\n{'='*80}")
    for e in entries:
        ev=e.get("eval",{});li=e.get("listing",{});md=ev.get("market_data",{})
        v=ev.get("verdict","?");ic={"STRONG BUY":"⚡","BUY":"✓","MAYBE":"?","PASS":"✕"}.get(v,"·")
        p=li.get("price"); ps="FREE" if p==0 else f"${p}" if p else "?"
        print(f"\n  {ic} {v:12s} | {ev.get('brand_or_designer','?'):25s} | Ask: {ps:>6s} → ${ev.get('estimated_resale_low',0)}-${ev.get('estimated_resale_high',0)}")
        print(f"    [{li.get('platform','?')}] {li.get('title','?')[:70]}")
        for c in (md.get("ebay_sold") or [])[:2]: print(f"    eBay: {c.get('title','')[:45]} → ${c.get('price','?')}")
        if li.get("image_url"): print(f"    📷 {li['image_url'][:80]}")

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1].lower()=="review":
        review(sys.argv[2] if len(sys.argv)>2 else None)
    else: Pipeline().run()
