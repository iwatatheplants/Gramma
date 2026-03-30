import { useState, useRef, useCallback, useEffect } from "react";

// ═══ GRAMMA CHARACTER SVG ═══
const GrammaWalk=({size=80})=>(
<svg width={size} height={size} viewBox="0 0 100 100" style={{display:"block"}}>
<g className="gramma-body">
{/* Body/Cardigan */}
<ellipse cx="50" cy="72" rx="22" ry="24" fill="#8B3A3A"/>
{/* Cardigan buttons */}
<circle cx="50" cy="65" r="1.5" fill="#C8A24E"/><circle cx="50" cy="72" r="1.5" fill="#C8A24E"/><circle cx="50" cy="79" r="1.5" fill="#C8A24E"/>
{/* Head */}
<ellipse cx="50" cy="38" rx="16" ry="18" fill="#F0D5B8"/>
{/* Hair */}
<ellipse cx="50" cy="28" rx="18" ry="14" fill="#E8E2D8"/>
<ellipse cx="54" cy="22" rx="7" ry="6" fill="#D8D2C8"/>
{/* Cheeks */}
<ellipse cx="42" cy="42" rx="4" ry="3" fill="#E8A0A0" opacity="0.5"/>
<ellipse cx="58" cy="42" rx="4" ry="3" fill="#E8A0A0" opacity="0.5"/>
{/* Eyes */}
<ellipse cx="44" cy="37" rx="2.5" ry="3" fill="#3D2B1F"/>
<ellipse cx="56" cy="37" rx="2.5" ry="3" fill="#3D2B1F"/>
<circle cx="45" cy="36" r="1" fill="#fff"/><circle cx="57" cy="36" r="1" fill="#fff"/>
{/* Smile */}
<path d="M45 46 Q50 50 55 46" fill="none" stroke="#8B5E3C" strokeWidth="1.2" strokeLinecap="round"/>
{/* Glasses */}
<path d="M38 36 Q38 32 44 32 L48 32 Q50 32 50 36 Q50 40 46 40 Q38 40 38 36Z" fill="none" stroke="#C8A24E" strokeWidth="1"/>
<path d="M50 36 Q50 32 54 32 L60 32 Q62 32 62 36 Q62 40 58 40 Q50 40 50 36Z" fill="none" stroke="#C8A24E" strokeWidth="1"/>
<path d="M38 34 L34 33" fill="none" stroke="#C8A24E" strokeWidth="1" strokeLinecap="round"/>
<path d="M62 34 L66 33" fill="none" stroke="#C8A24E" strokeWidth="1" strokeLinecap="round"/>
{/* Pearls */}
<circle cx="44" cy="53" r="1.5" fill="#F5ECD7"/><circle cx="48" cy="52.5" r="1.5" fill="#F5ECD7"/><circle cx="52" cy="52.5" r="1.5" fill="#F5ECD7"/><circle cx="56" cy="53" r="1.5" fill="#F5ECD7"/>
{/* Magnifying glass */}
<circle cx="28" cy="48" r="7" fill="none" stroke="#C8A24E" strokeWidth="1.5"/>
<line x1="33" y1="53" x2="37" y2="58" stroke="#C8A24E" strokeWidth="2" strokeLinecap="round"/>
{/* Arms */}
<path d="M30 68 Q26 58 30 50" fill="none" stroke="#8B3A3A" strokeWidth="6" strokeLinecap="round"/>
<path d="M70 68 Q74 60 70 54" fill="none" stroke="#8B3A3A" strokeWidth="6" strokeLinecap="round"/>
{/* Legs */}
<line x1="42" y1="92" x2="42" y2="100" stroke="#3D2B1F" strokeWidth="3" strokeLinecap="round" className="gramma-left-leg"/>
<line x1="58" y1="92" x2="58" y2="100" stroke="#3D2B1F" strokeWidth="3" strokeLinecap="round" className="gramma-right-leg"/>
</g>
</svg>);

// ═══ GRAMMA'S VOICE ═══
const GRAMMA_LOADING={
  quick:["Gramma's taking a quick look...","Let me adjust my glasses, dear..."],
  full:["Gramma's checking her records...","Flipping through the archives...","Calling my dealer friends...","Checking what these sold for...","Almost done, sweetheart..."],
};
const GRAMMA_VERDICTS={
  "STRONG BUY":"Oh honey, GRAB this immediately!","BUY":"Solid find — Gramma approves.","MAYBE":"Hmm, I've seen better deals, dear.","PASS":"Put it down, sweetheart. Not worth your gas money."
};
const GRAMMA_LISTING_LOADING=["Gramma's writing your listing...","Making it sound fancy...","Almost ready to post, dear..."];

// ═══ BRANDS DB ═══
const BRANDS={furniture:{tier1:{label:"Tier 1 — Museum Grade",color:"#C8A24E",brands:[{n:"Herman Miller",r:[200,15000],h:"Eames, Shell, Aeron"},{n:"Knoll",r:[300,12000],h:"Barcelona, Womb, Tulip"},{n:"Fritz Hansen",r:[400,8000],h:"Egg, Swan, Series 7"},{n:"Hans Wegner",r:[300,10000],h:"Wishbone, Papa Bear"},{n:"Eero Saarinen",r:[300,6000],h:"Tulip Table, Womb"},{n:"Isamu Noguchi",r:[500,8000],h:"Coffee Table, Akari"},{n:"George Nelson",r:[200,6000],h:"Bench, Ball Clock"},{n:"Vladimir Kagan",r:[1000,20000],h:"Serpentine Sofa"}]},tier2:{label:"Tier 2 — Collectible",color:"#a78bfa",brands:[{n:"Heywood-Wakefield",r:[150,2500],h:"Champagne birch"},{n:"Broyhill Brasilia",r:[200,2000],h:"Credenzas"},{n:"Lane Acclaim",r:[100,800],h:"Dovetail tables"},{n:"Paul McCobb",r:[200,3000],h:"Planner Group"},{n:"Milo Baughman",r:[300,4000],h:"Chrome flat-bar"},{n:"Adrian Pearsall",r:[400,5000],h:"Sculptural sofas"},{n:"Drexel",r:[100,1800],h:"Declaration, Profile"},{n:"Kent Coffey",r:[150,1200],h:"Perspecta"}]},tier3:{label:"Tier 3 — Quick Flips",color:"#60a5fa",brands:[{n:"Baker Furniture",r:[100,1000],h:"Far East"},{n:"Henredon",r:[80,800],h:"Scene One MCM"},{n:"Danish Modern",r:[100,1500],h:"Teak stamps"}]}},clothing:{tier1:{label:"Tier 1 — Luxury",color:"#C8A24E",brands:[{n:"Chanel",r:[100,5000],h:"Jackets, bags"},{n:"Hermès",r:[100,10000],h:"Scarves, bags"},{n:"Gucci",r:[50,3000],h:"Logo, horsebit"},{n:"Prada",r:[50,2000],h:"Nylon bags"},{n:"Burberry",r:[50,1500],h:"Trench coats"}]},tier2:{label:"Tier 2 — Strong Resale",color:"#a78bfa",brands:[{n:"Thierry Mugler",r:[80,1500],h:"Sculptural blazers"},{n:"Jean Paul Gaultier",r:[60,800],h:"Mesh tops"},{n:"Comme des Garçons",r:[50,1200],h:"Avant-garde"},{n:"Issey Miyake",r:[40,800],h:"Pleats Please"},{n:"Maison Margiela",r:[60,1500],h:"Tabi boots"}]},tier3:{label:"Tier 3 — Quick Flips",color:"#60a5fa",brands:[{n:"Vintage Levi's",r:[30,300],h:"501s, Big E"},{n:"Carhartt",r:[20,150],h:"Duck canvas"},{n:"Patagonia",r:[20,200],h:"Retro fleece"},{n:"Vintage Nike",r:[15,250],h:"Old swoosh"}]}}};

