"""
Yogya Online Crawler - Updated for new website structure
Uses cloudscraper for bot detection bypass and HTML parsing
Website changed to supermarket.yogyaonline.co.id subdomain
"""

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
    """Parse HTML content and extract product data using new structure"""
    parser = BeautifulSoup(html_content, 'html.parser')

    # Find all product items using new structure
    product_divs = parser.find_all("div", class_="product-item box-shadow-light")

    logging.info(f"Found {len(product_divs)} product items")

    products = []

    for div in product_divs:
        product = _extract_product_from_html(div)
        if product:
            # Save to database
            _save_product_to_db(product, counter)
            products.append(product)

    return products


def _extract_product_from_html(div):
    """Extract product data from HTML div element"""
    try:
        # Extract product name link
        name_link = div.find("a", class_="product-name")
        if not name_link:
            return None

        # Extract SKU and name from onclick attribute
        onclick = name_link.get('onclick', '')
        match = re.search(
            r"viewProduct\('([^']+)',\s*null,\s*'([^']*)',\s*'([^']*)'\)",
            onclick
        )

        if not match:
            return None

        sku = match.group(1)
        brand = match.group(2)
        name = match.group(3)

        # Extract link
        link = name_link.get('href', '')

        # Extract image
        img_tag = div.find("img", class_="product-image")
        image = img_tag.get('src', '') if img_tag else ''

        # Extract prices
        price_divs = div.find_all("div", class_="product-price")

        original_price_raw = None
        final_price_raw = None

        # If there are 2 prices, first is original, second is discounted
        # If there's 1 price, it's the final price
        if len(price_divs) >= 2:
            original_price_raw = price_divs[0].get_text(strip=True)
            final_price_raw = price_divs[1].get_text(strip=True)
        elif len(price_divs) == 1:
            final_price_raw = price_divs[0].get_text(strip=True)

        # Clean prices
        original_price = cleanUpCurrency(original_price_raw or '0')
        final_price = cleanUpCurrency(final_price_raw or '0')

        # Extract discount percentage
        discount_badge = div.find("span", class_="badge bg-danger")
        discount_pct = None
        discount_desc = ""

        if discount_badge:
            discount_text = discount_badge.get_text(strip=True)
            pct_match = re.search(r'-(\d+)%', discount_text)
            if pct_match:
                discount_pct = int(pct_match.group(1))
            discount_desc = discount_text

        # Calculate discount percentage if not found
        if (not discount_pct and original_price and final_price and
                original_price > final_price):
            discount_pct = int(
                ((original_price - final_price) / original_price) * 100
            )

        return {
            'item_id': sku,
            'item_name': name,
            'item_list_name': brand,
            'price': final_price or original_price,
            'original_price': original_price,
            'discount_price': final_price if original_price else None,
            'discount_percentage': discount_pct,
            'discount_description': discount_desc,
            'link': link,
            'image': image,
        }

    except Exception as e:
        logging.error(f"Error extracting product: {str(e)}")
        return None


def _save_product_to_db(product, counter):
    """Save product, price, and discount to database"""
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_today = now.strftime("%Y-%m-%d")
    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

    item_id = product.get('item_id', '')
    item_name = product.get('item_name', '')
    item_list_name = product.get('item_list_name', '')
    price = product.get('price', 0)
    original_price = product.get('original_price', 0)

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

    # Handle discounts (if there's an original price and it's higher)
    if original_price > 0 and price < original_price:
        discount_percent = product.get(
            'discount_percentage',
            int(((original_price - price) / original_price) * 100)
        )

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
                product.get('discount_description', ''),
                datetime_today
            )
            counter['newDiscounts'] += 1


def getCategories():
    """
    Main entry point - scrape all categories from Yogya Online
    Uses hardcoded category URLs from the new supermarket subdomain
    """
    # Hardcoded category URLs from supermarket.yogyaonline.co.id
    # These are the main product categories
    categories = [
        "https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-buahbuahan/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/hot-deals-promo-minggu-ini-harbolnas/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/hot-deals-flash-sale-12-13/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/hot-deals-produk-terbaru/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/hot-deals-produk-rekomendasi/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/makanan-bahan-masakan-cooking-oil/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/produk-import-makanan-import-cemilan/category",  # noqa: E501
        "https://supermarket.yogyaonline.co.id/supermarket/official-store-yoa-pasti-hemat-pasti-hemat/category",  # noqa: E501
    ]

    logging.info(
        f"Using {len(categories)} hardcoded categories from Yogya Online"
    )

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
