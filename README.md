# Ayurvedic Wellness — Competitive Pricing Intelligence

A web scraping + data analysis project that builds a pricing intelligence pipeline across three Indian Ayurvedic/wellness D2C brands, spanning premium, mid-tier, and value market positions.

**[🔗 View live dashboard](https://vallabhvibhu07.github.io/ayurvedic_brands_price_comparison/ayurveda_pricing_dashboard.html)**

## Why this project

Competitive pricing intelligence is a real function inside consumer brand strategy — understanding how competitors price, discount, and structure their catalog informs positioning, promotions, and assortment decisions. This project simulates that workflow end-to-end: scrape → clean → merge → analyze → visualize, using live product data rather than a static Kaggle dataset.

The category (Ayurvedic/wellness D2C) connects to prior GTM strategy work I've done for a wellness brand, so the analysis is framed around a question a real brand team would ask: *how are we positioned against comparable competitors, and where are the gaps?*

## Brands scraped

| Brand | Market position | Platform | Products |
|---|---|---|---|
| [Kama Ayurveda](https://www.kamaayurveda.in) | Premium | Next.js (server-rendered) | 89 |
| [Vedix](https://www.vedix.com) | Mid-tier / personalized | Shopify | 38 |
| [Devrishi Ayurveda](https://devrishiayurveda.com) | Value / mass wellness | WooCommerce | 73 |
| **Total** | | | **200** |

## What's in this repo

```
scrapers/
  kama_scraper.py        # Kama Ayurveda — category pages, requests + BeautifulSoup
  vedix_scraper.py        # Vedix — Shopify collections, session + browser headers (bot-detection workaround)
  devrishi_scraper.py     # Devrishi Ayurveda — WooCommerce shop pagination

data/
  kama_ayurveda_products.csv
  vedix_products.csv
  devrishi_products.csv
  unified_products.csv    # merged, common schema across all three brands

dashboard/
  ayurveda_pricing_dashboard.html   # self-contained Chart.js dashboard, no build step
```

## Methodology

- **Tooling:** Python (`requests`, `BeautifulSoup`), pandas-free (stdlib `csv`) for the merge, Chart.js for visualization.
- **Respectful scraping:** every scraper checks `robots.txt` before targeting a URL pattern, uses a persistent session with realistic browser headers, and adds randomized delays (3–9s) between requests. No login-gated or personal data was accessed.
- **Bot-detection handling:** Vedix's Shopify storefront initially returned `403` on repeated requests with a bare `requests.get()` call. Switching to a `requests.Session()` with full browser-style headers (`Accept`, `Accept-Language`, `Referer`, `Sec-Fetch-*`) and longer randomized delays resolved this — a real debugging step documented in the commit history, not glossed over.
- **Data cleaning:** deduplicated by product URL within each brand; dropped 3 off-topic rows that leaked into Vedix's "Hair Shampoo" collection page (it returned some skincare cross-sell items).

## Known data limitations

Each brand's listing pages expose different fields, so the merged dataset is intentionally imperfect rather than false-complete:

- **MRP / discount %** — only available for Kama Ayurveda; Vedix and Devrishi don't show strikethrough pricing on listing pages.
- **Review count** — only available for Kama Ayurveda.
- **Star rating** — available for Kama (partial) and Vedix (near-complete), largely absent for Devrishi.
- **Concern/scalp tags** — Vedix only.

This asymmetry is itself a finding: it reflects real differences in how these brands merchandise trust signals (reviews, ratings, discounts) on-site.

## Key findings

- **Price range:** Kama Ayurveda spans ₹350–₹9,495 (a mix of everyday essentials and luxury gift sets); Vedix and Devrishi cluster in much narrower, more standardized bands — consistent with subscription/personalized and mass-value pricing models respectively.
- **Review coverage gap:** only ~25% of the combined catalog shows a visible rating. Devrishi, the value-tier brand, has almost none — a potential trust-signal gap worth flagging in a real competitive review.
- **Catalog composition:** Kama concentrates in skincare and bath & body; Devrishi's catalog is dominated by digestive-care and general wellness supplements rather than beauty — the three brands compete on price within the "Ayurvedic" category label but serve meaningfully different product missions.

## Reproducing this

```bash
pip install requests beautifulsoup4
python scrapers/kama_scraper.py
python scrapers/vedix_scraper.py
python scrapers/devrishi_scraper.py
```

Each script writes its own CSV to the working directory. Open `dashboard/ayurveda_pricing_dashboard.html` directly in a browser — no server needed, data is embedded.

## About

Built by Vallabh Vibhu, MBA in Business Analytics @ IIM Ranchi. Part of a data science portfolio connecting business strategy with hands-on technical execution.

[LinkedIn](https://www.linkedin.com/in/vallabh-vibhu56/) · [GitHub](https://github.com/vallabhvibhu07)
