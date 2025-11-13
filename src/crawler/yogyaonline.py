"""
Yogya Online Crawler - Updated with infinite scroll support
Uses cloudscraper for bot detection bypass and AJAX POST requests for pagination
Website uses infinite scroll with /load-more-product endpoint
"""

import logging
import random
import re
import time
import urllib.parse
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


def _rate_limit():
    """Simple rate limiting to avoid overwhelming the server"""
    time.sleep(random.uniform(1.0, 2.5))


def _extract_category_id(parser):
    """Extract category ID from the page HTML"""
    # Look for data-category-id attribute
    cat_elem = parser.find(attrs={'data-category-id': True})
    if cat_elem:
        return int(cat_elem['data-category-id'])
    return None


def _fetch_products_page(scraper, category_url, category_id, page_num):
    """
    Fetch a page of products using the load-more-product AJAX endpoint

    Args:
        scraper: cloudscraper session
        category_url: Original category URL (for referer)
        category_id: Category ID
        page_num: Page number to fetch

    Returns:
        dict with 'products', 'total_pages', 'success' keys
    """
    url = 'https://supermarket.yogyaonline.co.id/load-more-product'

    # Get XSRF token from cookie
    xsrf_token = scraper.cookies.get('XSRF-TOKEN')
    if xsrf_token:
        xsrf_token = urllib.parse.unquote(xsrf_token)

    payload = {
        'current_page': page_num,
        'brands': [],
        'category_id': category_id
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': category_url,
    }

    if xsrf_token:
        headers['X-XSRF-TOKEN'] = xsrf_token

    try:
        _rate_limit()
        response = scraper.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            logging.error(
                f"Failed to fetch page {page_num}: "
                f"Status {response.status_code}"
            )
            return {'products': [], 'total_pages': 0, 'success': False}

        data = response.json()

        if not data.get('status'):
            logging.error(
                f"API returned error for page {page_num}: "
                f"{data.get('message')}"
            )
            return {'products': [], 'total_pages': 0, 'success': False}

        # Parse HTML from response
        html_content = data.get('html', '')
        parser = BeautifulSoup(html_content, 'html.parser')

        # Find all product items
        product_divs = parser.find_all("div", class_="product-item")

        products = []
        for div in product_divs:
            product = _extract_product_from_html(div)
            if product:
                products.append(product)

        return {
            'products': products,
            'total_pages': data.get('total_page', 0),
            'success': True
        }

    except Exception as e:
        logging.error(f"Error fetching page {page_num}: {str(e)}")
        return {'products': [], 'total_pages': 0, 'success': False}


def _extract_product_from_html(div):
    """Extract product data from HTML div element"""
    try:
        # Extract product name from div with product-name class
        name_div = div.find("div", class_="product-name")
        if not name_div:
            return None

        # Extract SKU and name from onclick attribute
        onclick = name_div.get('onclick', '')
        match = re.search(
            r"viewProduct\('([^']+)',\s*null,\s*'([^']*)',\s*'([^']*)'\)",
            onclick
        )

        if not match:
            return None

        sku = match.group(1)
        brand = match.group(2)
        name = match.group(3)

        # Extract link from image container link
        link_elem = div.find("a", class_="product-image-container")
        link = link_elem.get('href', '') if link_elem else ''

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


def scrape_category(scraper, category_url):
    """
    Scrape all products from a single category using infinite scroll

    Args:
        scraper: cloudscraper session
        category_url: URL of the category page

    Returns:
        list of products
    """
    logging.info(f"Scraping category: {category_url}")

    # First, visit the category page to get cookies and category ID
    _rate_limit()
    response = scraper.get(category_url, timeout=30)

    if response.status_code != 200:
        logging.error(
            f"Failed to load category page: {response.status_code}"
        )
        return []

    # Parse the page to find category ID
    parser = BeautifulSoup(response.text, 'html.parser')
    category_id = _extract_category_id(parser)

    if not category_id:
        logging.error(f"Could not find category ID for {category_url}")
        return []

    logging.info(f"Found category ID: {category_id}")

    # Get first page to determine total pages
    result = _fetch_products_page(scraper, category_url, category_id, 1)

    if not result['success']:
        logging.error("Failed to fetch first page")
        return []

    all_products = result['products']
    total_pages = result['total_pages']

    logging.info(
        f"Category has {total_pages} pages, "
        f"fetched {len(all_products)} products from page 1"
    )

    # Fetch remaining pages
    for page_num in range(2, total_pages + 1):
        logging.info(f"Fetching page {page_num}/{total_pages}")
        result = _fetch_products_page(
            scraper, category_url, category_id, page_num
        )

        if result['success']:
            all_products.extend(result['products'])
            logging.info(
                f"Fetched {len(result['products'])} products from "
                f"page {page_num}"
            )
        else:
            logging.warning(f"Failed to fetch page {page_num}, skipping")

    logging.info(
        f"Finished scraping category, total products: {len(all_products)}"
    )
    return all_products


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

    # Create cloudscraper session (reuse across all categories)
    scraper = cloudscraper.create_scraper()

    compiled_data = []

    # Scrape each category
    for cat_index, category in enumerate(
        tqdm(categories, desc="Scraping categories")
    ):
        logging.info(
            f"Processing category {cat_index + 1}/{len(categories)}: "
            f"{category}"
        )

        products = scrape_category(scraper, category)

        # Save products to database
        for product in products:
            _save_product_to_db(product, counter)

        compiled_data.extend(products)

        logging.info(
            f"Category {cat_index + 1} complete: "
            f"{len(products)} products scraped"
        )

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
