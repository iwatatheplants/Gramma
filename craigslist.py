#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  GRAMMA — Craigslist Monitor v4 (Optimized)             ║
║  5 broad feeds · 10-second polling · ~10-15s to your phone     ║
║  Two-stage AI · Multi-source comps · Photos in notifications   ║
╚══════════════════════════════════════════════════════════════════╝

SPEED ARCHITECTURE:
  Old: 12 narrow feeds × 30s = new listings in 30-54 seconds
  New: 5 broad feeds × 10s  = new listings in 10-15 seconds

  Each cycle: ~5 feeds × ~1s each = ~5 seconds per cycle
  Poll every 10 seconds → near real-time coverage

  Stage 1: Haiku pre-screen (1-2s, no web search, filters ~80%)
  Stage 2: Sonnet full analysis (10-20s, multi-source web search)

SETUP:
  pip install feedparser requests
  export ANTHROPIC_API_KEY="sk-ant-..."
  Set ntfy_topic below → run: python3 craigslist.py

COMMANDS:
  python3 craigslist.py          # Run monitor
  python3 craigslist.py test     # Test all feeds
  python3 craigslist.py review   # Review logged results
  python3 craigslist.py review "STRONG BUY"
"""

import feedparser, requests, json, time, os, sys, hashlib, logging, re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════

CONFIG = {
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY_HERE"),
    "ntfy_topic": "gramma-CHANGEME",
    "craigslist_region": "sfbay",

    # ── SPEED SETTINGS ──
    "poll_interval_seconds": 10,     # How often to check all feeds
    "pause_between_feeds": 0.8,      # Seconds between each feed request (rate limiting)
    "pause_between_evals": 0.3,      # Seconds between API calls

    "notify_verdicts": ["STRONG BUY", "BUY"],
    "max_eval_price": 600,
    "data_dir": "scout_data",
}

# ══════════════════════════════════════════════════════════════════
# CONSOLIDATED SEARCHES — 5 broad feeds instead of 12 narrow ones
# ══════════════════════════════════════════════════════════════════
#
# Craigslist OR syntax: word1|word2|word3 = match ANY
# Craigslist AND syntax: word1 word2 = match BOTH
# Categories: fua=furniture, cla=clothing, zip=free, atq=antiques, sss=all for sale
#
# Strategy: fewer feeds with broad OR queries → Haiku filters the junk
# This gives us faster cycle times AND better coverage

SEARCHES = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEED 1: All high-value furniture brands in one feed
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "name": "🪑 Designer Furniture",
        "query": (
            "eames|herman miller|knoll|saarinen|noguchi|wegner|jacobsen"
            "|bertoia|tulip table|womb chair|nelson bench|barcelona chair"
            "|fritz hansen|egg chair|swan chair|wishbone|shell chair"
            # Tier 2 brands
            "|broyhill brasilia|heywood wakefield|lane acclaim|drexel declaration"
            "|kent coffey|paul mccobb|planner group|thayer coggin|milo baughman"
            "|adrian pearsall|craft associates|westnofa|florence knoll"
            # Tier 3
            "|henredon|baker furniture|thomasville"
        ),
        "category": "fua",
        "min_price": 0,
        "max_price": 500,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEED 2: MCM style keywords + materials + urgency signals
    # Catches unbranded pieces that sellers don't know are valuable
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "name": "🪑 MCM & Vintage Style",
        "query": (
            "mid century|danish modern|danish teak|mcm furniture"
            "|vintage credenza|vintage dresser|vintage sideboard"
            "|walnut sideboard|teak sideboard|rosewood|walnut credenza"
            "|vintage sofa|vintage couch leather|vintage lounge chair"
            "|vintage desk|vintage dining|vintage cabinet|vintage bookcase"
            "|retro furniture|atomic age|space age"
            # Urgency + moving signals (goldmine for underpriced deals)
            "|moving sale furniture|estate sale furniture|downsizing furniture"
            "|everything must go|need gone today|must pick up"
        ),
        "category": "fua",
        "min_price": 0,
        "max_price": 400,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEED 3: FREE STUFF — highest ROI, zero risk
    # Broad terms to catch anything that could be real furniture
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "name": "🆓 Free Stuff",
        "query": (
            "furniture|dresser|table|chair|desk|sofa|couch|credenza"
            "|shelf|shelves|bookcase|cabinet|hutch|buffet|sideboard"
            "|dining|armoire|nightstand|end table|coffee table"
            "|lamp|chandelier|mirror|rug"
            # Wealthy neighborhood keywords
            "|pacific heights|atherton|hillsborough|palo alto|menlo park"
            "|mill valley|tiburon|sausalito|piedmont|berkeley hills"
            "|ross|larkspur|burlingame|san mateo|los altos|woodside"
            "|curb alert|free pickup|front porch|come get"
        ),
        "category": "zip",
        "min_price": 0,
        "max_price": 0,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEED 4: Designer clothing + vintage fashion
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "name": "👔 Designer Clothing",
        "query": (
            # Tier 1 luxury
            "gucci|chanel|prada|hermes|burberry|ysl|louis vuitton"
            "|vivienne westwood|balenciaga|givenchy|valentino|fendi|celine"
            # Tier 2 designer
            "|thierry mugler|jean paul gaultier|comme des garcons|issey miyake"
            "|maison margiela|rick owens|acne studios|isabel marant"
            "|diane von furstenburg|halston|escada|versace|moschino"
            # Tier 3 vintage staples
            "|vintage levis|carhartt jacket|vintage nike|vintage champion"
            "|patagonia|polo sport|ralph lauren vintage"
            "|vintage leather jacket|vintage denim|vintage band tee"
        ),
        "category": "cla",
        "min_price": 0,
        "max_price": 200,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEED 5: Antiques section — often has MCM mislabeled
    # Plus estate/moving sales across all categories
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "name": "🏺 Antiques & Estate Sales",
        "query": (
            "mid century|danish|teak|walnut|vintage modern|retro"
            "|eames|knoll|herman miller|danish design|scandinavian"
            "|estate sale|moving sale|downsizing|liquidation"
            "|vintage lighting|vintage lamp|vintage chandelier"
            "|vintage rug|kilim|persian"
            "|vintage art|oil painting|lithograph|signed print"
        ),
        "category": "atq",
        "min_price": 0,
        "max_price": 500,
    },
]

# ══════════════════════════════════════════════════════════════════
# AI PROMPTS
# ══════════════════════════════════════════════════════════════════

PRESCREEN_PROMPT = """You are a vintage furniture/clothing arbitrage pre-screener. Quickly decide if a Craigslist listing is worth a full AI evaluation with web search.

