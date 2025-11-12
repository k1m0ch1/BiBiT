"""
Klik Indomaret API Client
Uses cloudscraper to bypass Cloudflare bot detection
"""

import json
import logging
import time
import random
from typing import Dict, List, Optional
import cloudscraper

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)


class KlikIndomaretAPI:
    """
    API client for Klik Indomaret
    Uses cloudscraper to bypass Cloudflare bot detection automatically.
    """

    BASE_URL = "https://ap-mc.klikindomaret.com"

    def __init__(self):
        self.session = cloudscraper.create_scraper()

        # Try to mimic browser as closely as possible
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.klikindomaret.com/',
            'Origin': 'https://www.klikindomaret.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })

        self.default_params = {
            'storeCode': 'TJKT',
            'latitude': '-6.1763897',
            'longitude': '106.82667',
            'mode': 'DELIVERY',
            'districtId': '141100100'
        }

    def _rate_limit(self):
        """Simple rate limiting"""
        time.sleep(random.uniform(0.5, 1.5))

    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        logging.info("Fetching categories...")
        endpoint = "/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta"
        url = f"{self.BASE_URL}{endpoint}"

        self._rate_limit()

        try:
            response = self.session.get(url, params=self.default_params, timeout=30)
            response.raise_for_status()

            data = response.json()
            categories = data.get('data', [])
            logging.info(f"Found {len(categories)} categories")
            return categories

        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 403:
                logging.error("403 Forbidden - Bot detection still triggered despite cloudscraper!")
                logging.error("You may need to try playwright as an alternative.")
                raise Exception("API blocked request even with cloudscraper. Consider using playwright.")
            raise

    def get_products(self, page: int = 0, size: int = 50, category_id: Optional[str] = None) -> Dict:
        """Get products with pagination"""
        endpoint = "/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"
        url = f"{self.BASE_URL}{endpoint}"

        params = {
            **self.default_params,
            'page': page,
            'size': size,
            'categories': category_id or ''
        }

        self._rate_limit()

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 403:
                logging.error("403 Forbidden - Bot detection still triggered despite cloudscraper!")
                raise Exception("API blocked request even with cloudscraper. Consider using playwright.")
            raise

    def get_all_products_for_category(self, category_id: str, category_name: str = "Unknown") -> List[Dict]:
        """Get all products for a specific category (handles pagination)"""
        logging.info(f"Fetching all products for category: {category_name} (ID: {category_id})")

        all_products = []

        # Get first page to determine total pages
        first_page_response = self.get_products(page=0, size=50, category_id=category_id)
        first_page_data = first_page_response.get('data', {})

        total_pages = first_page_data.get('totalPages', 1)
        total_elements = first_page_data.get('totalElements', 0)

        logging.info(f"Category has {total_elements} products across {total_pages} pages")

        # Add first page products
        all_products.extend(first_page_data.get('content', []))

        # Fetch remaining pages
        for page_num in range(1, total_pages):
            logging.info(f"Fetching page {page_num + 1}/{total_pages} for {category_name}")
            page_response = self.get_products(page=page_num, size=50, category_id=category_id)
            page_data = page_response.get('data', {})
            all_products.extend(page_data.get('content', []))

        logging.info(f"Retrieved {len(all_products)} products for {category_name}")
        return all_products


# Test function
if __name__ == "__main__":
    print("Testing Klik Indomaret API with cloudscraper...")
    print("This should bypass Cloudflare bot detection.\n")

    try:
        api = KlikIndomaretAPI()

        # Test 1: Get categories
        print("[TEST 1] Fetching categories...")
        categories = api.get_categories()
        print(f"[OK] Found {len(categories)} categories")

        if categories:
            print("\nFirst 3 categories:")
            for i, cat in enumerate(categories[:3]):
                print(f"  {i+1}. {cat.get('name', 'Unknown')} (ID: {cat.get('id')})")

            # Test 2: Get products for first category
            first_category = categories[0]
            cat_id = str(first_category.get('id'))
            cat_name = first_category.get('name', 'Unknown')

            print(f"\n[TEST 2] Fetching products for category: {cat_name}")
            result = api.get_products(page=0, size=5, category_id=cat_id)

            result_data = result.get('data', {})
            total = result_data.get('totalElements', 0)
            products = result_data.get('content', [])

            print(f"[OK] Category has {total} total products")
            print(f"[OK] Retrieved {len(products)} products (page 1)")

            if products:
                print("\nFirst product:")
                product = products[0]
                print(f"  ID: {product.get('productId')}")
                print(f"  Name: {product.get('productName')}")
                print(f"  PLU/SKU: {product.get('plu')}")
                print(f"  Price: Rp {product.get('price', 0):,}")
                if product.get('finalPrice'):
                    print(f"  Final Price: Rp {product.get('finalPrice', 0):,}")
                if product.get('discountText'):
                    print(f"  Discount: {product.get('discountText')}")

        print("\n[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        print("\nCloudscraper is installed but still getting blocked.")
        print("You may need to try playwright as an alternative:")
        print("  pip install playwright && playwright install chromium")
        import sys
        sys.exit(1)
