"""
Kama Ayurveda Product Scraper
------------------------------
Scrapes product name, price, MRP/discount, rating, review count, and category
from Kama Ayurveda's category listing pages.

Respects robots.txt: only touches category/product listing pages
(not /cart/, /my-account/, /search/, or query-string URLs).

Run: python kama_scraper.py
Output: kama_ayurveda_products.csv
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from datetime import datetime

BASE_URL = "https://www.kamaayurveda.in"

# Category pages to scrape (each is server-rendered with the first batch of products)
CATEGORIES = {
    "Skincare": "/skin-care.html",
    "Haircare": "/hair-care.html",
    "Kumkumadi Collection": "/kumkumadi-collection.html",
    "Bringaras Collection": "/bringaras-collection.html",
    "Bath & Body": "/bath-body.html",
    "Bestsellers": "/best-seller.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

REQUEST_DELAY = 3  # seconds between requests — be a polite scraper


def clean_price(text):
    """Extract a numeric price from strings like '₹1895.00'."""
    if not text:
        return None
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    return float(match.group()) if match else None


def scrape_category(category_name, path):
    url = BASE_URL + path
    print(f"Scraping {category_name}: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"  Failed ({resp.status_code}), skipping.")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.list-item_categoryProductItem__6cMzw")
    print(f"  Found {len(cards)} products")

    products = []
    for card in cards:
        # Name + URL
        name_tag = card.select_one("h3")
        name = name_tag.get_text(strip=True) if name_tag else None

        link_tag = card.select_one("a[href]")
        product_url = BASE_URL + link_tag["href"] if link_tag and link_tag.get("href", "").startswith("/") else None

        # Price block
        price_block = card.select_one("div.stock_bag_bax h4")
        current_price = None
        mrp = None
        if price_block:
            # The abbr tag (if present) holds the original MRP
            abbr = price_block.select_one("abbr")
            if abbr:
                mrp = clean_price(abbr.get_text(strip=True))
                # Remove abbr text to isolate the current price
                full_text = price_block.get_text(strip=True)
                current_price = clean_price(full_text.replace(abbr.get_text(strip=True), ""))
            else:
                current_price = clean_price(price_block.get_text(strip=True))
                mrp = current_price  # no discount

        # Rating + review count
        rating = None
        review_count = None
        rating_block = card.select_one("div.list-item_category_row__ziqwr")
        if rating_block:
            rating_text = rating_block.get_text(strip=True)
            # e.g. "5.0 (44)"
            rating_match = re.match(r"([\d.]+)", rating_text)
            count_match = re.search(r"\((\d+)\)", rating_text)
            rating = float(rating_match.group(1)) if rating_match else None
            review_count = int(count_match.group(1)) if count_match else None

        # Badge / tag (New, Bestseller, etc.)
        badge_tag = card.select_one("div.category_star h6")
        badge = badge_tag.get_text(strip=True) if badge_tag else None

        discount_pct = None
        if mrp and current_price and mrp > current_price:
            discount_pct = round((mrp - current_price) / mrp * 100, 1)

        products.append({
            "brand": "Kama Ayurveda",
            "category": category_name,
            "product_name": name,
            "url": product_url,
            "price": current_price,
            "mrp": mrp,
            "discount_pct": discount_pct,
            "rating": rating,
            "review_count": review_count,
            "badge": badge,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return products


def main():
    all_products = []
    for name, path in CATEGORIES.items():
        all_products.extend(scrape_category(name, path))
        time.sleep(REQUEST_DELAY)

    # Deduplicate by product URL (some items appear in multiple categories)
    seen = set()
    deduped = []
    for p in all_products:
        key = p["url"] or p["product_name"]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    print(f"\nTotal unique products scraped: {len(deduped)}")

    with open("kama_ayurveda_products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=deduped[0].keys())
        writer.writeheader()
        writer.writerows(deduped)

    print("Saved to kama_ayurveda_products.csv")


if __name__ == "__main__":
    main()
