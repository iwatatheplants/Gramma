# CLAUDE.md — Gramma Project Spec

## What is Gramma?

Gramma is an AI-powered vintage furniture and designer clothing appraisal platform
for resellers, dealers, and collectors. The brand character is "Gramma" — a warm,
sharp, no-nonsense retired antique dealer with 45 years of experience.

The tagline is "Ask Gramma!" — users say this when they want to know what something
is worth. Gramma searches real sold prices from eBay, 1stDibs, Chairish, Poshmark,
and auction records, then delivers a verdict in her distinctive voice.

## Architecture

```
gramma/
├── app/
│   └── gramma.jsx          # Main React app (Claude.ai artifact)
├── monitors/
│   ├── craigslist.py        # CL RSS monitor (5 feeds, 10s polling)
│   ├── swoopa.py            # Swoopa email pipeline (Gmail IMAP)
│   └── launcher.py          # Combined launcher for all monitors
├── api/
│   └── ebay.py              # eBay Browse API client + Flask server
├── docs/
│   ├── SETUP.md             # Setup guide
│   └── starter_guide.md     # Beginner's vintage arbitrage guide
├── tracking/
│   └── flip_tracker.xlsx    # P&L spreadsheet with dashboard
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # This file
└── README.md                # Project README
```

## Tech Stack

- **Frontend**: React JSX (renders as Claude.ai artifact)
- **AI Models**: Claude Haiku 4.5 (quick ID, pre-screening) + Claude Sonnet 4 (full appraisals, listings)
- **Web Search**: Anthropic web_search tool for real sold comps
- **eBay API**: Browse API v1 for structured active listing data (free)
- **Monitors**: Python 3.12+, feedparser (RSS), imaplib (email)
- **Notifications**: ntfy.sh (free push notifications)
- **Storage**: window.storage (Claude.ai persistent storage) for scan history

## Key Design Decisions

1. **Two-stage AI pipeline**: Haiku pre-screens (~$0.001/listing, 1-2s) to filter ~80%
   junk before Sonnet + web search (~$0.04/listing, 10-20s). Reduces avg cost from
   $0.04 to ~$0.01 per listing.

2. **Multi-source comps**: Every full appraisal searches eBay sold (floor), 1stDibs
   (ceiling), Chairish (mid-market), Poshmark (clothing), and auction records.

3. **Gramma's voice**: All AI responses use Gramma's personality — warm, direct,
   knowledgeable. Verdict reasons and negotiation tips are written in her voice.