Respond with ONLY valid JSON: {"pass": true/false, "reason": "one sentence"}

pass=true (SKIP — not worth evaluating):
- Generic mass-market: IKEA, Target, Wayfair, Ashley, Rooms To Go, Bob's, Amazon basics
- Clearly damaged beyond profitable repair: "broken", "water damage", "mold", "infested"
- Non-vintage categories: baby furniture, mattresses, appliances, exercise equipment, office cubicles
- Fast-fashion clothing: H&M, Zara, Shein, Forever 21, Primark, Old Navy, Gap (non-vintage)
- Generic modern items with no vintage/design value

pass=false (SEND TO FULL EVALUATION):
- ANY designer/brand name (Herman Miller, Knoll, Eames, Wegner, Gucci, Chanel, Levi's, etc.)
- ANY vintage/MCM keywords: mid century, danish, teak, walnut, rosewood, retro, atomic, vintage
- ANY quality material mentions: solid wood, hardwood, brass, chrome, leather, silk, cashmere, wool
- FREE items that could be real furniture (not particle board)
- Urgency language: "moving", "must go", "estate", "downsizing", "need gone", "first come"
- Wealthy neighborhood names in the listing
- Price seems suspiciously low for what's described
- Ambiguous but COULD be something valuable — a "wooden dresser" for $20 could be MCM teak

WHEN IN DOUBT, pass=false. Missing a $500 deal costs far more than a $0.04 API call.
ONLY output JSON."""

FULL_PROMPT = """You are Gramma, a warm but sharp AI vintage appraiser for the SF Bay Area.

Use web search for REAL price data from MULTIPLE sources:
a) eBay sold/completed — search "[brand] [model] sold" or "[description] vintage sold"
b) 1stDibs — search "1stdibs [brand] [model]" for dealer ceiling prices
c) Chairish — search "chairish [brand] [model]" for mid-market prices
d) For clothing: "poshmark [brand] [item] sold"
e) For high-end: "liveauctioneers [brand] [model]"

