# Gramma — "Ask Gramma!"

### The best vintage finder and value identifier in the galaxy.

Gramma is an AI-powered vintage furniture and designer clothing appraisal platform.
Snap a photo, get real sold prices from 5 sources in 15 seconds.

**Not AI guesses. Actual market data.**

---

## What Gramma Does

📸 **Scan** — Upload 1-4 photos (item + maker's mark + construction + labels)

🔍 **Appraise** — AI searches eBay sold, 1stDibs, Chairish, Poshmark, and auction records

⚡ **Decide** — STRONG BUY / BUY / MAYBE / PASS with profit calculation

📝 **List** — One-tap professional listing generator with title, description, tags, pricing

📄 **Export** — Print-ready PDF appraisal document

📱 **Monitor** — Automated alerts for underpriced listings on Craigslist and Facebook Marketplace

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd gramma
pip install -r requirements.txt

# 2. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Open app/gramma.jsx in Claude.ai as an artifact

# 4. (Optional) Start Craigslist monitor
python3 monitors/craigslist.py

# 5. (Optional) Set up eBay API for market data
export EBAY_CLIENT_ID="..." && export EBAY_CLIENT_SECRET="..."
python3 api/ebay.py test
```

See `docs/SETUP.md` for full configuration guide.

---

## Project Structure

```
gramma/
├── app/gramma.jsx           # Main app (React artifact)
├── monitors/
│   ├── craigslist.py        # CL RSS monitor (10s polling, 5 feeds)
│   ├── swoopa.py            # Swoopa email pipeline
│   └── launcher.py          # Runs all monitors together
├── api/ebay.py              # eBay Browse API client + deal scanner
├── tracking/flip_tracker.xlsx  # P&L spreadsheet
├── docs/                    # Setup guide + starter guide
├── CLAUDE.md                # Full project spec for Claude Code
└── README.md                # This file
```

---

## Two Modes

| Mode | Speed | Model | What You Get |
|------|-------|-------|-------------|
| ⚡ Quick Look | ~2 sec | Haiku | Brand, era, estimate, where to check marks |
| 🔍 Full Appraisal | ~15 sec | Sonnet + web search | Multi-source comps, verdict, negotiation tips |

---

## Monthly Cost

| Usage | API Cost | Total |
|-------|----------|-------|
| Casual (CL only) | ~$8 | ~$8 |
| Serious (CL + Swoopa) | ~$21 | ~$71-121 |
| Full-time | ~$52 | ~$152 |

One flip pays for months of costs.

---

## Meet Gramma

> *"Oh honey, that's not Danish. That's IKEA with a coat of tung oil. Put it back."*

Gramma grew up above her parents' antique shop in Pacific Heights.
By 8, she could identify Heywood-Wakefield by touch.
45 years as the Bay Area's most trusted vintage dealer.
Now she's retired — but she can't stop appraising.

**Ask Gramma!**