4. **Multi-photo upload**: 4 slots (item, maker's mark, construction, label/other).
   All photos sent to Claude in one API call with labeled context.

5. **Post-purchase pipeline**: After buying, users enter price + dimensions → Gramma
   generates professional listing description with title, tags, and pricing.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Test eBay API connection
python3 api/ebay.py test

# Scan for underpriced eBay deals
python3 api/ebay.py deals

# Market analysis
python3 api/ebay.py market "broyhill brasilia credenza"

# Start Craigslist monitor
python3 monitors/craigslist.py

# Test Craigslist feeds
python3 monitors/craigslist.py test

# Start all monitors
python3 monitors/launcher.py

# Start eBay API server (port 5050)
python3 api/ebay.py server
```

## Coding Conventions

- Python: f-strings, no nested f-strings (causes syntax errors — extract to variable first)
- JSX: inline styles (no CSS modules), DM Sans + DM Mono + Instrument Serif fonts
- Colors: Gold #C8A24E (accent), Burgundy #8B3A3A (Gramma), Dark #07060a (bg)
- All API calls wrapped in try/catch with user-friendly error messages in Gramma's voice
- Model names: "claude-haiku-4-5-20251001" (quick) and "claude-sonnet-4-20250514" (full)
- Storage keys prefixed with "gramma-" (e.g. "gramma-h" for history)

## Known Issues to Fix

1. **Swoopa launcher.py references old filenames** — needs updating to point to
   monitors/craigslist.py and monitors/swoopa.py instead of vintage_scout_monitor.py

2. **No error retry logic in JSX** — API failures should offer a "Try again" button

3. **Landing page not rebuilt with Gramma branding** — still says "Vintage Scout"

4. **No rate limiting on client-side API calls** — users could accidentally burn through
   quota by rapid-scanning

5. **PDF export uses window.open + print** — works but should use a proper PDF library
   for better formatting and direct download

6. **eBay API not yet integrated into the JSX app** — ebay.py works standalone but
   the web app doesn't call it yet (needs the Flask server running)

7. **No authentication or user accounts** — needed before SaaS launch (Supabase/Clerk
   + Stripe for payments)

## Improvement Opportunities

### High Priority
- Add scan counter per session to prevent accidental overuse
- Add "Try again" button on API errors
- Integrate eBay active listing data into Full Appraisal results
- Add visual matches (eBay image search) to results
- Rebuild landing page with Gramma branding + revised pricing ($19/$49/$99)

### Medium Priority
- Add sell-through rate data (how fast items sell, not just price)
- Add condition-adjusted pricing (mint vs good vs fair)
- Chrome extension for scanning listings while browsing
- React Native wrapper for App Store / Play Store distribution
- Add "Gramma's Daily Deals" email digest from eBay deal scanner

### Low Priority
- Add voice input ("Hey Gramma, what's this worth?")
- Social sharing of appraisals
- Community features (share finds, rate accuracy)
- Multi-language support
- Gramma sticker pack / merch store

## Gramma's Character

- **Name**: Gramma
- **Role**: Retired antique dealer turned AI appraiser
- **Personality**: Warm, sharp, no-nonsense, slightly mischievous
- **Visual**: Silver updo, cat-eye glasses (gold frames), burgundy cardigan,
  pearl necklace, magnifying glass + price tag as signature tools
- **Voice examples**:
  - STRONG BUY: "Oh honey, GRAB this immediately!"
  - BUY: "Solid find — Gramma approves."
  - MAYBE: "Hmm, I've seen better deals, dear."
  - PASS: "Put it down, sweetheart. Not worth your gas money."
  - Loading: "Gramma's checking her records..."
  - Error: "Gramma couldn't read that, dear. Try again?"

## Pricing Model (SaaS)

| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | 3 Quick IDs + 1 Full Appraisal/month |
| Pro | $19/mo | 50 Full + unlimited Quick IDs |
| Dealer | $49/mo | 200 Full + eBay deals digest + image search |
| Team | $99/mo | 500 Full + 3 seats + API access |

Annual discount: 2 months free.

## Current Sprint

> Update this section at the start of each session.

**Status**: Pre-launch / MVP buildout

**Working on now**:
- [ ] Rebuild landing page with Gramma branding (remove "Vintage Scout" references)
- [ ] Integrate eBay active listing data into Full Appraisal results
- [ ] Add scan counter per session to prevent accidental overuse

**Recently completed**:
- Batch photo scan tab (Promise.allSettled, parallel processing, per-card retry)
- Client-side image compression (max 1200px, 82% JPEG)
- Exponential backoff on API calls (3 retries, 2/4/8s)
- Batch Haiku prescreening (8 listings per call, ~8x efficiency gain)
- Local dev setup (Vite + fetch interceptor in src/main.jsx)
- Registered askgramma.app and askgramma.io domains

## Decision Log

> Record key decisions here so they don't get re-litigated.

| Date | Decision | Reason |
|------|----------|--------|
| 2026-03 | Primary domain: askgramma.app | askgramma.com parked by unrelated VPS company, .app is clean and enforces HTTPS |
| 2026-03 | Skipped askgramma.ai ($100/yr) | Too expensive to park a redirect; trademark is the real protection |
| 2026-03 | Skipped gramma.app ($1,988) | No ROI at MVP stage; revisit post-revenue |
| 2026-03 | Wyoming LLC over California | Avoids $800/yr CA franchise tax; use Northwest Registered Agent (~$39/yr) |
| 2026-03 | Form LLC before USPTO filing | Trademark should be filed under entity name from the start |
| 2026-03 | Trademark "Ask Gramma!" Class 42 | AI/software services; file TEAS Plus after LLC is formed |
| 2026-03 | Two-stage AI pipeline (Haiku + Sonnet) | Haiku filters ~80% junk at $0.001/listing before $0.04 Sonnet call |
| 2026-03 | No Linear/Notion for project tracking | Solo founder; CLAUDE.md + GitHub Issues is sufficient |

## Competitive Positioning

Gramma is NOT a generalist scanning tool. Gramma is a specialist for vintage
furniture, mid-century modern, and designer clothing. The differentiation:

- 5 data sources (vs 1 for generalist apps)
- Multi-photo maker's mark analysis (vs single photo)
- Post-purchase listing generator (vs scan-only)
- A memorable brand character (vs forgettable tool names)
- "Curio tells you what it is. Gramma tells you what it's worth."
