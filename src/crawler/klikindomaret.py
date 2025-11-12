"""
Klik Indomaret Crawler - API-based version
Uses KlikIndomaretAPI with cloudscraper to bypass bot detection
"""

import logging
import pytz
import shortuuid

from datetime import datetime
from tqdm import tqdm

from api_client.klikindomaret_api import KlikIndomaretAPI
from db import DBSTATE

db = DBSTATE

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


def getDataCategories():
    """
    Main scraping function for Klik Indomaret
    Uses API client instead of HTML scraping
    """
    newItems = 0
    totalItem = 0
    newPrices = 0
    newDiscounts = 0

    try:
        # Initialize API client
        api = KlikIndomaretAPI()

        # Get all categories
        categories = api.get_categories()
        logging.info(f"Found {len(categories)} categories to scrape")

        # Process each category
        for category in tqdm(categories, desc="Processing categories"):
            category_id = str(category.get('id'))
            category_name = category.get('name', 'Unknown')

            # Get all products for this category
            try:
                products = api.get_all_products_for_category(
                    category_id=category_id,
                    category_name=category_name
                )

                # Process each product
                for product in tqdm(
                    products,
                    desc=f"Processing {category_name}",
                    leave=False
                ):
                    # Get product data with proper field mapping
                    product_id = str(product.get('productId', ''))
                    plu = str(product.get('plu', ''))
                    product_name = product.get('productName', '')
                    image_url = product.get('imageUrl', '')
                    permalink = product.get('permalink', '')
                    price = product.get('price', 0)
                    final_price = product.get('finalPrice')
                    discount_text = product.get('discountText', '')

                    # Skip if essential data is missing
                    if not product_name or not plu:
                        logging.warning(f"Skipping product with missing data: {product}")
                        continue

                    # Build full product URL
                    product_link = (
                        f"https://www.klikindomaret.com/product/{permalink}"
                        if permalink else ""
                    )

                    # Get current datetime in Asia/Jakarta timezone
                    now = datetime.now(pytz.timezone("Asia/Jakarta"))
                    date_today = now.strftime("%Y-%m-%d")
                    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

                    # Check if item already exists (by PLU or name)
                    reqQuery = {
                        'script': "SELECT id FROM items WHERE sku=? OR name=?",
                        'values': (plu, product_name)
                    }
                    checkIdItem = db.execute(**reqQuery)

                    idItem = product_id
                    totalItem += 1

                    # Insert new item if it doesn't exist
                    if len(checkIdItem) == 0:
                        db["items"].insert(
                            product_id,
                            plu,
                            product_name,
                            category_name,
                            image_url,
                            product_link,
                            'klikindomaret',
                            datetime_today
                        )
                        newItems += 1
                    else:
                        idItem = checkIdItem[0][0]

                    # Use final_price if available, otherwise use regular price
                    current_price = final_price if final_price is not None else price

                    # Check if today's price already exists
                    reqQuery = {
                        'script': (
                            "SELECT id FROM prices "
                            "WHERE items_id=? AND created_at LIKE ? AND price=?"
                        ),
                        'values': (idItem, f'{date_today}%', current_price)
                    }
                    checkItemIdinPrice = db.execute(**reqQuery)

                    # Insert new price if it doesn't exist
                    if len(checkItemIdinPrice) == 0:
                        db["prices"].insert(
                            shortuuid.uuid(),
                            idItem,
                            current_price,
                            "",
                            datetime_today
                        )
                        newPrices += 1

                    # Handle discounts (if finalPrice is different from price)
                    if final_price is not None and final_price < price:
                        # Calculate discount percentage
                        discount_percent = int(((price - final_price) / price) * 100)

                        reqQuery = {
                            'script': (
                                "SELECT id FROM discounts "
                                "WHERE items_id=? AND created_at LIKE ? "
                                "AND discount_price=? AND original_price=?"
                            ),
                            'values': (idItem, f'{date_today}%', final_price, price)
                        }
                        checkItemIdinDiscount = db.execute(**reqQuery)

                        if len(checkItemIdinDiscount) == 0:
                            db["discounts"].insert(
                                shortuuid.uuid(),
                                idItem,
                                final_price,
                                price,
                                discount_percent,
                                discount_text,
                                datetime_today
                            )
                            newDiscounts += 1

            except Exception as e:
                logging.error(f"Error processing category {category_name}: {str(e)}")
                continue

        # Log summary
        summary = (
            f"=== Finish scrap {totalItem} items by added {newItems} items, "
            f"{newPrices} prices, {newDiscounts} discounts"
        )
        logging.info(summary)

        if newItems == 0 and newPrices == 0 and newDiscounts == 0:
            logging.info("=== I guess nothing different today")

        return summary

    except Exception as e:
        error_msg = f"=== ERROR: Scraping failed - {str(e)}"
        logging.error(error_msg)
        return error_msg
