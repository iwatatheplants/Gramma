#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  GRAMMA — eBay Browse API Integration                   ║
║  Structured active listing data · Image search · Market comps  ║
║  Free API · OAuth client credentials · 5,000 calls/day         ║
╚══════════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
  The eBay Browse API searches ACTIVE listings (what's currently for sale).
  Claude's web_search finds SOLD/completed listings (what actually sold).
  Together they give you the full market picture:
    → Active listings = current asking prices, market supply, competition
    → Sold listings = actual transaction prices, demand validation
    → Image search = find visually similar items you might have missed

SETUP:
  1. Join eBay Developers Program (free): https://developer.ebay.com/join
  2. Create an application: https://developer.ebay.com/my/keys
  3. Copy your Production App ID (Client ID) and Cert ID (Client Secret)
  4. Set environment variables:
       export EBAY_CLIENT_ID="your-client-id"
       export EBAY_CLIENT_SECRET="your-client-secret"
  5. pip install requests

USAGE:
  from ebay_api import EbayClient

  client = EbayClient()

  # Search by keywords
  results = client.search("broyhill brasilia credenza", max_results=10)

  # Search by image (Base64)
  results = client.search_by_image(base64_image_data, max_results=10)

  # Get market analysis
  analysis = client.market_analysis("herman miller eames lounge chair")

  # Get structured comps for Scout integration
  comps = client.get_comps_for_scout("knoll tulip table", asking_price=150)

API LIMITS:
  Default: 5,000 calls/day (application-level, not per-user)
  Free to increase: Submit "Application Growth Check" when approaching limit
  OAuth tokens expire every 2 hours (auto-refreshed by this module)

COST: $0. The eBay Browse API is completely free.
"""

import os
import time
import base64
import json
import re
import requests
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote


class EbayClient:
    """eBay Browse API client with OAuth and caching."""

    OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    BROWSE_URL = "https://api.ebay.com/buy/browse/v1"
    SCOPE = "https://api.ebay.com/oauth/api_scope"

    # eBay category IDs for vintage/furniture/clothing
    CATEGORIES = {
        "furniture": "3197",            # Home & Garden > Furniture
        "antiques_furniture": "20091",  # Antiques > Furniture
        "mid_century": "183081",        # MCM subcategory
        "vintage_clothing": "175759",   # Clothing > Vintage
        "designer_clothing": "15724",   # Clothing, Shoes & Accessories
    }

    def __init__(self, client_id=None, client_secret=None, cache_dir=None):
        self.client_id = client_id or os.environ.get("EBAY_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("EBAY_CLIENT_SECRET", "")
        self.cache_dir = Path(cache_dir or "scout_data/ebay_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._token = None
        self._token_expiry = 0

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "eBay API credentials required.\n"
                "Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET environment variables.\n"
                "Get them free at: https://developer.ebay.com/my/keys"
            )

    # ══════════════════════════════════════════════════════════════
    # OAUTH
    # ══════════════════════════════════════════════════════════════

    def _get_token(self):
        """Get or refresh OAuth token (client credentials grant)."""
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        r = requests.post(
            self.OAUTH_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {creds}",
            },
            data={
                "grant_type": "client_credentials",
                "scope": self.SCOPE,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 7200)
        return self._token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "X-EBAY-C-ENDUSERCTX": "contextualLocation=country%3DUS%2Czip%3D94105",
        }

    # ══════════════════════════════════════════════════════════════
    # SEARCH
    # ══════════════════════════════════════════════════════════════

    def search(self, query, max_results=20, category_id=None, min_price=None,
               max_price=None, condition=None, sort="price", buying_options=None):
        """
        Search eBay active listings by keyword.

        Args:
            query: Search keywords (e.g. "broyhill brasilia credenza")
            max_results: Number of results (1-200)
            category_id: eBay category ID to filter by
            min_price: Minimum price USD
            max_price: Maximum price USD
            condition: "NEW", "USED", "UNSPECIFIED"
            sort: "price", "-price", "newlyListed", "endingSoonest"
            buying_options: "FIXED_PRICE", "AUCTION", "BEST_OFFER"

        Returns:
            List of item dicts with: title, price, condition, url, image, seller, location
        """
        params = {
            "q": query,
            "limit": min(max_results, 200),
            "sort": sort,
        }

        filters = []
        if min_price is not None:
            filters.append(f"price:[{min_price}..{max_price or ''}],priceCurrency:USD")
        elif max_price is not None:
            filters.append(f"price:[..{max_price}],priceCurrency:USD")

        if condition:
            filters.append(f"conditions:{{{condition}}}")
        if buying_options:
            filters.append(f"buyingOptions:{{{buying_options}}}")
        if category_id:
            params["category_ids"] = category_id

        if filters:
            params["filter"] = ",".join(filters)

        try:
            r = requests.get(
                f"{self.BROWSE_URL}/item_summary/search",
                headers=self._headers(),
                params=params,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()

            items = []
            for item in data.get("itemSummaries", []):
                price_val = item.get("price", {})
                items.append({
                    "title": item.get("title", ""),
                    "price": float(price_val.get("value", 0)),
                    "currency": price_val.get("currency", "USD"),
                    "condition": item.get("condition", ""),
                    "url": item.get("itemWebUrl", ""),
                    "affiliate_url": item.get("itemAffiliateWebUrl", ""),
                    "image": (item.get("image") or {}).get("imageUrl", ""),
                    "item_id": item.get("itemId", ""),
                    "seller": (item.get("seller") or {}).get("username", ""),
                    "location": item.get("itemLocation", {}).get("postalCode", ""),
                    "buying_options": item.get("buyingOptions", []),
                    "listing_date": item.get("itemCreationDate", ""),
                    "categories": [c.get("categoryName", "") for c in item.get("categories", [])],
                })

            return items

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠️  eBay API rate limit hit. Daily limit: 5,000 calls.")
            raise
        except Exception as e:
            print(f"eBay API error: {e}")
            return []

    def search_by_image(self, image_base64, max_results=20, category_id=None):
        """
        Search eBay by image — find visually similar items.

        Args:
            image_base64: Base64-encoded image data (no data URI prefix)
            max_results: Number of results
            category_id: Optional category filter

        Returns:
            List of item dicts (same format as search())
        """
        # Strip data URI prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        params = {"limit": min(max_results, 200)}
        if category_id:
            params["category_ids"] = category_id

        body = {"image": image_base64}

        try:
            r = requests.post(
                f"{self.BROWSE_URL}/item_summary/search_by_image",
                headers=self._headers(),
                params=params,
                json=body,
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()

            items = []
            for item in data.get("itemSummaries", []):
                price_val = item.get("price", {})
                items.append({
                    "title": item.get("title", ""),
                    "price": float(price_val.get("value", 0)),
                    "currency": price_val.get("currency", "USD"),
                    "condition": item.get("condition", ""),
                    "url": item.get("itemWebUrl", ""),
                    "image": (item.get("image") or {}).get("imageUrl", ""),
                    "item_id": item.get("itemId", ""),
                })

            return items

        except Exception as e:
            print(f"eBay image search error: {e}")
            return []

    # ══════════════════════════════════════════════════════════════
    # MARKET ANALYSIS
    # ══════════════════════════════════════════════════════════════

    def market_analysis(self, query, category_id=None):
        """
        Get market statistics for a search query.

        Returns:
            Dict with: count, price_low, price_high, price_median, price_avg,
                       items (sorted by price), newly_listed_count
        """
        items = self.search(query, max_results=50, category_id=category_id, sort="price")

        if not items:
            return {"count": 0, "items": [], "error": "No active listings found"}

        prices = [i["price"] for i in items if i["price"] > 0]
        if not prices:
            return {"count": len(items), "items": items, "error": "No priced listings"}

        prices_sorted = sorted(prices)
        n = len(prices_sorted)
        median = prices_sorted[n // 2] if n % 2 else (prices_sorted[n // 2 - 1] + prices_sorted[n // 2]) / 2

        # Count newly listed (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
        newly_listed = sum(1 for i in items if i.get("listing_date", "") > week_ago)

        return {
            "count": len(items),
            "price_low": min(prices),
            "price_high": max(prices),
            "price_median": round(median, 2),
            "price_avg": round(sum(prices) / len(prices), 2),
            "newly_listed_7d": newly_listed,
            "items": items,
        }

    def get_comps_for_scout(self, query, asking_price=None, max_results=10):
        """
        Get structured comp data formatted for Scout's evaluation pipeline.

        Returns a dict ready to merge into Scout's market_data:
        {
            "ebay_active": [{"title": str, "price": num, "url": str, "image": str}],
            "active_price_low": num,
            "active_price_high": num,
            "active_price_median": num,
            "active_count": num,
            "price_assessment": "underpriced" | "fair" | "overpriced" | "unknown",
            "market_supply": "scarce" | "moderate" | "saturated",
            "visual_matches": [{"title": str, "price": num, "url": str, "image": str}],
        }
        """
        analysis = self.market_analysis(query, category_id=None)

        result = {
            "ebay_active": [],
            "active_price_low": analysis.get("price_low", 0),
            "active_price_high": analysis.get("price_high", 0),
            "active_price_median": analysis.get("price_median", 0),
            "active_count": analysis.get("count", 0),
            "price_assessment": "unknown",
            "market_supply": "unknown",
            "visual_matches": [],
        }

        # Format top comps
        for item in analysis.get("items", [])[:max_results]:
            result["ebay_active"].append({
                "title": item["title"][:80],
                "price": item["price"],
                "url": item.get("url", ""),
                "image": item.get("image", ""),
                "condition": item.get("condition", ""),
            })

        # Assess price if asking price provided
        if asking_price and asking_price > 0 and result["active_price_median"] > 0:
            ratio = asking_price / result["active_price_median"]
            if ratio < 0.4:
                result["price_assessment"] = "underpriced"
            elif ratio < 0.75:
                result["price_assessment"] = "below_market"
            elif ratio < 1.25:
                result["price_assessment"] = "fair"
            else:
                result["price_assessment"] = "overpriced"

        # Assess supply
        count = result["active_count"]
        if count == 0:
            result["market_supply"] = "none_found"
        elif count < 5:
            result["market_supply"] = "scarce"
        elif count < 20:
            result["market_supply"] = "moderate"
        else:
            result["market_supply"] = "saturated"

        return result

    # ══════════════════════════════════════════════════════════════
    # DEAL FINDER — scan for underpriced vintage items
    # ══════════════════════════════════════════════════════════════

    def find_underpriced(self, brand, item_type="", max_price=None, min_savings_pct=50):
        """
        Find potentially underpriced items for a brand.

        Strategy: Search for the brand, get median price, then find listings
        significantly below median. These are potential flips.

        Args:
            brand: Brand name (e.g. "broyhill brasilia")
            item_type: Optional item type (e.g. "credenza")
            max_price: Maximum price to consider
            min_savings_pct: Minimum % below median to flag (default 50%)

        Returns:
            List of deal dicts: {item, savings_pct, median_price, deal_quality}
        """
        query = f"{brand} {item_type}".strip()
        analysis = self.market_analysis(query)

        if analysis.get("count", 0) < 3:
            return []

        median = analysis["price_median"]
        threshold = median * (1 - min_savings_pct / 100)

        deals = []
        for item in analysis["items"]:
            price = item["price"]
            if price <= 0 or price > threshold:
                continue
            if max_price and price > max_price:
                continue

            savings_pct = round((1 - price / median) * 100)
            deal_quality = "HOT" if savings_pct >= 70 else "GOOD" if savings_pct >= 50 else "OK"

            deals.append({
                "item": item,
                "current_price": price,
                "median_price": median,
                "savings_pct": savings_pct,
                "potential_profit": round(median - price, 2),
                "deal_quality": deal_quality,
            })

        deals.sort(key=lambda d: d["savings_pct"], reverse=True)
        return deals

    def scan_vintage_brands(self, brands=None, max_price=500, min_savings_pct=50):
        """
        Scan multiple vintage brands for underpriced deals.

        Args:
            brands: List of brand search terms. Defaults to top MCM brands.
            max_price: Maximum price to consider
            min_savings_pct: Minimum % below median

        Returns:
            List of all deals found, sorted by potential profit
        """
        if brands is None:
            brands = [
                "broyhill brasilia", "heywood wakefield", "lane acclaim",
                "drexel declaration", "kent coffey", "paul mccobb",
                "danish teak credenza", "danish teak desk",
                "mid century walnut dresser", "mid century walnut credenza",
                "eames shell chair", "knoll tulip",
                "vintage herman miller", "vintage chanel jacket",
                "vintage gucci bag", "vintage levis 501",
            ]

        all_deals = []
        for brand in brands:
            try:
                deals = self.find_underpriced(brand, max_price=max_price,
                                              min_savings_pct=min_savings_pct)
                all_deals.extend(deals)
                time.sleep(0.5)  # Rate limiting courtesy
            except Exception as e:
                print(f"  Error scanning '{brand}': {e}")

        all_deals.sort(key=lambda d: d["potential_profit"], reverse=True)
        return all_deals


# ══════════════════════════════════════════════════════════════════
# FLASK API SERVER (optional — serves structured eBay data to web app)
# ══════════════════════════════════════════════════════════════════

def create_api_server():
    """
    Create a lightweight Flask server that the Scout web app can call
    for structured eBay data. Runs alongside the main Scout app.

    Endpoints:
        GET  /api/ebay/search?q=broyhill+brasilia&max=10
        POST /api/ebay/image-search  (body: {"image": "base64..."})
        GET  /api/ebay/comps?q=broyhill+brasilia&asking=150
        GET  /api/ebay/deals?brands=broyhill+brasilia,lane+acclaim
    """
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
    except ImportError:
        print("Install Flask: pip install flask flask-cors")
        return None

    app = Flask(__name__)
    CORS(app)
    client = EbayClient()

    @app.route("/api/ebay/search")
    def ebay_search():
        q = request.args.get("q", "")
        max_results = int(request.args.get("max", 10))
        category = request.args.get("category")
        if not q:
            return jsonify({"error": "q parameter required"}), 400
        results = client.search(q, max_results=max_results, category_id=category)
        return jsonify({"results": results, "count": len(results)})

    @app.route("/api/ebay/image-search", methods=["POST"])
    def ebay_image_search():
        data = request.get_json()
        image = data.get("image", "")
        if not image:
            return jsonify({"error": "image field required"}), 400
        results = client.search_by_image(image, max_results=int(data.get("max", 10)))
        return jsonify({"results": results, "count": len(results)})

    @app.route("/api/ebay/comps")
    def ebay_comps():
        q = request.args.get("q", "")
        asking = request.args.get("asking", type=float)
        if not q:
            return jsonify({"error": "q parameter required"}), 400
        comps = client.get_comps_for_scout(q, asking_price=asking)
        return jsonify(comps)

    @app.route("/api/ebay/deals")
    def ebay_deals():
        brands_str = request.args.get("brands", "")
        brands = [b.strip() for b in brands_str.split(",") if b.strip()] or None
        max_price = request.args.get("max_price", 500, type=float)
        deals = client.scan_vintage_brands(brands=brands, max_price=max_price)
        return jsonify({"deals": deals, "count": len(deals)})

    @app.route("/api/ebay/health")
    def health():
        try:
            client._get_token()
            return jsonify({"status": "ok", "authenticated": True})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return app


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

def main():
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nCOMMANDS:")
        print("  python3 ebay_api.py search 'broyhill brasilia credenza'")
        print("  python3 ebay_api.py market 'herman miller eames lounge'")
        print("  python3 ebay_api.py deals")
        print("  python3 ebay_api.py deals 'broyhill brasilia,lane acclaim'")
        print("  python3 ebay_api.py server              # Start API server on :5050")
        print("  python3 ebay_api.py test                 # Test API connection")
        return

    cmd = sys.argv[1].lower()

    if cmd == "test":
        print("Testing eBay API connection...")
        try:
            client = EbayClient()
            token = client._get_token()
            print(f"✅ OAuth token obtained ({len(token)} chars)")
            results = client.search("mid century modern furniture", max_results=3)
            print(f"✅ Search returned {len(results)} results")
            if results:
                for r in results[:3]:
                    print(f"   ${r['price']:>8.2f}  {r['title'][:60]}")
            print("\n✅ eBay API integration working!")
        except Exception as e:
            print(f"❌ Error: {e}")

    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        client = EbayClient()
        results = client.search(query, max_results=15, sort="price")
        print(f"\n{'=' * 70}")
        print(f"  eBay Active Listings: '{query}' ({len(results)} results)")
        print(f"{'=' * 70}")
        for r in results:
            print(f"  ${r['price']:>8.2f}  {r['condition'][:12]:12s}  {r['title'][:50]}")
        if results:
            prices = [r["price"] for r in results if r["price"] > 0]
            if prices:
                print(f"\n  Low: ${min(prices):.2f}  |  High: ${max(prices):.2f}  |  "
                      f"Avg: ${sum(prices)/len(prices):.2f}")

    elif cmd == "market":
        query = " ".join(sys.argv[2:])
        client = EbayClient()
        analysis = client.market_analysis(query)
        print(f"\n{'=' * 70}")
        print(f"  Market Analysis: '{query}'")
        print(f"{'=' * 70}")
        print(f"  Active listings:   {analysis.get('count', 0)}")
        print(f"  Price range:       ${analysis.get('price_low', 0):.2f} – ${analysis.get('price_high', 0):.2f}")
        print(f"  Median price:      ${analysis.get('price_median', 0):.2f}")
        print(f"  Average price:     ${analysis.get('price_avg', 0):.2f}")
        print(f"  New (7 days):      {analysis.get('newly_listed_7d', 0)}")
        supply = "scarce" if analysis.get("count", 0) < 5 else "moderate" if analysis.get("count", 0) < 20 else "saturated"
        print(f"  Supply:            {supply}")

    elif cmd == "deals":
        brands = None
        if len(sys.argv) > 2:
            brands = [b.strip() for b in " ".join(sys.argv[2:]).split(",")]
        client = EbayClient()
        print(f"\n{'=' * 70}")
        print(f"  Scanning for underpriced vintage deals...")
        print(f"{'=' * 70}\n")
        deals = client.scan_vintage_brands(brands=brands)
        if deals:
            for d in deals[:20]:
                q = d["deal_quality"]
                ic = "🔥" if q == "HOT" else "✓" if q == "GOOD" else "·"
                print(f"  {ic} {q:4s}  ${d['current_price']:>7.2f}  (median ${d['median_price']:.2f}, "
                      f"-{d['savings_pct']}%, +${d['potential_profit']:.2f})")
                print(f"         {d['item']['title'][:65]}")
                print(f"         {d['item'].get('url', '')[:70]}")
                print()
            print(f"  Found {len(deals)} deals across {len(brands or [])} brands")
        else:
            print("  No deals found matching criteria.")

    elif cmd == "server":
        app = create_api_server()
        if app:
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5050
            print(f"\n  eBay API server starting on http://localhost:{port}")
            print(f"  Endpoints:")
            print(f"    GET  /api/ebay/search?q=broyhill+brasilia")
            print(f"    POST /api/ebay/image-search")
            print(f"    GET  /api/ebay/comps?q=knoll+tulip&asking=150")
            print(f"    GET  /api/ebay/deals")
            print(f"    GET  /api/ebay/health\n")
            app.run(host="0.0.0.0", port=port, debug=True)

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: test, search, market, deals, server")


if __name__ == "__main__":
    main()
