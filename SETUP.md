# Vintage Scout — Complete Setup Guide

## Architecture

```
DETECTION:
  Craigslist RSS  → vintage_scout_monitor.py (10s polling, 5 broad feeds)
  Swoopa Email    → swoopa_pipeline.py (Gmail IMAP)
  Manual          → vintage_scout_ultimate.jsx (multi-photo web app)
  eBay API        → ebay_api.py (deal scanner + structured comps)

EVALUATION (two-stage):
  Stage 1: Haiku pre-screen (1-2s, ~$0.001) → filters ~80%
  Stage 2: Sonnet + web_search (10-20s, ~$0.04) → multi-source comps
  eBay API: Active listing data (free, instant) → current market prices

POST-PURCHASE:
  Listing generator → title + description + tags + pricing
  PDF export → print-ready appraisal document

NOTIFICATION:
  ntfy.sh → push with photo + comps + verdict + link
```

## Step 1: Get API Keys

### Anthropic (required)
1. https://console.anthropic.com → create account
2. Copy API key: `export ANTHROPIC_API_KEY="sk-ant-..."`
3. Cost: ~$0.01/listing avg with two-stage pipeline

### eBay Developer (free, optional)
1. https://developer.ebay.com/join → free account
2. https://developer.ebay.com/my/keys → create Production app
3. Copy App ID + Cert ID:
```bash
export EBAY_CLIENT_ID="your-app-id"
export EBAY_CLIENT_SECRET="your-cert-id"
```
4. Cost: $0. Limit: 5,000 calls/day (free to increase)

### ntfy.sh (free, optional)
1. Install ntfy app on phone
2. Subscribe to unique topic (e.g. `vintage-scout-yourname`)

## Step 2: Install

```bash
pip install feedparser requests flask flask-cors --break-system-packages
```

## Step 3: Run

```bash
# Test eBay API connection
python3 ebay_api.py test

# Scan vintage brands for underpriced eBay deals
python3 ebay_api.py deals

# Market analysis for specific item
python3 ebay_api.py market "broyhill brasilia credenza"

# Start Craigslist monitor
python3 vintage_scout_monitor.py

# Start eBay API server (for web app integration)
python3 ebay_api.py server

# Start all monitors together
python3 run_scout.py
```

## eBay API: What It Adds

Claude web_search finds **sold** listings. eBay Browse API finds **active** listings.

| Data | web_search | eBay API |
|---|---|---|
| Sold prices | Yes | No |
| Active prices (structured) | Partial | Yes |
| Market supply count | No | Yes |
| Image-based search | No | Yes |
| Price percentile | No | Yes |

## Monthly Costs

| | Casual | Serious | Full-time |
|---|---|---|---|
| Anthropic API | ~$8 | ~$21 | ~$52 |
| eBay API | $0 | $0 | $0 |
| Swoopa | $0 | $50-100 | $100 |
| **Total** | **~$8** | **~$76** | **~$152** |

## Files

| File | Purpose |
|---|---|
| vintage_scout_ultimate.jsx | Web app: multi-photo, dual-mode, listing gen, PDF |
| vintage_scout_monitor.py | Craigslist monitor: 5 feeds, 10s poll, two-stage AI |
| swoopa_pipeline.py | Swoopa email monitor |
| ebay_api.py | eBay API: search, image search, deals, market analysis |
| run_scout.py | Combined launcher |
| vintage_scout_tracker.xlsx | Flip P&L tracker with dashboard |
| vintage_scout_landing.jsx | SaaS landing page |