// ═══ PROMPTS ═══
const QUICK_SYS=`You are Gramma — a warm, sharp, no-nonsense vintage AI appraiser. You're a retired antique dealer with 45 years of experience. You speak like a loving grandmother who knows EVERYTHING about vintage. Quick ID mode. Return ONLY JSON:
{"brand_or_designer":"str","specific_model":"str or null","item_type":"str","era":"str","materials":"str","estimated_resale_low":num,"estimated_resale_high":num,"confidence":"high|medium|low","quick_notes":"1-2 sentences IN GRAMMA'S VOICE — warm, direct, knowledgeable","authenticity_clues":"brief","where_marks":"where to look for marks"}
ONLY JSON.`;

const FULL_SYS=`You are Gramma — a warm, sharp vintage AI appraiser with 45 years of experience. Use web search for REAL prices: eBay sold, 1stDibs, Chairish, Poshmark, auctions. Return ONLY JSON:
{"identified":bool,"confidence":"high|medium|low","brand_or_designer":"str","specific_model":"str or null","item_type":"str","era":"str","materials":"str","authenticity_notes":"str","condition_notes":"str","makers_mark_analysis":"str","market_data":{"ebay_sold":[{"title":"str","price":num}],"firstdibs_active":[{"title":"str","price":num}],"chairish_active":[{"title":"str","price":num}],"poshmark_sold":[{"title":"str","price":num}],"auction_results":[{"title":"str","price":num,"house":"str"}],"data_quality_note":"str"},"estimated_resale_low":num,"estimated_resale_high":num,"resale_ceiling":num,"profit_score":1-10,"verdict":"STRONG BUY"|"BUY"|"MAYBE"|"PASS","verdict_reason":"IN GRAMMA'S VOICE — cite specific comp prices as evidence","what_to_check":"str","where_to_sell":["str"],"comp_search_terms":"str","flip_time_estimate":"str","negotiation_tip":"IN GRAMMA'S VOICE","ai_price_assessment":"underpriced|fair|overpriced|unknown","historical_context":"2-3 sentences"}
Search 2-3+ sources. Cite prices. Use ALL photos. ONLY JSON.`;

const LIST_SYS=`You are Gramma writing a resale listing. Professional but warm. Return ONLY JSON:
{"title":"max 80 chars, keyword-rich","description":"full listing — professional, detailed, include dimensions if provided","tags":["8-12 tags"],"suggested_price_quick_sale":num,"suggested_price_max_value":num,"best_platform":"which platform and why (1 sentence)"}
ONLY JSON.`;

const PHOTO_SLOTS=[
  {id:"main",label:"Item Photo",hint:"Full view",icon:"📸",required:true},
  {id:"mark",label:"Maker's Mark",hint:"Labels underneath",icon:"🏷"},
  {id:"detail",label:"Construction",hint:"Joints, hardware",icon:"🔍"},
  {id:"extra",label:"Label / Other",hint:"Tags, damage",icon:"📋"},
];

const VD={"STRONG BUY":{bg:"linear-gradient(135deg,#14532d,#052e16)",bdr:"#22c55e",txt:"#4ade80",ic:"⚡"},"BUY":{bg:"linear-gradient(135deg,#1a2e05,#0f1d03)",bdr:"#84cc16",txt:"#a3e635",ic:"✓"},"MAYBE":{bg:"linear-gradient(135deg,#422006,#2a1503)",bdr:"#f59e0b",txt:"#fbbf24",ic:"?"},"PASS":{bg:"linear-gradient(135deg,#450a0a,#2d0505)",bdr:"#ef4444",txt:"#f87171",ic:"✕"}};
const PB={underpriced:{bg:"#052e16",bdr:"#22c55e",txt:"#4ade80",l:"UNDERPRICED"},fair:{bg:"#1a1a2e",bdr:"#6366f1",txt:"#818cf8",l:"FAIR"},overpriced:{bg:"#2d0505",bdr:"#ef4444",txt:"#f87171",l:"OVERPRICED"},unknown:{bg:"#1a1a2e",bdr:"#4a4660",txt:"#6b6880",l:"UNKNOWN"}};
const ebUrl=q=>`https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(q)}&LH_Complete=1&LH_Sold=1`;

