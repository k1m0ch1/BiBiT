"""
Yogya Online Crawler - Improved version
Uses cloudscraper for better reliability and rate limiting
"""

import json
import logging
import random
import re
import time
from datetime import datetime

import cloudscraper
import pytz
import shortuuid
from bs4 import BeautifulSoup
from tqdm import tqdm

from db import DBSTATE
from util import cleanUpCurrency

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

db = DBSTATE
CATEGORIES = {}


def _rate_limit():
    """Simple rate limiting to avoid overwhelming the server"""
    time.sleep(random.uniform(1.0, 2.5))


def scrap_page(url, page_num, item_limit, counter):
    """
    Scrape a single page from a category

    Args:
        url: Category URL
        page_num: Page number to scrape
        item_limit: Number of items per page
        counter: Dictionary tracking new items/prices/discounts

    Returns:
        List of product data, or empty list on error
    """
    target_url = f"{url}?p={page_num}&product_list_limit={item_limit}"
    logging.info(f"Scraping {url} page {page_num}")

    # Create cloudscraper session
    scraper = cloudscraper.create_scraper()
    _rate_limit()

    try:
        response = scraper.get(target_url, timeout=30)

        # Handle 503 by reducing item limit
        if response.status_code == 503:
            new_limit = int(item_limit / 2)
            CATEGORIES[url]['item_limit'] = new_limit
            logging.warning(
                f"503 error, reducing item_limit to {new_limit}"
            )
            return []

        response.raise_for_status()

    except Exception as e:
        logging.error(f"Error fetching {target_url}: {str(e)}")
        return []

    return _parse_page(response.text, counter)


def _parse_page(html_content, counter):
    """Parse HTML content and extract product data"""
    parser = BeautifulSoup(html_content, 'html.parser')

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

    # Extract promotions
    promotions = _extract_promotions(parser)

    # Extract product data from JavaScript
    products = _extract_product_data(parser)

    # Combine all data
    return _process_products(
        products, product_links, product_images, promotions, counter
    )


def _extract_promotions(parser):
    """Extract promotion data from price boxes"""
    promotions = []

    for item in parser.find_all("div", {"class": "price-box price-final_price"}):
        promo_type = ""
        description = ""

        # Check for promo label
        promo_labels = item.find_all("div", {"class": "label-promo custom"})
        if len(promo_labels) > 0:
            promo_type = "promo"
            description = (
                promo_labels[0].get_text()
                .replace(" ", "")
                .replace("\r\n", "")
            )

        # Check for discount label
        discount_labels = item.find_all(
            "div", {"class": "product product-promotion"}
        )
        if len(discount_labels) > 0:
            promo_type = "discount"
            description = (
                discount_labels[0].get_text()
                .replace(" ", "")
                .replace("\r\n", "")
            )

        # Extract original price
        price_spans = item.find_all("span", {"class": "price"})
        original_price = price_spans[0].get_text() if price_spans else ""

        promotions.append({
            "type": promo_type,
            "description": description,
            "original_price": original_price
        })

    # Pad promotions list to ensure we have enough entries
    # (Yogya pages typically show up to 80 items)
    while len(promotions) < 80:
        promotions.append({
            "type": "",
            "description": "",
            "original_price": ""
        })

    return promotions


def _extract_product_data(parser):
    """Extract product data from JavaScript variable"""
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
        logging.warning("Could not find product data in JavaScript")
        return []

    try:
        data_raw = json.loads(found)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing product JSON: {str(e)}")
        return []

    # Extract items and deduplicate
    products = []
    seen_ids = []

    for grouped_item in data_raw:
        data_ecommerce = grouped_item.get('ecommerce', {})
        for item in data_ecommerce.get('items', []):
            item_id = item.get('item_id')
            if item_id and item_id not in seen_ids:
                products.append(item)
                seen_ids.append(item_id)

    return products


def _process_products(products, links, images, promotions, counter):
    """Process products and save to database"""
    data_products = []

    for index, product in enumerate(products):
        # Skip if we don't have corresponding data
        if index >= len(links) or index >= len(images):
            continue

        # Add additional data to product
        product['link'] = links[index]
        product['image'] = images[index]
        product['promotion'] = (
            promotions[index] if index < len(promotions)
            else {"type": "", "description": "", "original_price": ""}
        )

        # Save to database
        _save_product_to_db(product, counter)
        data_products.append(product)

    return data_products