Respond ONLY with valid JSON:
{
  "identified": boolean, "confidence": "high"|"medium"|"low",
  "brand_or_designer": "string", "specific_model": "string or null",
  "item_type": "string", "era": "string", "materials": "string",
  "market_data": {
    "ebay_sold": [{"title":"str","price":num}],
    "firstdibs_active": [{"title":"str","price":num}],
    "chairish_active": [{"title":"str","price":num}],
    "poshmark_sold": [{"title":"str","price":num}],
    "auction_results": [{"title":"str","price":num,"house":"str"}],
    "data_quality_note": "str"
  },
  "estimated_resale_low": num, "estimated_resale_high": num, "resale_ceiling": num,
  "profit_score": 1-10,
  "verdict": "STRONG BUY"|"BUY"|"MAYBE"|"PASS",
  "verdict_reason": "cite specific comp prices as evidence",
  "what_to_check": "what to verify in person",
  "where_to_sell": ["platforms ranked by return"],
  "comp_search_terms": "exact search for more comps",
  "flip_time_estimate": "e.g. 1-3 days",
  "negotiation_tip": "specific to this deal",
  "ai_price_assessment": "underpriced"|"fair"|"overpriced"|"unknown"
}

RULES:
- Search 2-3+ sources. eBay sold=floor, 1stDibs=ceiling, Chairish=mid.
- STRONG BUY = comps confirm 3x+ asking. BUY = 2x+. FREE + real wood/brand = STRONG BUY.
- verdict_reason MUST cite specific dollar amounts from comps.
- Include empty arrays [] for sources with no comps found.
- SF Bay Area has strong demand for MCM, Danish, designer.
- ONLY output JSON."""


# ══════════════════════════════════════════════════════════════════
# IMAGE EXTRACTION
# ══════════════════════════════════════════════════════════════════

def extract_image(entry):
    """Extract image URL from Craigslist RSS entry."""
    for enc in entry.get("enclosures", []):
        url = enc.get("href") or enc.get("url")
        if url:
            return url
    for link in entry.get("links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")
    summary = entry.get("summary", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if m:
        return m.group(1)
    return None


def fetch_listing_image(url):
    """Fetch og:image from listing page."""
    if not url:
        return None
    try:
        r = requests.get(url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=6)
        if r.status_code == 200:
            m = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', r.text)
            if m:
                return m.group(1)
            m = re.search(r'"(https://images\.craigslist\.org/[^"]+)"', r.text)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════
# MONITOR ENGINE
# ══════════════════════════════════════════════════════════════════

class Monitor:
    def __init__(self):
        self.dd = Path(CONFIG["data_dir"]); self.dd.mkdir(exist_ok=True)
        self.sf = self.dd / "seen.json"; self.lf = self.dd / "scout_log.jsonl"
        self.seen = self._load()
        self.stats = {
            "cycles": 0, "prescreened": 0, "filtered": 0, "evaluated": 0,
            "strong": 0, "buys": 0, "maybes": 0, "passes": 0, "errors": 0,
        }
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(self.dd / "monitor.log")])
        self.log = logging.getLogger("VS")

    def _load(self):
        if self.sf.exists():
            try:
                d = json.loads(self.sf.read_text())
                cut = (datetime.now() - timedelta(days=7)).isoformat()
                return {k: v for k, v in d.items() if v.get("ts", "") > cut}
            except:
                return {}
        return {}

    def _save(self):
        self.sf.write_text(json.dumps(self.seen, indent=2))

    def _lid(self, e):
        return hashlib.md5((e.get("link", "") + e.get("title", "")).encode()).hexdigest()

    def build_url(self, s):
        p = {"format": "rss", "query": s["query"], "sort": "date"}
        if s.get("min_price"):
            p["min_price"] = s["min_price"]
        if s.get("max_price") is not None:
            p["max_price"] = s["max_price"]
        return f"https://{CONFIG['craigslist_region']}.craigslist.org/search/{s['category']}?{urlencode(p)}"

    def fetch(self, s):
        try:
            f = feedparser.parse(self.build_url(s))
            return f.entries if not (f.bozo and not f.entries) else []
        except:
            return []

    def price(self, e):
        m = re.search(r'\$(\d[\d,]*)', e.get("title", ""))
        return int(m.group(1).replace(",", "")) if m else 0

    def api_call(self, model, system, prompt, web_search=False, timeout=15):
        k = CONFIG["anthropic_api_key"]
        if k == "YOUR_API_KEY_HERE":
            return None
        body = {
            "model": model,
            "max_tokens": 2000 if web_search else 300,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        if web_search:
            body["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
        try:
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json", "x-api-key": k, "anthropic-version": "2023-06-01"},
                json=body, timeout=timeout)
            r.raise_for_status()
            txt = "".join(b["text"] for b in r.json()["content"] if b["type"] == "text")
            m = re.search(r'\{[\s\S]*\}', txt.replace("```json", "").replace("```", "").strip())
            return json.loads(m.group(0)) if m else None
        except Exception as e:
            self.log.error(f"API ({model.split('-')[1]}): {e}")
            return None

    def prescreen(self, title, price, category):
        prompt = f"Title: {title}\nPrice: ${price}{' (FREE)' if price == 0 else ''}\nCategory: {category}"
        return self.api_call("claude-haiku-4-5-20251001", PRESCREEN_PROMPT, prompt,
                             web_search=False, timeout=10)

    def full_evaluate(self, listing):
        prompt = (
            f"Evaluate this Craigslist listing:\n"
            f"Title: {listing['title']}\n"
            f"Price: ${listing['price']}{' (FREE)' if listing['price'] == 0 else ''}\n"
            f"Description: {re.sub(r'<[^>]+>', '', listing.get('summary', ''))[:500]}\n"
            f"Location: SF Bay Area"
        )
        return self.api_call("claude-sonnet-4-20250514", FULL_PROMPT, prompt,
                             web_search=True, timeout=45)

    def notify(self, listing, ev):
        topic = CONFIG["ntfy_topic"]
        if topic == "gramma-CHANGEME":
            return
        v = ev.get("verdict", "?")
        brand = ev.get("brand_or_designer", "?")
        rl, rh = ev.get("estimated_resale_low", 0), ev.get("estimated_resale_high", 0)
        p = listing["price"]
        ceil = ev.get("resale_ceiling", 0)
        md = ev.get("market_data", {})

        if p > 0:
            mid = (rl + rh) / 2
            prof = f"+${int(mid - p)} ({int((mid / p - 1) * 100)}%)"
        elif p == 0:
            prof = f"FREE → ${rl}-${rh}"
        else:
            prof = f"${rl}-${rh}"

        comps = []
        for c in (md.get("ebay_sold") or [])[:2]:
            comps.append(f"eBay: ${c.get('price', '?')}")
        for c in (md.get("firstdibs_active") or [])[:1]:
            comps.append(f"1stDibs: ${c.get('price', '?')}")
        for c in (md.get("chairish_active") or [])[:1]:
            comps.append(f"Chairish: ${c.get('price', '?')}")

        title_str = f"{'⚡' if v == 'STRONG BUY' else '✓'} {v}: {brand}"
        body = (
            f"{listing['title']}\n\n"
            f"💰 Ask: {'FREE' if p == 0 else f'${p}'}\n"
            f"📈 Resale: ${rl}-${rh}{f' (ceil ${ceil})' if ceil else ''}\n"
            f"🔥 {prof}\n"
            f"📊 Score: {ev.get('profit_score', '?')}/10\n\n"
            f"📊 COMPS:\n" + ("\n".join(comps) if comps else "Limited data") + "\n\n"
            f"👁 {ev.get('what_to_check', '')[:100]}\n"
            f"💬 {ev.get('negotiation_tip', '')[:80]}"
        )

        headers = {
            "Title": title_str,
            "Priority": "5" if v == "STRONG BUY" else "4",
            "Tags": "moneybag" if v == "STRONG BUY" else "chart_with_upwards_trend",
        }
        if listing.get("link"):
            headers["Click"] = listing["link"]
            headers["Actions"] = f"view, Open Listing, {listing['link']}"
        if listing.get("image_url"):
            headers["Attach"] = listing["image_url"]

        try:
            requests.post(f"https://ntfy.sh/{topic}", data=body.encode("utf-8"),
                          headers=headers, timeout=10)
            self.log.info(f"📱 Push: {title_str}" + (" 📷" if listing.get("image_url") else ""))
        except Exception as e:
            self.log.error(f"ntfy: {e}")

    def process(self, entry, search):
        lid = self._lid(entry)
        if lid in self.seen:
            return
        title = entry.get("title", "")
        price = self.price(entry)
        self.seen[lid] = {"ts": datetime.now().isoformat(), "title": title[:100], "price": price}

        if price > CONFIG["max_eval_price"]:
            return

        # ── Extract image (non-blocking, quick) ──
        image_url = extract_image(entry)

        # ── STAGE 1: Haiku pre-screen (~1-2s) ──
        self.stats["prescreened"] += 1
        ps = self.prescreen(title, price, search["category"])
        if ps and ps.get("pass") is True:
            self.stats["filtered"] += 1
            return

        # Only fetch the full page image if we're going to evaluate
        if not image_url:
            image_url = fetch_listing_image(entry.get("link"))

        self.log.info(f"🔍 Evaluating: {title[:65]} — {'FREE' if price == 0 else f'${price}'}")

        listing = {
            "title": title,
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "price": price,
            "cat": search["category"],
            "search": search["name"],
            "image_url": image_url,
        }

        # ── STAGE 2: Sonnet + multi-source web search (~10-20s) ──
        ev = self.full_evaluate(listing)
        if not ev:
            self.stats["errors"] += 1
            return

        v = ev.get("verdict", "PASS")
        md = ev.get("market_data", {})
        nc = sum(len(md.get(k, []) or []) for k in
                 ["ebay_sold", "firstdibs_active", "chairish_active", "poshmark_sold", "auction_results"])

        self.stats["evaluated"] += 1
        self.stats[{"STRONG BUY": "strong", "BUY": "buys", "MAYBE": "maybes"}.get(v, "passes")] += 1

        ic = {"STRONG BUY": "⚡", "BUY": "✓", "MAYBE": "?", "PASS": "✕"}.get(v, "·")
        self.log.info(
            f"  {ic} {v} | {ev.get('brand_or_designer', '?')} | "
            f"${ev.get('estimated_resale_low', 0)}-${ev.get('estimated_resale_high', 0)} | "
            f"{nc} comps | {ev.get('ai_price_assessment', '?')}"
        )

        with open(self.lf, "a") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "listing": listing,
                "eval": ev,
            }) + "\n")

        if v in CONFIG["notify_verdicts"]:
            self.notify(listing, ev)

    def cycle(self):
        """One full cycle: check all feeds for new listings."""
        new_total = 0
        for s in SEARCHES:
            entries = self.fetch(s)
            new_in_feed = 0
            for e in entries:
                if self._lid(e) not in self.seen:
                    new_in_feed += 1
                    self.process(e, s)
                    time.sleep(CONFIG["pause_between_evals"])
            if new_in_feed > 0:
                self.log.info(f"  📡 {s['name']}: {new_in_feed} new")
            new_total += new_in_feed
            time.sleep(CONFIG["pause_between_feeds"])
        self._save()
        self.stats["cycles"] += 1
        return new_total

    def print_banner(self):
        feed_count = len(SEARCHES)
        # Count total unique brand/keyword terms
        all_terms = set()
        for s in SEARCHES:
            for term in s["query"].split("|"):
                all_terms.add(term.strip())
        term_count = len(all_terms)

        cycle_time = feed_count * CONFIG["pause_between_feeds"]

        print("\n" + "=" * 62)
        print("  ◈  GRAMMA — Craigslist Monitor v4")
        print("     Optimized: broad feeds + fast polling")
        print("=" * 62)
        print(f"  Region:       {CONFIG['craigslist_region']}")
        print(f"  Feeds:        {feed_count} broad (covering {term_count} search terms)")
        print(f"  Cycle time:   ~{cycle_time:.0f}s per full scan")
        print(f"  Poll rate:    every {CONFIG['poll_interval_seconds']}s")
        print(f"  Detection:    ~{CONFIG['poll_interval_seconds'] + cycle_time:.0f}s from post to your phone")
        print(f"  Notify on:    {', '.join(CONFIG['notify_verdicts'])}")
        print(f"  ntfy topic:   {CONFIG['ntfy_topic']}")
        print(f"  Seen cache:   {len(self.seen)} entries")
        print(f"  Stage 1:      Haiku pre-screen (~1-2s, filters ~80%)")
        print(f"  Stage 2:      Sonnet + eBay/1stDibs/Chairish (~10-20s)")
        print("=" * 62)
        print("  Monitoring... (Ctrl+C to stop)\n")

    def run(self):
        self.print_banner()
        if CONFIG["anthropic_api_key"] == "YOUR_API_KEY_HERE":
            print("❌ Set your Anthropic API key!")
            print("   export ANTHROPIC_API_KEY='sk-ant-...'")
            sys.exit(1)
        if CONFIG["ntfy_topic"] == "gramma-CHANGEME":
            print("⚠️  ntfy topic not set — no push notifications.\n")

        try:
            while True:
                try:
                    self.cycle()
                except Exception as e:
                    self.log.error(f"Cycle error: {e}")

                # Periodic stats
                if self.stats["cycles"] % 30 == 0 and self.stats["cycles"] > 0:
                    s = self.stats
                    filt_pct = f"{s['filtered'] / max(s['prescreened'], 1) * 100:.0f}%" if s['prescreened'] else "n/a"
                    self.log.info(
                        f"💓 Cycle #{s['cycles']} | "
                        f"Prescreened: {s['prescreened']} ({filt_pct} filtered) | "
                        f"Full evals: {s['evaluated']} | "
                        f"⚡{s['strong']} ✓{s['buys']} ?{s['maybes']} ✕{s['passes']} ❌{s['errors']} | "
                        f"Seen: {len(self.seen)}"
                    )

                time.sleep(CONFIG["poll_interval_seconds"])

        except KeyboardInterrupt:
            s = self.stats
            filt_pct = f"{s['filtered'] / max(s['prescreened'], 1) * 100:.0f}%" if s['prescreened'] else "n/a"
            print(f"\n\n🛑 Stopped after {s['cycles']} cycles")
            print(f"   Prescreened: {s['prescreened']} ({filt_pct} filtered)")
            print(f"   Full evals:  {s['evaluated']}")
            print(f"   Results:     ⚡{s['strong']} strong | ✓{s['buys']} buy | ?{s['maybes']} maybe | ✕{s['passes']} pass")
            print(f"   Errors:      {s['errors']}")
            self._save()
            print(f"   Log:         {self.lf}")


# ══════════════════════════════════════════════════════════════════
# REVIEW UTILITY
# ══════════════════════════════════════════════════════════════════

def review(vf=None):
    lf = Path(CONFIG["data_dir"]) / "scout_log.jsonl"
    if not lf.exists():
        print("No log file yet. Run the monitor first.")
        return
    entries = []
    for line in lf.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if vf:
        entries = [e for e in entries if e.get("eval", {}).get("verdict") == vf.upper()]

    print(f"\n{'=' * 80}")
    print(f"  SCOUT LOG — {len(entries)} entries" + (f" (filtered: {vf})" if vf else ""))
    print(f"{'=' * 80}")

    for e in entries:
        ev = e.get("eval", {})
        li = e.get("listing", {})
        md = ev.get("market_data", {})
        v = ev.get("verdict", "?")
        ic = {"STRONG BUY": "⚡", "BUY": "✓", "MAYBE": "?", "PASS": "✕"}.get(v, "·")
        nc = sum(len(md.get(k, []) or []) for k in
                 ["ebay_sold", "firstdibs_active", "chairish_active", "poshmark_sold", "auction_results"])
        p = li.get("price", 0)

        print(f"\n  {ic} {v:12s} | {ev.get('brand_or_designer', '?'):25s} | "
              f"Ask: ${p:>5d} → ${ev.get('estimated_resale_low', 0)}-${ev.get('estimated_resale_high', 0)} | "
              f"{nc} comps | {ev.get('ai_price_assessment', '?')}")
        print(f"    {li.get('title', '?')[:75]}")
        for c in (md.get("ebay_sold") or [])[:2]:
            print(f"    eBay: {c.get('title', '')[:50]} → ${c.get('price', '?')}")
        for c in (md.get("firstdibs_active") or [])[:1]:
            print(f"    1stDibs: {c.get('title', '')[:50]} → ${c.get('price', '?')}")
        for c in (md.get("chairish_active") or [])[:1]:
            print(f"    Chairish: {c.get('title', '')[:50]} → ${c.get('price', '?')}")
        print(f"    {ev.get('verdict_reason', '')[:80]}")
        if li.get("image_url"):
            print(f"    📷 {li['image_url'][:80]}")
        if li.get("link"):
            print(f"    {li['link']}")


# ══════════════════════════════════════════════════════════════════
# TEST FEEDS
# ══════════════════════════════════════════════════════════════════

def test():
    print(f"\n{'=' * 62}")
    print("  TESTING RSS FEEDS — Optimized v4")
    print(f"{'=' * 62}\n")

    m = Monitor()
    total_listings = 0

    for s in SEARCHES:
        url = m.build_url(s)
        entries = m.fetch(s)
        total_listings += len(entries)
        terms = len(s["query"].split("|"))
        status = f"✅ {len(entries):>3d} listings" if entries else "❌   0 results"

        print(f"  {s['name']:30s} {status} ({terms} terms)")
        if entries:
            first = entries[0]
            img = extract_image(first)
            print(f"    └─ Latest: {first.get('title', '?')[:55]}" + (" 📷" if img else ""))
        # Show URL for debugging
        print(f"    └─ URL: {url[:80]}...")
        print()

    print(f"  Total: {total_listings} listings across {len(SEARCHES)} feeds")
    cycle_time = len(SEARCHES) * CONFIG["pause_between_feeds"]
    print(f"  Estimated cycle time: ~{cycle_time:.0f}s")
    print(f"  Estimated detection latency: ~{CONFIG['poll_interval_seconds'] + cycle_time:.0f}s\n")


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "review":
            review(sys.argv[2] if len(sys.argv) > 2 else None)
        elif cmd == "test":
            test()
        elif cmd == "help":
            print(__doc__)
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python3 craigslist.py [test|review|help]")
    else:
        Monitor().run()
