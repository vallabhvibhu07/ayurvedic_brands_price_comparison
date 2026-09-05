"""
Devrishi Ayurveda Product Scraper
-----------------------------------
Scrapes product name, price, category, and rating from Devrishi Ayurveda's
WooCommerce shop listing pages (paginated).

Respects robots.txt: only touches /shop/ pages
(not wp-admin, add-to-cart query params, wc-logs).

Run: python devrishi_scraper.py
Output: devrishi_products.csv
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import random
from datetime import datetime

BASE_URL = "https://devrishiayurveda.com"
NUM_PAGES = 8  # ~24 products/page -> up to ~190 products

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://devrishiayurveda.com/",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_DELAY_MIN = 4
REQUEST_DELAY_MAX = 7

session = requests.Session()
session.headers.update(HEADERS)


def clean_price(text):
    if not text:
        return None
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    return float(match.group()) if match else None


def extract_category(class_list):
    """Pull the first meaningful product_cat-* class as the category."""
    cats = [c.replace("product_cat-", "") for c in class_list if c.startswith("product_cat-")]
    # Prefer a more specific/readable category over generic ones if possible
    generic = {"wellness", "men-women", "patent-product"}
    specific = [c for c in cats if c not in generic]
    chosen = specific[0] if specific else (cats[0] if cats else None)
    return chosen.replace("-", " ").title() if chosen else None


def scrape_page(page_num):
    url = f"{BASE_URL}/shop/page/{page_num}/" if page_num > 1 else f"{BASE_URL}/shop/"
    print(f"Scraping page {page_num}: {url}")

    resp = session.get(url, timeout=15)
    if resp.status_code == 403:
        print("  Got 403, cooling down 20s and retrying once...")
        time.sleep(20)
        resp = session.get(url, timeout=15)

    if resp.status_code != 200:
        print(f"  Failed ({resp.status_code}), stopping pagination.")
        return [], False

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div.product-grid-item.product")
    print(f"  Found {len(cards)} products")

    if not cards:
        return [], False  # no more products -> stop pagination

    products = []
    for card in cards:
        class_list = card.get("class", [])
        category = extract_category(class_list)

        title_tag = card.select_one("h3.wd-entities-title a")
        name = title_tag.get_text(strip=True) if title_tag else None
        product_url = title_tag["href"] if title_tag else None

        price_tag = card.select_one("span.price span.amount")
        price = clean_price(price_tag.get_text(strip=True)) if price_tag else None

        rating_tag = card.select_one("div.star-rating strong.rating")
        rating = float(rating_tag.get_text(strip=True)) if rating_tag else None

        products.append({
            "brand": "Devrishi Ayurveda",
            "category": category,
            "product_name": name,
            "url": product_url,
            "price": price,
            "rating": rating,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return products, True


def main():
    all_products = []
    for page_num in range(1, NUM_PAGES + 1):
        products, has_more = scrape_page(page_num)
        all_products.extend(products)
        if not has_more:
            break
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    # Deduplicate by URL
    seen = set()
    deduped = []
    for p in all_products:
        key = p["url"] or p["product_name"]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    print(f"\nTotal unique products scraped: {len(deduped)}")

    if deduped:
        with open("devrishi_products.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=deduped[0].keys())
            writer.writeheader()
            writer.writerows(deduped)
        print("Saved to devrishi_products.csv")
    else:
        print("No products scraped — check selectors.")


if __name__ == "__main__":
    main()