def _save_product_to_db(product, counter):
    """Save product, price, and discount to database"""
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_today = now.strftime("%Y-%m-%d")
    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

    item_id = product.get('item_id', '')
    item_name = product.get('item_name', '')
    item_list_name = product.get('item_list_name', '')
    price = cleanUpCurrency(product.get('price', '0'))
    original_price = cleanUpCurrency(
        product.get('promotion', {}).get('original_price', '0')
    )

    # Check if item exists
    req_query = {
        'script': "SELECT id FROM items WHERE sku=? OR name=?",
        'values': (item_id, item_name)
    }
    check_item = db.execute(**req_query)

    db_item_id = shortuuid.uuid()

    # Insert new item if it doesn't exist
    if len(check_item) == 0:
        db["items"].insert(
            db_item_id,
            item_id,
            item_name,
            item_list_name,
            product['image'],
            product['link'],
            'yogyaonline',
            datetime_today
        )
        counter['newItems'] += 1
    else:
        db_item_id = check_item[0][0]

    # Check if today's price exists
    req_query = {
        'script': (
            "SELECT id FROM prices "
            "WHERE items_id=? AND created_at LIKE ? AND price=?"
        ),
        'values': (db_item_id, f'{date_today}%', price)
    }
    check_price = db.execute(**req_query)

    # Insert new price if it doesn't exist
    if len(check_price) == 0:
        db["prices"].insert(
            shortuuid.uuid(),
            db_item_id,
            price,
            "",
            datetime_today
        )
        counter['newPrices'] += 1

    # Handle discounts (if there's a promotion with original price)
    if original_price > 0 and price < original_price:
        # Calculate discount percentage
        discount_percent = int(((original_price - price) / original_price) * 100)

        req_query = {
            'script': (
                "SELECT id FROM discounts "
                "WHERE items_id=? AND created_at LIKE ? "
                "AND discount_price=? AND original_price=?"
            ),
            'values': (
                db_item_id, f'{date_today}%', price, original_price
            )
        }
        check_discount = db.execute(**req_query)

        if len(check_discount) == 0:
            db["discounts"].insert(
                shortuuid.uuid(),
                db_item_id,
                price,
                original_price,
                discount_percent,
                product.get('promotion', {}).get('description', ''),
                datetime_today
            )
            counter['newDiscounts'] += 1


def getCategories():
    """
    Main entry point - scrape all categories from Yogya Online
    """
    target_url = "https://www.yogyaonline.co.id/"

    logging.info("Fetching categories from Yogya Online...")

    # Create cloudscraper session
    scraper = cloudscraper.create_scraper()
    _rate_limit()

    try:
        response = scraper.get(target_url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        error_msg = f"Error fetching categories: {str(e)}"
        logging.error(error_msg)
        return error_msg

    parser = BeautifulSoup(response.text, 'html.parser')
    category_elements = parser.find_all("li", {"id": re.compile('vesitem-*')})

    categories = []
    for cat in category_elements:
        link = cat.find('a')
        if not link:
            continue

        href = link.get('href')

        # Skip invalid links
        if not href or href == "#":
            continue
        if "blog-yogya-online" in href:
            continue

        if href not in categories:
            categories.append(href)

    logging.info(f"Found {len(categories)} categories")

    # Initialize counter
    counter = {
        "newItems": 0,
        "newPrices": 0,
        "newDiscounts": 0
    }

    compiled_data = []

    # Scrape each category
    for cat_index, category in enumerate(
        tqdm(categories, desc="Scraping categories")
    ):
        logging.info(
            f"Processing category {cat_index + 1}/{len(categories)}: {category}"
        )

        # Initialize category config
        CATEGORIES[category] = {"item_limit": 640}

        # Scrape first page
        page_num = 1
        prev_data = []
        curr_data = scrap_page(category, page_num, 640, counter)
        compiled_data.extend(curr_data)

        # Continue scraping pages until we get no new data
        page_num = 2
        while len(curr_data) > 0 and curr_data != prev_data:
            prev_data = curr_data
            item_limit = CATEGORIES[category]['item_limit']
            curr_data = scrap_page(category, page_num, item_limit, counter)

            if curr_data:
                compiled_data.extend(curr_data)
                page_num += 1

    # Log summary
    summary = (
        f"=== Finish scrap {len(compiled_data)} items by added "
        f"{counter['newItems']} items, {counter['newPrices']} prices, "
        f"{counter['newDiscounts']} discounts"
    )
    logging.info(summary)

    if (counter['newItems'] == 0 and
            counter['newPrices'] == 0 and
            counter['newDiscounts'] == 0):
        logging.info("=== I guess nothing different today")

    return summary
