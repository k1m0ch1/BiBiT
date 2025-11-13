"""
Test script for Yogya Online scraper
Scrapes one category and shows 10 sample items
"""

import sys
import json
sys.path.insert(0, 'src')

from crawler.yogyaonline import scrap_page, getCategories
import cloudscraper
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


def test_get_one_category():
    """Get first category from Yogya Online"""
    target_url = "https://www.yogyaonline.co.id/"

    logging.info("Fetching categories...")
    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(target_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return None

    parser = BeautifulSoup(response.text, 'html.parser')
    category_elements = parser.find_all("li", {"id": re.compile('vesitem-*')})

    categories = []
    for cat in category_elements:
        link = cat.find('a')
        if not link:
            continue

        href = link.get('href')
        if not href or href == "#":
            continue
        if "blog-yogya-online" in href:
            continue

        if href not in categories:
            categories.append(href)

    logging.info(f"Found {len(categories)} categories")

    if categories:
        logging.info(f"First category: {categories[0]}")
        return categories[0]

    return None


def test_scrape_category_sample(category_url):
    """Scrape first page of a category (without saving to DB)"""
    logging.info(f"Testing scrape of: {category_url}")

    target_url = f"{category_url}?p=1&product_list_limit=80"
    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(target_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return []

    # Parse the page
    parser = BeautifulSoup(response.text, 'html.parser')

    # Extract product links
    list_items = parser.find_all(
        "ol", {"class": "products list items product-items"}
    )
    product_links = []
    if len(list_items) > 0:
        links = list_items[0].find_all(
            "a", {"class": "product-item-link"}, href=True
        )
        product_links = [item['href'] for item in links]

    # Extract product images
    product_images = [
        item.get('data-original')
        for item in parser.find_all(
            "img", {"class": "product-image-photo lazy"}
        )
    ]

    # Extract product data from JavaScript
    pattern = re.compile(r'var dl4Objects = (.*);')
    found = ""

    for script in parser.find_all("script", {"src": False}):
        if script and script.string:
            match = pattern.search(script.string)
            if match is not None:
                found = match.group().replace("var dl4Objects =", "")
                found = found.replace(";", "")
                break

    if not found:
        logging.error("Could not find product data")
        return []

    try:
        data_raw = json.loads(found)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON: {str(e)}")
        return []

    # Extract items
    products = []
    seen_ids = []

    for grouped_item in data_raw:
        data_ecommerce = grouped_item.get('ecommerce', {})
        for item in data_ecommerce.get('items', []):
            item_id = item.get('item_id')
            if item_id and item_id not in seen_ids:
                # Add link and image
                index = len(products)
                if index < len(product_links):
                    item['link'] = product_links[index]
                if index < len(product_images):
                    item['image'] = product_images[index]

                products.append(item)
                seen_ids.append(item_id)

    logging.info(f"Found {len(products)} products")
    return products


if __name__ == "__main__":
    print("=" * 80)
    print("YOGYA ONLINE SCRAPER TEST")
    print("=" * 80)

    # Get first category
    category = test_get_one_category()

    if not category:
        print("❌ Could not get categories")
        sys.exit(1)

    print(f"\n✅ Testing category: {category}")
    print("-" * 80)

    # Scrape sample
    products = test_scrape_category_sample(category)

    if not products:
        print("❌ Could not scrape products")
        sys.exit(1)

    # Show first 10 items
    print(f"\n✅ Found {len(products)} products total")
    print("\n📦 Showing first 10 items:")
    print("=" * 80)

    for i, product in enumerate(products[:10]):
        print(f"\n[{i+1}] {product.get('item_name', 'N/A')}")
        print(f"    SKU:      {product.get('item_id', 'N/A')}")
        print(f"    Price:    {product.get('price', 'N/A')}")
        print(f"    Category: {product.get('item_list_name', 'N/A')}")
        print(f"    Link:     {product.get('link', 'N/A')[:60]}...")
        if product.get('image'):
            print(f"    Image:    {product.get('image')[:60]}...")

    print("\n" + "=" * 80)
    print(f"✅ Test completed! Scraped {len(products)} products from first page")
    print("=" * 80)
