"""
Vedix Product Scraper
----------------------
Scrapes product name, price, rating, size, product type, and concern tags
from Vedix's collection listing pages (Shopify store).

Respects robots.txt: only touches /collections/ pages
(not /cart, /checkout, /account, /search).

Run: python vedix_scraper.py
Output: vedix_products.csv
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import random
from datetime import datetime

BASE_URL = "https://www.vedix.com"

# Collection pages to scrape
COLLECTIONS = {
    "Hair Shampoo": "/collections/hair-shampoos",
    "Hair Oil": "/collections/hair-oils",
    "Hair Serum": "/collections/hair-serums",
    "Hair Conditioner": "/collections/hair-conditioners",
    "Hair Mask": "/collections/hair-packs",
    "Skin Cleanser": "/collections/skin-cleansers",
    "Skin Moisturizer": "/collections/skin-moisturizers",
    "Skin Serum": "/collections/skin-actives",
    "Sunscreen": "/collections/sunscreen",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.vedix.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_DELAY_MIN = 5  # seconds between requests
REQUEST_DELAY_MAX = 9

session = requests.Session()
session.headers.update(HEADERS)


def clean_price(text):
    if not text:
        return None
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    return float(match.group()) if match else None


def scrape_collection(collection_name, path):
    url = BASE_URL + path
    print(f"Scraping {collection_name}: {url}")

    resp = session.get(url, timeout=15)

    if resp.status_code == 403:
        # One retry after a longer cool-down — bot-detection often clears after a pause
        print("  Got 403, cooling down 20s and retrying once...")
        time.sleep(20)
        resp = session.get(url, timeout=15)

    if resp.status_code != 200:
        print(f"  Failed ({resp.status_code}), skipping.")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div[data-product-type]")
    print(f"  Found {len(cards)} products")

    products = []
    for card in cards:
        product_type = card.get("data-product-type")
        variant_id = card.get("data-variant-id")

        link_tag = card.select_one("a[href^='/products/']")
        product_url = BASE_URL + link_tag["href"] if link_tag else None

        title_tag = card.select_one("span.product-title-clamp")
        name = title_tag.get_text(strip=True) if title_tag else None

        subtitle_tag = card.select_one("p.text-\\[\\#81552F\\]")
        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else None

        price_tag = card.select_one("span.selling_price")
        price = clean_price(price_tag.get_text(strip=True)) if price_tag else None

        # Rating: the small green semibold number near the star icon
        rating = None
        rating_block = card.select_one("div.text-\\[\\#2DB433\\]")
        if rating_block:
            rating_text = rating_block.get_text(strip=True)
            rating_match = re.search(r"[\d.]+", rating_text)
            rating = float(rating_match.group()) if rating_match else None

        # Size (e.g. "100 ml")
        size_tag = card.select_one("span.opacity-50")
        size = size_tag.get_text(strip=True).replace("\n", " ") if size_tag else None
        size = re.sub(r"\s+", " ", size) if size else None

        # Concern/scalp tags (can be multiple)
        tag_elements = card.select("span.truncate.font-medium")
        tags = [t.get_text(strip=True) for t in tag_elements if t.get_text(strip=True)]

        products.append({
            "brand": "Vedix",
            "product_type": product_type,
            "collection": collection_name,
            "product_name": name,
            "subtitle": subtitle,
            "url": product_url,
            "price": price,
            "rating": rating,
            "size": size,
            "tags": " | ".join(tags),
            "variant_id": variant_id,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return products


def main():
    all_products = []
    for name, path in COLLECTIONS.items():
        all_products.extend(scrape_collection(name, path))
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    # Deduplicate by product URL
    seen = set()
    deduped = []
    for p in all_products:
        key = p["url"] or p["product_name"]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    print(f"\nTotal unique products scraped: {len(deduped)}")

    if deduped:
        with open("vedix_products.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=deduped[0].keys())
            writer.writeheader()
            writer.writerows(deduped)
        print("Saved to vedix_products.csv")
    else:
        print("No products scraped — check selectors.")


if __name__ == "__main__":
    main()