export default function App(){
  const [tab,setTab]=useState("scan");
  const [photos,setPhotos]=useState({main:null,mark:null,detail:null,extra:null});
  const [previews,setPreviews]=useState({main:null,mark:null,detail:null,extra:null});
  const [ask,setAsk]=useState("");const [desc,setDesc]=useState("");
  const [plat,setPlat]=useState("Estate Sale");
  const [mode,setMode]=useState("full");
  const [res,setRes]=useState(null);const [loading,setLoading]=useState(false);
  const [err,setErr]=useState(null);const [loadMsg,setLoadMsg]=useState("");
  const [hist,setHist]=useState([]);const [bf,setBf]=useState("all");const [bc,setBc]=useState("furniture");const [exH,setExH]=useState(null);
  const [purchased,setPurchased]=useState(false);const [buyPrice,setBuyPrice]=useState("");
  const [dims,setDims]=useState({w:"",d:"",h:""});
  const [listing,setListing]=useState(null);const [listingLoading,setListingLoading]=useState(false);
  const [copied,setCopied]=useState(null);
  const [danceMode,setDanceMode]=useState("walk"); // walk, twerk
  const [batchFiles,setBatchFiles]=useState([]);
  const [batchRunning,setBatchRunning]=useState(false);
  const fileRefs=useRef({});const rRef=useRef(null);const listRef=useRef(null);const batchInputRef=useRef(null);

  useEffect(()=>{(async()=>{try{const r=await window.storage.get("gramma-h");if(r?.value)setHist(JSON.parse(r.value))}catch{}})()},[]);
  const sH=async h=>{setHist(h);try{await window.storage.set("gramma-h",JSON.stringify(h.slice(0,100)))}catch{}};

  // Cycle dance mode every few seconds while loading
  useEffect(()=>{if(!loading)return;const iv=setInterval(()=>setDanceMode(d=>d==="walk"?"twerk":"walk"),3000);return()=>clearInterval(iv)},[loading]);

  const compressImage=useCallback((dataUrl,maxPx=1200,quality=0.82)=>new Promise(resolve=>{
    const img=new Image();img.onload=()=>{
      let {width:w,height:h}=img;
      if(w>maxPx||h>maxPx){if(w>h){h=Math.round(h*maxPx/w);w=maxPx;}else{w=Math.round(w*maxPx/h);h=maxPx;}}
      const c=document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(img,0,0,w,h);resolve(c.toDataURL('image/jpeg',quality));
    };img.src=dataUrl;
  }),[]);

  const hFile=useCallback((slotId,f)=>{
    if(!f||!f.type.startsWith("image/"))return;
    const r=new FileReader();r.onload=async e=>{
      const compressed=await compressImage(e.target.result);
      setPhotos(p=>({...p,[slotId]:compressed}));
      setPreviews(p=>({...p,[slotId]:e.target.result}));
      setRes(null);setErr(null);setPurchased(false);setListing(null);
    };r.readAsDataURL(f);
  },[compressImage]);
  const removePhoto=id=>{setPhotos(p=>({...p,[id]:null}));setPreviews(p=>({...p,[id]:null}));setRes(null)};

  const handleBatchSelect=useCallback(async files=>{
    const items=await Promise.all(
      Array.from(files).filter(f=>f.type.startsWith("image/")).slice(0,20).map(f=>new Promise(res=>{
        const r=new FileReader();r.onload=async e=>{
          const compressed=await compressImage(e.target.result);
          res({id:Date.now()+Math.random(),preview:e.target.result,compressed,status:"idle",result:null,error:null});
        };r.readAsDataURL(f);
      }))
    );
    setBatchFiles(prev=>[...prev,...items].slice(0,20));
  },[compressImage]);

  const runBatchScan=useCallback(async()=>{
    const idle=batchFiles.filter(f=>f.status==="idle");
    if(!idle.length)return;
    setBatchRunning(true);
    setBatchFiles(prev=>prev.map(f=>f.status==="idle"?{...f,status:"loading"}:f));
    await Promise.allSettled(idle.map(async item=>{
      try{
        const b64=item.compressed.split(",")[1];
        const mt=item.compressed.match(/data:(image\/\w+);/)?.[1]||"image/jpeg";
        const images=[{type:"text",text:"[Item photo]:"},{type:"image",source:{type:"base64",media_type:mt,data:b64}}];
        const result=await apiCall("claude-haiku-4-5-20251001",QUICK_SYS,"Quick-identify this vintage item for resale value.",false,images);
        setBatchFiles(prev=>prev.map(f=>f.id===item.id?{...f,status:"done",result}:f));
      }catch(e){
        setBatchFiles(prev=>prev.map(f=>f.id===item.id?{...f,status:"error",error:e.message}:f));
      }
    }));
    setBatchRunning(false);
  },[batchFiles,apiCall]);
  const hasAnyPhoto=Object.values(photos).some(Boolean);
  const photoCount=Object.values(photos).filter(Boolean).length;

  const apiCall=async(model,system,prompt,webSearch=false,images=[])=>{
    const uc=[...images,{type:"text",text:prompt}];
    const body={model,max_tokens:webSearch?2000:800,system,messages:[{role:"user",content:uc}]};
    if(webSearch)body.tools=[{type:"web_search_20250305",name:"web_search"}];
    const r=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const d=await r.json();if(d.error)throw new Error(d.error.message);
    const t=d.content.filter(b=>b.type==="text").map(b=>b.text).join("");
    const jm=t.replace(/```json|```/g,"").trim().match(/\{[\s\S]*\}/);
    if(!jm)throw new Error("Gramma couldn't read that, dear. Try again?");
    return JSON.parse(jm[0]);
  };

  const buildImageContent=()=>{
    const uc=[];const labels={main:"Main item photo",mark:"Maker's mark / label",detail:"Construction detail",extra:"Additional detail"};
    for(const [id,data] of Object.entries(photos)){
      if(data){const b=data.split(",")[1];const m=data.match(/data:(image\/\w+);/);
        uc.push({type:"text",text:`[${labels[id]}]:`});
        uc.push({type:"image",source:{type:"base64",media_type:m?.[1]||"image/jpeg",data:b}});
      }}return uc;
  };

  const analyze=async()=>{
    if(!hasAnyPhoto&&!desc){setErr("Show Gramma a photo or describe what you've got, dear.");return;}
    setLoading(true);setErr(null);setRes(null);setPurchased(false);setListing(null);
    const isQ=mode==="quick";
    const msgs=isQ?GRAMMA_LOADING.quick:GRAMMA_LOADING.full;
    let mi=0;setLoadMsg(msgs[0]);
    const iv=setInterval(()=>{mi=(mi+1)%msgs.length;setLoadMsg(msgs[mi])},isQ?1200:2500);
    const images=buildImageContent();
    let p=isQ?"Quick-identify this item.":"Full appraisal — analyze all photos.";
    if(desc)p+=`\n\nDescription: "${desc}"`;if(ask)p+=`\nAsking: $${ask}`;
    if(!isQ)p+=`\nPlatform: ${plat}\nLocation: SF Bay Area`;
    if(photoCount>1)p+=`\n\n${photoCount} photos provided — analyze all, especially marks/labels.`;
    try{
      const parsed=await apiCall(isQ?"claude-haiku-4-5-20251001":"claude-sonnet-4-20250514",isQ?QUICK_SYS:FULL_SYS,p,!isQ,images);
      parsed._mode=mode;setRes(parsed);
      await sH([{id:Date.now(),ts:new Date().toISOString(),ask:ask?+ask:null,plat,desc:desc?.substring(0,120),mode,photoCount,r:parsed},...hist]);
      setTimeout(()=>rRef.current?.scrollIntoView({behavior:"smooth",block:"start"}),120);
    }catch(e){setErr(e.message)}finally{clearInterval(iv);setLoading(false);setLoadMsg("")}
  };

  const generateListing=async()=>{
    setListingLoading(true);setListing(null);
    const dimStr=(dims.w||dims.d||dims.h)?`Dimensions: ${dims.w?dims.w+'"W ':""} ${dims.d?'× '+dims.d+'"D ':""} ${dims.h?'× '+dims.h+'"H':""}`.trim():"";
    const md=res?.market_data||{};
    const compSummary=[...(md.ebay_sold||[]).slice(0,2).map(c=>`eBay: ${c.title} $${c.price}`),...(md.firstdibs_active||[]).slice(0,1).map(c=>`1stDibs: ${c.title} $${c.price}`)].join("\n")||"No comps";
    const prompt=`Brand: ${res?.brand_or_designer||"Unknown"}\nModel: ${res?.specific_model||"Unknown"}\nType: ${res?.item_type}\nEra: ${res?.era}\nMaterials: ${res?.materials}\n${dimStr}\nCondition: ${res?.condition_notes||"Not assessed"}\nAuth: ${res?.authenticity_notes||""}\nMark: ${res?.makers_mark_analysis||""}\nHistory: ${res?.historical_context||""}\nBuy price: $${buyPrice||ask||"?"}\nResale: $${res?.estimated_resale_low||0}-$${res?.estimated_resale_high||0}\nComps:\n${compSummary}\nChannels: ${(res?.where_to_sell||[]).join(", ")}`;
    try{const result=await apiCall("claude-sonnet-4-20250514",LIST_SYS,prompt,false,[]);setListing(result);
      setTimeout(()=>listRef.current?.scrollIntoView({behavior:"smooth",block:"start"}),120);
    }catch(e){setErr(e.message)}finally{setListingLoading(false)}
  };

  const exportPDF=()=>{
    const md=res?.market_data||{};
    const comps=[...(md.ebay_sold||[]).map(c=>`<tr><td>eBay Sold</td><td>${c.title}</td><td>$${c.price?.toLocaleString()}</td></tr>`),...(md.firstdibs_active||[]).map(c=>`<tr><td>1stDibs</td><td>${c.title}</td><td>$${c.price?.toLocaleString()}</td></tr>`),...(md.chairish_active||[]).map(c=>`<tr><td>Chairish</td><td>${c.title}</td><td>$${c.price?.toLocaleString()}</td></tr>`),...(md.poshmark_sold||[]).map(c=>`<tr><td>Poshmark</td><td>${c.title}</td><td>$${c.price?.toLocaleString()}</td></tr>`)].join("")||"<tr><td colspan='3'>No comps found</td></tr>";
    const dimLine=(dims.w||dims.d||dims.h)?`<p><strong>Dimensions:</strong> ${dims.w?dims.w+'"W ':""} ${dims.d?'× '+dims.d+'"D ':""} ${dims.h?'× '+dims.h+'"H':""}</p>`:"";
    const html=`<!DOCTYPE html><html><head><meta charset="utf-8"><title>Gramma Appraisal — ${res?.brand_or_designer||"Item"}</title><style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:Georgia,serif;color:#1a1a1a;max-width:720px;margin:0 auto;padding:40px 32px;line-height:1.6}h1{font-size:28px;font-weight:normal;font-style:italic;color:#8B3A3A;margin-bottom:4px}h2{font-size:14px;font-weight:bold;text-transform:uppercase;letter-spacing:0.1em;color:#8B3A3A;margin:28px 0 12px;padding-bottom:6px;border-bottom:1px solid #ddd}p{font-size:14px;margin-bottom:8px}.meta{font-size:12px;color:#888;margin-bottom:24px;font-family:monospace}.verdict{display:inline-block;font-size:18px;font-weight:bold;padding:6px 16px;border-radius:6px;margin:8px 0 16px;${res?.verdict==="STRONG BUY"?"background:#e6f9e6;color:#166616":res?.verdict==="BUY"?"background:#eef6e6;color:#3a6614":res?.verdict==="MAYBE"?"background:#fef6e6;color:#7a5a0a":"background:#fde8e8;color:#7a1414"}}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;margin:8px 0}.grid-item label{font-size:11px;color:#888;text-transform:uppercase}.grid-item p{font-size:14px;font-weight:500;margin:2px 0}.resale{font-size:28px;font-weight:bold;margin:4px 0}table{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px}th{text-align:left;padding:8px 10px;background:#f5f5f0;border:1px solid #e0e0d8;font-size:11px;text-transform:uppercase;color:#666}td{padding:8px 10px;border:1px solid #e0e0d8}td:last-child{text-align:right;font-weight:600}.footer{margin-top:32px;padding-top:16px;border-top:1px solid #ddd;font-size:11px;color:#aaa;text-align:center}@media print{body{padding:20px}}</style></head><body><h1>Gramma Appraisal</h1><p class="meta">${new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})} · ${res?.confidence?.toUpperCase()||""} confidence</p><div class="verdict">${res?.verdict||"—"}</div><p style="font-size:15px;color:#444;margin-bottom:20px;font-style:italic">${res?.verdict_reason||res?.quick_notes||""}</p><h2>Identification</h2><div class="grid">${[["Brand",res?.brand_or_designer],["Model",res?.specific_model],["Type",res?.item_type],["Era",res?.era],["Materials",res?.materials]].filter(([,v])=>v).map(([l,v])=>`<div class="grid-item"><label>${l}</label><p>${v}</p></div>`).join("")}</div>${dimLine}<h2>Market Valuation</h2><p class="resale">$${res?.estimated_resale_low?.toLocaleString()||0} – $${res?.estimated_resale_high?.toLocaleString()||0}</p>${res?.resale_ceiling?`<p>Ceiling: $${res.resale_ceiling.toLocaleString()}</p>`:""}<h2>Comparable Sales</h2><table><thead><tr><th>Source</th><th>Item</th><th>Price</th></tr></thead><tbody>${comps}</tbody></table>${res?.authenticity_notes?`<h2>Authenticity</h2><p>${res.authenticity_notes}</p>`:""} ${res?.what_to_check?`<h2>What to Check</h2><p>${res.what_to_check}</p>`:""} ${res?.historical_context?`<h2>History</h2><p>${res.historical_context}</p>`:""} ${listing?`<h2>Listing</h2><p><strong>${listing.title}</strong></p><p>${listing.description}</p>`:""}<div class="footer">Generated by Gramma · "Ask Gramma!" · Not a formal appraisal</div></body></html>`;
    const w=window.open("","_blank");w.document.write(html);w.document.close();setTimeout(()=>w.print(),500);
  };

  const copyText=(text,label)=>{navigator.clipboard?.writeText(text);setCopied(label);setTimeout(()=>setCopied(null),2000)};
  const reset=()=>{setPhotos({main:null,mark:null,detail:null,extra:null});setPreviews({main:null,mark:null,detail:null,extra:null});setAsk("");setDesc("");setRes(null);setErr(null);setPurchased(false);setListing(null);setBuyPrice("");setDims({w:"",d:"",h:""})};
  const v=res?VD[res.verdict]||VD["MAYBE"]:null;
  const pb=res?PB[res.ai_price_assessment]||PB.unknown:null;
  const md=res?.market_data||{};
  const st={tot:hist.length,buys:hist.filter(h=>h.r?.verdict==="STRONG BUY"||h.r?.verdict==="BUY").length};

  // Colors
  const G="#C8A24E",BU="#8B3A3A",BG="#07060a",BG2="#12111a",BD="#1e1c2a",TX="#d4d0c8",DM="#4a4660",MDC="#6b6880",HI="#ece8de";
  const cd={background:BG2,border:`1px solid ${BD}`,borderRadius:14,padding:"18px 22px"};
  const lb={fontSize:10,color:MDC,textTransform:"uppercase",letterSpacing:"0.1em",marginBottom:6,display:"block",fontFamily:"'DM Mono',monospace"};
  const ip={width:"100%",background:"#0e0d14",border:`1px solid ${BD}`,borderRadius:10,padding:"11px 14px",color:TX,fontSize:14,fontFamily:"inherit",boxSizing:"border-box",outline:"none"};

  const Comp=({title,items,color,searchUrl})=>{
    if(!items?.length)return null;
    return <div style={{marginBottom:10}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:6}}>
        <span style={{fontSize:11,fontWeight:600,color,fontFamily:"'DM Mono',monospace"}}>{title}</span>
        {searchUrl&&<span style={{fontSize:10,color:G,cursor:"pointer",fontFamily:"'DM Mono',monospace"}} onClick={()=>window.open(searchUrl,"_blank")}>search →</span>}
      </div>
      {items.map((c,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"7px 12px",background:i%2===0?"rgba(255,255,255,0.015)":"transparent",borderRadius:6,marginBottom:2}}>
        <span style={{flex:1,fontSize:12,color:"#c4c0b8",marginRight:12}}>{c.title}</span>
        <span style={{fontFamily:"'DM Mono',monospace",fontSize:14,fontWeight:600,color,flexShrink:0}}>${typeof c.price==="number"?c.price.toLocaleString():c.price}</span>
      </div>)}
    </div>;
  };

  const CopyBtn=({text,label})=>(
    <button onClick={()=>copyText(text,label)} style={{background:copied===label?"#22c55e22":"#1e1c2a",border:`1px solid ${copied===label?"#22c55e44":BD}`,borderRadius:8,padding:"6px 14px",color:copied===label?"#4ade80":"#8a8698",fontSize:12,cursor:"pointer",fontFamily:"inherit",whiteSpace:"nowrap"}}>
      {copied===label?"Copied!":"Copy"}
    </button>
  );

  return(
    <div style={{minHeight:"100vh",background:BG,color:TX,fontFamily:"'DM Sans','Helvetica Neue',sans-serif"}}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700&family=DM+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet"/>
      <style>{`
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes grammaWalk{
  0%{transform:translateX(-100px) scaleX(1)}
  49%{transform:translateX(calc(100vw - 20px)) scaleX(1)}
  50%{transform:translateX(calc(100vw - 20px)) scaleX(-1)}
  99%{transform:translateX(-100px) scaleX(-1)}
  100%{transform:translateX(-100px) scaleX(1)}
}
@keyframes grammaStep{
  0%,100%{transform:rotate(-8deg)}
  50%{transform:rotate(8deg)}
}
@keyframes grammaStepAlt{
  0%,100%{transform:rotate(8deg)}
  50%{transform:rotate(-8deg)}
}
@keyframes grammaTwerk{
  0%,100%{transform:rotate(-3deg) translateY(0)}
  25%{transform:rotate(4deg) translateY(-3px)}
  50%{transform:rotate(-4deg) translateY(0)}
  75%{transform:rotate(5deg) translateY(-4px)}
}
@keyframes grammaBounce{
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-8px)}
}
.gramma-walking{animation:grammaWalk 6s linear infinite}
.gramma-walking .gramma-left-leg{transform-origin:42px 92px;animation:grammaStep 0.3s ease-in-out infinite}
.gramma-walking .gramma-right-leg{transform-origin:58px 92px;animation:grammaStepAlt 0.3s ease-in-out infinite}
.gramma-twerking{animation:grammaBounce 0.4s ease-in-out infinite}
.gramma-twerking .gramma-body{animation:grammaTwerk 0.25s ease-in-out infinite}
input:focus,textarea:focus,select:focus{border-color:${G}!important}
::placeholder{color:#3d3a4a}*{box-sizing:border-box}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-thumb{background:${BD};border-radius:3px}
`}</style>

      {/* HEADER */}
      <div style={{borderBottom:`1px solid ${BD}`,padding:"14px 20px",display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{width:40,height:40,borderRadius:12,background:BU,display:"flex",alignItems:"center",justifyContent:"center",overflow:"hidden"}}><GrammaWalk size={36}/></div>
          <div><div style={{fontFamily:"'Instrument Serif',Georgia,serif",fontSize:22,color:HI,fontStyle:"italic"}}>Gramma</div>
          <div style={{fontSize:9,color:DM,letterSpacing:"0.12em",textTransform:"uppercase",fontFamily:"'DM Mono',monospace"}}>Ask Gramma! — Vintage AI Appraiser</div></div>
        </div>
        {st.tot>0&&<div style={{fontSize:11,fontFamily:"'DM Mono',monospace",color:MDC}}>{st.tot} scans · <span style={{color:"#4ade80"}}>{st.buys} buys</span></div>}
      </div>

      {/* TABS */}
      <div style={{display:"flex",borderBottom:`1px solid ${BD}`,padding:"0 12px",overflowX:"auto"}}>
        {[["scan","Ask Gramma"],["batch","Batch Scan"],["history","History"],["brands","Brand DB"]].map(([k,l])=>(
          <button key={k} onClick={()=>setTab(k)} style={{background:"none",border:"none",borderBottom:tab===k?`2px solid ${G}`:"2px solid transparent",color:tab===k?HI:DM,padding:"12px 14px",fontSize:12,fontWeight:600,cursor:"pointer",fontFamily:"inherit",whiteSpace:"nowrap"}}>{l}{k==="history"&&hist.length?` (${hist.length})`:""}{k==="batch"&&batchFiles.length?` (${batchFiles.length})`:""}</button>
        ))}
      </div>

      <div style={{maxWidth:720,margin:"0 auto",padding:"20px 16px 80px"}}>

      {/* ══════ SCAN TAB ══════ */}
      {tab==="scan"&&<div style={{animation:"fadeUp 0.3s ease"}}>
        {/* Mode toggle */}
        <div style={{display:"flex",gap:8,marginBottom:16}}>
          {[["quick","⚡ Quick Look","~2 sec · Gramma's first impression"],["full","🔍 Full Appraisal","~15 sec · Gramma checks all her sources"]].map(([m,label,sub])=>(
            <button key={m} onClick={()=>{setMode(m);setRes(null);setPurchased(false);setListing(null)}} style={{flex:1,background:mode===m?"#1e1c2a":"transparent",border:`1px solid ${mode===m?G+"55":BD}`,borderRadius:12,padding:"14px 16px",cursor:"pointer",textAlign:"left"}}>
              <div style={{fontSize:14,fontWeight:600,color:mode===m?HI:MDC}}>{label}</div>
              <div style={{fontSize:11,color:mode===m?MDC:DM,marginTop:3}}>{sub}</div>
            </button>
          ))}
        </div>

        {/* Photo grid */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
          {PHOTO_SLOTS.map(slot=>{
            const has=previews[slot.id];
            return <div key={slot.id} onClick={()=>!has&&fileRefs.current[slot.id]?.click()} style={{border:`1.5px dashed ${has?BD:slot.required?"#2a2838":"#1a1828"}`,borderRadius:12,padding:has?0:"20px 12px",textAlign:"center",cursor:has?"default":"pointer",background:has?"#0e0d14":"transparent",overflow:"hidden",position:"relative",minHeight:has?0:slot.id==="main"?140:100}}>
              <input ref={el=>fileRefs.current[slot.id]=el} type="file" accept="image/*" capture="environment" style={{display:"none"}} onChange={e=>hFile(slot.id,e.target.files[0])}/>
              {has?<div style={{position:"relative"}}>
                <img src={previews[slot.id]} alt="" style={{width:"100%",height:slot.id==="main"?200:130,objectFit:"cover",display:"block"}}/>
                <button onClick={e=>{e.stopPropagation();removePhoto(slot.id)}} style={{position:"absolute",top:6,right:6,background:"rgba(0,0,0,0.8)",border:`1px solid ${BD}`,borderRadius:6,color:TX,width:26,height:26,fontSize:13,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}}>×</button>
                <div style={{position:"absolute",bottom:0,left:0,right:0,background:"rgba(0,0,0,0.7)",padding:"4px 8px",fontSize:10,color:MDC,fontFamily:"'DM Mono',monospace"}}>{slot.label}</div>
              </div>:<>
                <div style={{fontSize:20,marginBottom:6,opacity:0.3}}>{slot.icon}</div>
                <div style={{fontSize:12,fontWeight:500,color:slot.required?"#8a8698":"#4a4660"}}>{slot.label}{slot.required?"":" (optional)"}</div>
                <div style={{fontSize:10,color:DM,marginTop:2}}>{slot.hint}</div>
              </>}
            </div>
          })}
        </div>

        {/* Fields */}
        <div style={{marginTop:14,display:"flex",flexDirection:"column",gap:10}}>
          <div><label style={lb}>Tell Gramma about it</label><textarea value={desc} onChange={e=>setDesc(e.target.value)} placeholder='Labels, seller description, any context...' rows={2} style={{...ip,resize:"vertical"}}/></div>
          <div style={{display:"flex",gap:10}}>
            <div style={{flex:1}}><label style={lb}>Asking Price</label><div style={{position:"relative"}}><span style={{position:"absolute",left:14,top:"50%",transform:"translateY(-50%)",color:DM}}>$</span><input type="number" value={ask} onChange={e=>setAsk(e.target.value)} placeholder="0" style={{...ip,paddingLeft:28}}/></div></div>
            {mode==="full"&&<div style={{flex:1}}><label style={lb}>Source</label><select value={plat} onChange={e=>setPlat(e.target.value)} style={{...ip,appearance:"none"}}>{["Estate Sale","Thrift Store","Facebook Marketplace","Craigslist","OfferUp","Auction","Free/Curb"].map(p=><option key={p}>{p}</option>)}</select></div>}
          </div>
        </div>

        <button onClick={analyze} disabled={loading||(!hasAnyPhoto&&!desc)} style={{width:"100%",marginTop:16,padding:"16px",background:loading?"#1e1c2a":(!hasAnyPhoto&&!desc)?"#1e1c2a":`linear-gradient(135deg,${G},#8b6914)`,border:"none",borderRadius:12,color:loading||(!hasAnyPhoto&&!desc)?DM:"#000",fontSize:14,fontWeight:700,cursor:loading?"wait":"pointer",letterSpacing:"0.04em",textTransform:"uppercase",opacity:(!hasAnyPhoto&&!desc)?0.4:1}}>
          {loading?"":mode==="quick"?"⚡ Ask Gramma (Quick)":"🔍 Ask Gramma · Full Appraisal"}
        </button>

        {/* ═══ GRAMMA LOADING ANIMATION ═══ */}
        {loading&&<div style={{marginTop:16,padding:"20px 16px",background:BG2,border:`1px solid ${BD}`,borderRadius:16,overflow:"hidden",position:"relative"}}>
          <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:8}}>
            <div style={{width:"100%",height:100,position:"relative",overflow:"hidden"}}>
              <div className={danceMode==="walk"?"gramma-walking":"gramma-twerking"} style={{position:danceMode==="walk"?"absolute":"relative",left:danceMode==="walk"?0:"calc(50% - 40px)",top:danceMode==="walk"?10:0}}>
                <GrammaWalk size={80}/>
              </div>
            </div>
            <div style={{fontSize:14,color:HI,fontStyle:"italic",fontFamily:"'Instrument Serif',Georgia,serif",textAlign:"center"}}>{loadMsg}</div>
            <div style={{display:"flex",gap:4}}>{[0,1,2].map(i=><div key={i} style={{width:6,height:6,borderRadius:3,background:G,opacity:0.3+((Date.now()/400+i)%3===0?0.7:0),animation:`grammaBounce 0.6s ease-in-out ${i*0.2}s infinite`}}/>)}</div>
          </div>
        </div>}

        {(hasAnyPhoto||desc||res)&&!loading&&<button onClick={reset} style={{width:"100%",marginTop:6,padding:"10px",background:"none",border:`1px solid ${BD}`,borderRadius:10,color:DM,fontSize:12,cursor:"pointer"}}>Clear all</button>}
        {err&&<div style={{marginTop:12,padding:"12px 16px",background:"#1a0505",border:"1px solid #450a0a",borderRadius:10,color:"#f87171",fontSize:13}}>
          <div>{err}</div>
          <button onClick={analyze} style={{marginTop:8,padding:"6px 14px",background:"#2d0505",border:"1px solid #7a1414",borderRadius:8,color:"#f87171",fontSize:12,cursor:"pointer",fontFamily:"inherit"}}>Try Again</button>
        </div>}

        {/* Quick → Full upgrade */}
        {res&&res._mode==="quick"&&<div style={{marginTop:12,padding:"12px 16px",background:`${G}08`,border:`1px solid ${G}22`,borderRadius:10,cursor:"pointer"}} onClick={()=>{setMode("full");setTimeout(analyze,100)}}>
          <div style={{fontSize:13,fontWeight:600,color:G}}>Want Gramma to check her sources? Tap for Full Appraisal →</div>
        </div>}

        {/* ══ RESULTS ══ */}
        {res&&<div ref={rRef} style={{marginTop:20,animation:"fadeUp 0.4s ease"}}>
          {/* Quick results */}
          {res._mode==="quick"&&<>
            <div style={{...cd,borderColor:`${G}44`}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
                <div style={{flex:1}}>
                  <div style={{...lb,color:G,marginBottom:8}}>⚡ Gramma's quick take</div>
                  <div style={{fontSize:18,fontWeight:600,color:HI}}>{res.brand_or_designer}{res.specific_model?` — ${res.specific_model}`:""}</div>
                  <div style={{fontSize:13,color:"#8a8698",marginTop:4}}>{res.item_type}{res.era?` · ${res.era}`:""}{res.materials?` · ${res.materials}`:""}</div>
                  <div style={{fontSize:14,color:"#c4c0b8",lineHeight:1.6,marginTop:10,fontStyle:"italic"}}>{res.quick_notes}</div>
                </div>
                {res.estimated_resale_high>0&&<div style={{textAlign:"right",flexShrink:0}}>
                  <div style={{...lb,marginBottom:4}}>Est. range</div>
                  <div style={{fontFamily:"'DM Mono',monospace",fontSize:22,fontWeight:500,color:HI}}>${res.estimated_resale_low?.toLocaleString()}–${res.estimated_resale_high?.toLocaleString()}</div>
                </div>}
              </div>
            </div>
            {res.where_marks&&<div style={{...cd,marginTop:8}}><div style={{fontSize:12,fontWeight:600,color:"#8a8698",marginBottom:4}}>🏷 Gramma says check here for marks</div><div style={{fontSize:13,color:"#c4c0b8",lineHeight:1.6}}>{res.where_marks}</div></div>}
          </>}

          {/* Full results */}
          {res._mode==="full"&&<>
            {/* Verdict with Gramma's voice */}
            <div style={{background:v.bg,border:`1px solid ${v.bdr}33`,borderRadius:14,padding:"22px 24px"}}>
              <div style={{display:"flex",gap:12,marginBottom:10,alignItems:"center"}}>
                <div style={{width:44,height:44,borderRadius:12,background:BU,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}><GrammaWalk size={38}/></div>
                <div>
                  <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                    <span style={{fontSize:16}}>{v.ic}</span>
                    <span style={{fontFamily:"'DM Mono',monospace",fontSize:14,fontWeight:500,color:v.txt,letterSpacing:"0.08em"}}>{res.verdict}</span>
                    {res.profit_score&&<span style={{background:`${v.bdr}22`,border:`1px solid ${v.bdr}44`,borderRadius:6,padding:"2px 8px",fontSize:11,color:v.txt,fontFamily:"'DM Mono',monospace"}}>{res.profit_score}/10</span>}
                    {pb&&<span style={{background:pb.bg,border:`1px solid ${pb.bdr}44`,borderRadius:6,padding:"2px 8px",fontSize:10,color:pb.txt,fontFamily:"'DM Mono',monospace"}}>{pb.l}</span>}
                  </div>
                  <div style={{fontSize:12,color:v.txt,opacity:0.7,marginTop:2,fontFamily:"'Instrument Serif',serif",fontStyle:"italic"}}>{GRAMMA_VERDICTS[res.verdict]||""}</div>
                </div>
              </div>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-end",flexWrap:"wrap",gap:16}}>
                <div style={{flex:1,fontSize:14,color:"#c4c0b8",lineHeight:1.6,fontStyle:"italic"}}>{res.verdict_reason}</div>
                {res.estimated_resale_high>0&&<div style={{textAlign:"right",flexShrink:0}}>
                  <div style={{...lb,marginBottom:4}}>Est. Resale</div>
                  <div style={{fontFamily:"'DM Mono',monospace",fontSize:24,fontWeight:500,color:HI}}>${res.estimated_resale_low?.toLocaleString()}–${res.estimated_resale_high?.toLocaleString()}</div>
                  {res.resale_ceiling>0&&<div style={{fontSize:11,color:MDC,marginTop:2}}>Ceiling: ${res.resale_ceiling?.toLocaleString()}</div>}
                  {ask&&(()=>{const mid=(res.estimated_resale_low+res.estimated_resale_high)/2;const pr=Math.round(mid-+ask);return<div style={{marginTop:6,fontSize:12,fontFamily:"'DM Mono',monospace"}}><span style={{color:pr>0?"#4ade80":"#f87171"}}>{pr>0?"+":""}${pr.toLocaleString()} ({Math.round((mid/+ask-1)*100)}%)</span></div>})()}
                </div>}
              </div>
            </div>

            {/* Market data */}
            {(md.ebay_sold?.length||md.firstdibs_active?.length||md.chairish_active?.length||md.poshmark_sold?.length)?
            <div style={{...cd,marginTop:12,borderColor:"#065f46"}}>
              <div style={{...lb,color:"#22c55e",marginBottom:12}}>Gramma's sources — real sold prices</div>
              <Comp title="eBay Sold" items={md.ebay_sold} color="#4ade80" searchUrl={res.comp_search_terms?ebUrl(res.comp_search_terms):null}/>
              <Comp title="1stDibs" items={md.firstdibs_active} color="#fbbf24"/>
              <Comp title="Chairish" items={md.chairish_active} color="#a78bfa"/>
              <Comp title="Poshmark" items={md.poshmark_sold} color="#ec4899"/>
              {md.auction_results?.length>0&&<Comp title="Auctions" items={md.auction_results} color="#f59e0b"/>}
              {md.data_quality_note&&<div style={{fontSize:11,color:MDC,fontStyle:"italic",marginTop:4,paddingTop:8,borderTop:`1px solid ${BD}`}}>{md.data_quality_note}</div>}
            </div>:null}

            {/* ID + details */}
            <div style={{...cd,marginTop:12}}><div style={lb}>Identification</div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"14px 20px",marginTop:8}}>
                {[["Brand",res.brand_or_designer],["Model",res.specific_model],["Type",res.item_type],["Era",res.era],["Materials",res.materials]].map(([l2,vl])=>vl&&<div key={l2}><div style={{fontSize:10,color:DM,fontFamily:"'DM Mono',monospace"}}>{l2}</div><div style={{fontSize:14,fontWeight:500,color:HI,marginTop:2}}>{vl}</div></div>)}
              </div>
            </div>

            {[["Maker's Mark","🏷",res.makers_mark_analysis],["Authenticity","🔍",res.authenticity_notes],["Check Before Buying","👁",res.what_to_check],["Gramma's Negotiation Tip","💬",res.negotiation_tip],["History","📖",res.historical_context]].map(([t2,ic,c2])=>c2&&<div key={t2} style={{...cd,marginTop:8}}><div style={{fontSize:12,fontWeight:600,color:"#8a8698",marginBottom:5}}>{ic} {t2}</div><div style={{fontSize:13,color:"#c4c0b8",lineHeight:1.65,fontStyle:t2.includes("Tip")?"italic":"normal"}}>{c2}</div></div>)}

            {res.where_to_sell?.length>0&&<div style={{...cd,marginTop:8}}><div style={{...lb,marginBottom:8}}>Where Gramma says to sell</div><div style={{display:"flex",flexWrap:"wrap",gap:4}}>{res.where_to_sell.map((ch,i)=><span key={ch} style={{background:"#1e1c2a",borderRadius:6,padding:"4px 10px",fontSize:11,color:"#c4c0b8"}}>{i+1}. {ch}</span>)}</div></div>}
          </>}

          {/* ══ ACTION BAR ══ */}
          <div style={{display:"flex",gap:8,marginTop:16}}>
            {!purchased&&<button onClick={()=>setPurchased(true)} style={{flex:1,padding:"14px",background:"#22c55e11",border:"1px solid #22c55e33",borderRadius:12,color:"#4ade80",fontSize:13,fontWeight:600,cursor:"pointer"}}>✓ I bought it — Gramma, write my listing!</button>}
            <button onClick={exportPDF} style={{flex:purchased?1:0,minWidth:purchased?"auto":140,padding:"14px",background:"#1e1c2a",border:`1px solid ${BD}`,borderRadius:12,color:"#8a8698",fontSize:13,cursor:"pointer"}}>📄 Export PDF</button>
          </div>

          {/* ══ POST-PURCHASE ══ */}
          {purchased&&!listing&&<div style={{...cd,marginTop:12,borderColor:`${G}33`,animation:"fadeUp 0.3s ease"}}>
            <div style={{...lb,color:G,marginBottom:12}}>Tell Gramma the details for your listing</div>
            <div style={{display:"flex",gap:10,marginBottom:12}}>
              <div style={{flex:1}}><label style={{...lb,fontSize:9}}>Purchase Price</label>
                <div style={{position:"relative"}}><span style={{position:"absolute",left:12,top:"50%",transform:"translateY(-50%)",color:DM,fontSize:13}}>$</span>
                <input type="number" value={buyPrice} onChange={e=>setBuyPrice(e.target.value)} placeholder={ask||"0"} style={{...ip,paddingLeft:26,padding:"9px 14px 9px 26px",fontSize:13}}/></div>
              </div>
            </div>
            <div style={{marginBottom:12}}>
              <label style={{...lb,fontSize:9}}>Dimensions (inches)</label>
              <div style={{display:"flex",gap:8}}>
                {[["w","Width"],["d","Depth"],["h","Height"]].map(([k,label])=>(
                  <div key={k} style={{flex:1}}><input type="number" value={dims[k]} onChange={e=>setDims(d=>({...d,[k]:e.target.value}))} placeholder={label} style={{...ip,fontSize:13,padding:"9px 12px",textAlign:"center"}}/></div>
                ))}
              </div>
            </div>
            <button onClick={generateListing} disabled={listingLoading} style={{width:"100%",padding:"14px",background:listingLoading?"#1e1c2a":`linear-gradient(135deg,${G},#8b6914)`,border:"none",borderRadius:10,color:listingLoading?MDC:"#000",fontSize:13,fontWeight:700,cursor:listingLoading?"wait":"pointer",textTransform:"uppercase"}}>
              {listingLoading?<span style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,color:"#8a8698"}}><span style={{display:"inline-block",width:12,height:12,border:"2px solid #2a2838",borderTopColor:G,borderRadius:"50%",animation:"spin 0.7s linear infinite"}}/>Gramma's writing your listing...</span>:"Gramma, write my listing!"}
            </button>
          </div>}

          {/* ══ LISTING OUTPUT ══ */}
          {listing&&<div ref={listRef} style={{marginTop:12,animation:"fadeUp 0.4s ease"}}>
            <div style={{...cd,borderColor:"#22c55e33"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
                <div style={{...lb,color:"#22c55e",marginBottom:0}}>Gramma wrote your listing — ready to post!</div>
                <CopyBtn text={listing.title+"\n\n"+listing.description+"\n\nTags: "+(listing.tags||[]).join(", ")} label="all"/>
              </div>
              {[["TITLE",listing.title,16],["DESCRIPTION",listing.description,13]].map(([label,text,fs])=>(
                <div key={label} style={{background:"#0e0d14",borderRadius:10,padding:"14px 16px",marginBottom:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:10}}>
                    <div style={{flex:1}}><div style={{fontSize:10,color:DM,fontFamily:"'DM Mono',monospace",marginBottom:4}}>{label}</div>
                      <div style={{fontSize:fs,fontWeight:label==="TITLE"?600:400,color:HI,lineHeight:1.6,whiteSpace:label==="DESCRIPTION"?"pre-wrap":"normal"}}>{text}</div>
                    </div><CopyBtn text={text} label={label.toLowerCase()}/>
                  </div>
                </div>
              ))}
              {listing.tags?.length>0&&<div style={{background:"#0e0d14",borderRadius:10,padding:"14px 16px",marginBottom:10}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:10}}>
                  <div style={{flex:1}}><div style={{fontSize:10,color:DM,fontFamily:"'DM Mono',monospace",marginBottom:6}}>TAGS</div>
                    <div style={{display:"flex",flexWrap:"wrap",gap:5}}>{listing.tags.map(t=><span key={t} style={{background:"#1e1c2a",borderRadius:6,padding:"3px 10px",fontSize:12,color:"#8a8698"}}>{t}</span>)}</div>
                  </div><CopyBtn text={listing.tags.join(", ")} label="tags"/>
                </div>
              </div>}
              <div style={{display:"flex",gap:10}}>
                {listing.suggested_price_quick_sale&&<div style={{flex:1,background:"#0e0d14",borderRadius:10,padding:"12px 16px",textAlign:"center"}}>
                  <div style={{fontSize:10,color:DM,fontFamily:"'DM Mono',monospace"}}>Quick sale</div>
                  <div style={{fontSize:20,fontWeight:600,color:"#84cc16",marginTop:4,fontFamily:"'DM Mono',monospace"}}>${listing.suggested_price_quick_sale.toLocaleString()}</div>
                </div>}
                {listing.suggested_price_max_value&&<div style={{flex:1,background:"#0e0d14",borderRadius:10,padding:"12px 16px",textAlign:"center"}}>
                  <div style={{fontSize:10,color:DM,fontFamily:"'DM Mono',monospace"}}>Max value</div>
                  <div style={{fontSize:20,fontWeight:600,color:G,marginTop:4,fontFamily:"'DM Mono',monospace"}}>${listing.suggested_price_max_value.toLocaleString()}</div>
                </div>}
              </div>
              {listing.best_platform&&<div style={{fontSize:12,color:MDC,marginTop:10,fontStyle:"italic",textAlign:"center"}}>{listing.best_platform}</div>}
            </div>
          </div>}
        </div>}
      </div>}

      {/* ══════ BATCH SCAN ══════ */}
      {tab==="batch"&&<div style={{animation:"fadeUp 0.3s ease"}}>
        <div style={{...cd,marginBottom:14,borderColor:`${G}33`}}>
          <div style={{...lb,color:G,marginBottom:4}}>Batch Scanner — identify many items at once</div>
          <div style={{fontSize:12,color:MDC,lineHeight:1.5}}>Upload up to 20 photos. Gramma identifies each one simultaneously — results appear as they finish.</div>
        </div>
        <input ref={batchInputRef} type="file" accept="image/*" multiple style={{display:"none"}} onChange={e=>handleBatchSelect(e.target.files)}/>
        <div onClick={()=>batchInputRef.current?.click()} style={{border:`2px dashed ${batchFiles.length?BD:G+"44"}`,borderRadius:14,padding:"28px 16px",textAlign:"center",cursor:"pointer",marginBottom:14,background:"#0a0910"}}>
          <div style={{fontSize:28,marginBottom:8}}>📸</div>
          <div style={{fontSize:14,fontWeight:600,color:HI}}>Tap to add photos</div>
          <div style={{fontSize:11,color:DM,marginTop:3}}>Select multiple from camera roll — up to 20 items</div>
        </div>
        {batchFiles.length>0&&<>
          <div style={{display:"flex",gap:8,marginBottom:14}}>
            <button onClick={runBatchScan} disabled={batchRunning||!batchFiles.some(f=>f.status==="idle")} style={{flex:1,padding:"14px",background:batchRunning||!batchFiles.some(f=>f.status==="idle")?"#1e1c2a":`linear-gradient(135deg,${G},#8b6914)`,border:"none",borderRadius:12,color:batchRunning||!batchFiles.some(f=>f.status==="idle")?DM:"#000",fontSize:14,fontWeight:700,cursor:batchRunning?"wait":"pointer",letterSpacing:"0.04em",textTransform:"uppercase"}}>
              {batchRunning?`Scanning... ${batchFiles.filter(f=>f.status==="done"||f.status==="error").length}/${batchFiles.length} done`:
                batchFiles.some(f=>f.status==="idle")?`⚡ Scan All (${batchFiles.filter(f=>f.status==="idle").length} items)`:"✓ All scanned"}
            </button>
            <button onClick={()=>setBatchFiles([])} style={{padding:"14px 16px",background:"none",border:`1px solid ${BD}`,borderRadius:12,color:DM,fontSize:13,cursor:"pointer"}}>Clear</button>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
            {batchFiles.map(item=>{
              const bv=item.result?.verdict?VD[item.result.verdict]||VD["MAYBE"]:null;
              return <div key={item.id} style={{...cd,padding:0,overflow:"hidden",position:"relative",cursor:"default"}}>
                <img src={item.preview} alt="" style={{width:"100%",height:120,objectFit:"cover",display:"block"}}/>
                <div style={{position:"absolute",top:6,right:6}}>
                  {item.status==="loading"&&<div style={{width:22,height:22,border:`2px solid #2a2838`,borderTopColor:G,borderRadius:"50%",animation:"spin 0.7s linear infinite"}}/>}
                  {item.status==="done"&&bv&&<div style={{background:bv.bdr,borderRadius:5,padding:"2px 7px",fontSize:10,fontWeight:700,color:"#000",letterSpacing:"0.04em"}}>{item.result.verdict==="STRONG BUY"?"⚡ SB":item.result.verdict}</div>}
                  {item.status==="error"&&<div style={{background:"#7a1414",borderRadius:5,padding:"2px 7px",fontSize:10,color:"#f87171"}}>ERR</div>}
                </div>
                <button onClick={e=>{e.stopPropagation();setBatchFiles(prev=>prev.filter(f=>f.id!==item.id))}} style={{position:"absolute",top:6,left:6,background:"rgba(0,0,0,0.75)",border:"none",borderRadius:4,color:"#8a8698",width:22,height:22,fontSize:12,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}}>×</button>
                <div style={{padding:"8px 10px"}}>
                  {item.status==="idle"&&<div style={{fontSize:11,color:DM}}>Ready</div>}
                  {item.status==="loading"&&<div style={{fontSize:11,color:G,fontStyle:"italic"}}>Gramma's looking...</div>}
                  {item.status==="done"&&item.result&&<>
                    <div style={{fontSize:12,fontWeight:600,color:HI,lineHeight:1.3,marginBottom:2}}>{item.result.brand_or_designer||"Unknown"}</div>
                    <div style={{fontSize:10,color:MDC}}>{[item.result.era,item.result.item_type].filter(Boolean).join(" · ")}</div>
                    {item.result.estimated_resale_high>0&&<div style={{fontFamily:"'DM Mono',monospace",fontSize:12,color:bv?.txt||HI,marginTop:3}}>${item.result.estimated_resale_low?.toLocaleString()}–${item.result.estimated_resale_high?.toLocaleString()}</div>}
                    <button onClick={()=>{setMode("full");setPhotos({main:item.compressed,mark:null,detail:null,extra:null});setPreviews({main:item.preview,mark:null,detail:null,extra:null});setRes(null);setErr(null);setPurchased(false);setListing(null);setTab("scan");}} style={{width:"100%",marginTop:6,padding:"5px",background:`${G}11`,border:`1px solid ${G}33`,borderRadius:6,color:G,fontSize:10,cursor:"pointer",fontFamily:"inherit"}}>Full Appraisal →</button>
                  </>}
                  {item.status==="error"&&<>
                    <div style={{fontSize:10,color:"#f87171",marginBottom:4}}>{item.error||"Scan failed"}</div>
                    <button onClick={()=>setBatchFiles(prev=>prev.map(f=>f.id===item.id?{...f,status:"idle",error:null}:f))} style={{width:"100%",padding:"4px",background:"#2d0505",border:"1px solid #7a1414",borderRadius:5,color:"#f87171",fontSize:10,cursor:"pointer"}}>Retry</button>
                  </>}
                </div>
              </div>;
            })}
          </div>
        </>}
      </div>}

      {/* ══════ HISTORY ══════ */}
      {tab==="history"&&<div style={{animation:"fadeUp 0.3s ease"}}>
        {hist.length===0?<div style={{textAlign:"center",padding:"60px 20px",color:DM}}><div style={{marginBottom:12}}><GrammaWalk size={60}/></div>No scans yet. Show Gramma something!</div>
        :<><div style={{display:"flex",justifyContent:"space-between",marginBottom:14}}><span style={{fontSize:13,color:MDC}}>{hist.length} scans</span><button onClick={()=>sH([])} style={{background:"none",border:`1px solid ${BD}`,borderRadius:8,color:DM,padding:"5px 12px",fontSize:11,cursor:"pointer"}}>Clear</button></div>
          {hist.map(h=>{const vd=h.r?.verdict?VD[h.r.verdict]||VD["MAYBE"]:null;const ex=exH===h.id;
          return(
            <div key={h.id} onClick={()=>setExH(ex?null:h.id)} style={{...cd,marginBottom:8,cursor:"pointer",borderColor:ex?`${G}44`:BD}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <div>
                  <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
                    {h.mode==="quick"&&<span style={{fontSize:10,color:G,fontFamily:"'DM Mono',monospace",border:`1px solid ${G}33`,borderRadius:4,padding:"1px 5px"}}>QUICK</span>}
                    {vd&&<span style={{color:vd.txt,fontFamily:"'DM Mono',monospace",fontSize:11,fontWeight:600}}>{h.r?.verdict}</span>}
                    <span style={{fontSize:13,fontWeight:600,color:HI}}>{h.r?.brand_or_designer||"Unknown"}</span>
                  </div>
                  <div style={{fontSize:11,color:DM,marginTop:4,fontFamily:"'DM Mono',monospace"}}>{new Date(h.ts).toLocaleDateString()} · {h.plat||"—"}</div>
                </div>
                {h.r?.estimated_resale_high>0&&<div style={{fontFamily:"'DM Mono',monospace",fontSize:14,color:HI,flexShrink:0}}>${h.r.estimated_resale_low?.toLocaleString()}–${h.r.estimated_resale_high?.toLocaleString()}</div>}
              </div>
              {ex&&<div style={{marginTop:12,paddingTop:12,borderTop:`1px solid ${BD}`,fontSize:13,color:"#8a8698",lineHeight:1.6,fontStyle:"italic"}}>{h.r?.verdict_reason||h.r?.quick_notes}</div>}
            </div>)})}</>}
      </div>}

      {/* ══════ BRANDS ══════ */}
      {tab==="brands"&&<div style={{animation:"fadeUp 0.3s ease"}}>
        <div style={{display:"flex",gap:8,marginBottom:16}}>{["furniture","clothing"].map(c=><button key={c} onClick={()=>setBc(c)} style={{flex:1,background:bc===c?"#1e1c2a":"none",border:`1px solid ${bc===c?G+"44":BD}`,borderRadius:10,padding:"10px",color:bc===c?HI:MDC,fontSize:13,fontWeight:500,cursor:"pointer",textTransform:"capitalize"}}>{c}</button>)}</div>
        <div style={{display:"flex",gap:6,marginBottom:16,flexWrap:"wrap"}}>{["all","tier1","tier2","tier3"].map(f=><button key={f} onClick={()=>setBf(f)} style={{background:bf===f?"#1e1c2a":"none",border:`1px solid ${bf===f?G+"44":BD}`,borderRadius:8,padding:"5px 12px",color:bf===f?HI:DM,fontSize:11,cursor:"pointer",fontFamily:"'DM Mono',monospace"}}>{f==="all"?"All":BRANDS[bc][f]?.label}</button>)}</div>
        {Object.entries(BRANDS[bc]).filter(([k])=>bf==="all"||k===bf).map(([tier,data])=><div key={tier} style={{marginBottom:20}}>
          <div style={{fontSize:12,fontWeight:600,color:data.color,marginBottom:10,fontFamily:"'DM Mono',monospace"}}>{data.label}</div>
          {data.brands.map(b=><div key={b.n} style={{...cd,marginBottom:6,padding:"14px 18px",cursor:"pointer"}} onClick={()=>window.open(ebUrl(b.n+" vintage"),"_blank")}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
              <div><div style={{fontSize:14,fontWeight:600,color:HI}}>{b.n}</div><div style={{fontSize:12,color:MDC,marginTop:4}}>{b.h}</div></div>
              <div style={{textAlign:"right",flexShrink:0,marginLeft:16}}><div style={{fontFamily:"'DM Mono',monospace",fontSize:13,color:data.color}}>${b.r[0].toLocaleString()}–${b.r[1].toLocaleString()}</div><div style={{fontSize:9,color:DM,marginTop:2}}>tap → eBay</div></div>
            </div>
          </div>)}
        </div>)}
      </div>}

      </div>
    </div>
  );
}
