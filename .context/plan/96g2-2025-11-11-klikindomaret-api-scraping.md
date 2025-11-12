# Klik Indomaret API-Based Scraping Plan

**Plan ID:** 96g2
**Date:** 2025-11-11
**Status:** Ready for implementation
**Priority:** HIGH
**Approach:** Direct API access (no HTML parsing needed)

---

## Executive Summary

Instead of scraping HTML, we discovered that Klik Indomaret uses a **public REST API** at `https://ap-mc.klikindomaret.com` for all product and category data. This approach is:
- ✅ Faster (JSON responses)
- ✅ More reliable (no HTML parsing)
- ✅ Less prone to breakage (structured data)
- ✅ Easier to maintain

---

## Task List & Execution Permissions

### Phase 1: Testing & Validation (Manual)
- [X] **Test Category API endpoint** - Verify API returns valid category data
- [X] **Test Product API endpoint** - Verify API returns valid product data
- [X] **Test pagination** - Verify multiple pages can be fetched
- [X] **Test rate limiting** - Check if API has rate limits
- [X] **Verify request headers** - Ensure headers match browser requests
- [X] **User approval required** - Review API test results before proceeding

### Phase 2: Code Implementation (Claude Code - Requires Approval)
- [X] **Create API client class** - Write `KlikIndomaretAPI` class in new file
- [X] **Create test script** - Write `test_klikindomaret_api.py` for testing
- [X] **Test with sample category** - Run test on 1 category only
- [X] **User approval required** - Review test results and code before replacing production code

### Phase 3: Production Implementation (Claude Code - Requires Approval)
- [X] **Backup old scraper** - Copy current `klikindomaret.py` to `klikindomaret_old.py`
- [X] **Update scraper file** - Replace `src/crawler/klikindomaret.py` with API version
- [X] **Add error handling** - Implement retry logic and error logging
- [X] **Add rate limiting** - Implement delays between requests
- [X] **User approval required** - Review updated code before test run

### Phase 4: Testing (Manual)
- [X] **Run test scrape** - Execute scraper on 2-3 categories only
- [X] **Verify database entries** - Check items/prices/discounts are inserted correctly
- [X] **Check for duplicates** - Verify deduplication logic works
- [X] **Monitor logs** - Check for errors or warnings
- [X] **User approval required** - Review test scrape results before full run

### Phase 5: Full Deployment (Manual)
- [X] **Run full scrape** - Execute on all categories
- [X] **Monitor performance** - Check execution time and resource usage
- [X] **Verify data quality** - Spot check random products
- [X] **Update cron schedule** - Update if needed in `config.py`
- [X] **Update Docker container** - Rebuild and deploy if needed

### Phase 6: Monitoring (Manual)
- [X] **Check daily runs** - Monitor automated scraping
- [X] **Alert on failures** - Set up error notifications
- [X] **Review metrics** - Track items/prices/discounts added daily

---

## Execution Rules

### ✅ Allowed to Execute (with approval):
1. Creating new test files
2. Creating API client class in new file
3. Running test scripts with limited scope
4. Backing up existing files
5. Updating code after user review

### ❌ Not Allowed to Execute (without explicit approval):
1. Replacing production scraper code
2. Running full scrape on all categories
3. Modifying database schema
4. Changing Docker configuration
5. Updating cron schedules
6. Deploying to production

### 🔍 Requires Manual Verification:
1. API test results
2. Database entries after test scrape
3. Performance metrics
4. Error logs
5. Data quality checks

---

## API Endpoints Discovered

### Base URL
```
https://ap-mc.klikindomaret.com
```

### 1. Category Metadata API
**Endpoint:**
```
GET /assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta
```

**Parameters:**
- `storeCode` - Store identifier (e.g., "TJKT")
- `latitude` - Location latitude (e.g., "-6.1763897")
- `longitude` - Location longitude (e.g., "106.82667")
- `mode` - Delivery mode (e.g., "DELIVERY")
- `districtId` - District ID (e.g., "141100100")

**Full Example URL:**
```
https://ap-mc.klikindomaret.com/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta?storeCode=TJKT&latitude=-6.1763897&longitude=106.82667&mode=DELIVERY&districtId=141100100
```

**Response:**
```json
{
  "data": [
    {
      "id": 345,
      "label": "Perawatan Diri",
      "children": [...]
    },
    ...
  ],
  "totalCategories": 9
}
```

---

### 2. Product Search/Listing API
**Endpoint:**
```
GET /assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result
```

**Parameters:**
- `page` - Page number (0-indexed)
- `size` - Items per page (e.g., 18, 50, 100)
- `categories` - Category filter (empty for all, or category ID)
- `storeCode` - Store identifier
- `latitude` - Location latitude
- `longitude` - Location longitude
- `mode` - Delivery mode
- `districtId` - District ID

**Full Example URL:**
```
https://ap-mc.klikindomaret.com/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result?page=0&size=50&categories=&storeCode=TJKT&latitude=-6.1763897&longitude=106.82667&mode=DELIVERY&districtId=141100100
```

**Response Structure:**
```json
{
  "data": [
    {
      "id": "product-id",
      "name": "Product Name",
      "mainImage": "https://cdn-klik.klikindomaret.com/...",
      "prices": [
        {
          "price": 15000,
          "originalPrice": 18000,
          "discount": "20%"
        }
      ],
      "sku": "SKU123",
      "category": "..."
    }
  ],
  "totalElements": 1523,
  "totalPages": 31,
  "size": 50,
  "number": 0
}
```

---

### 3. Search Suggestion API (Optional)
**Endpoint:**
```
GET /assets-klikidmsearch/api/get/catalog-xpress/api/webapp/search/suggestion
```

**Parameters:** Same as product search

**Use Case:** Get autocomplete suggestions

---

## Required Request Headers

Based on browser network analysis, these headers should be used:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.klikindomaret.com/',
    'Origin': 'https://www.klikindomaret.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
```

---

## Default Parameters

These parameters work for general scraping:

```python
DEFAULT_PARAMS = {
    'storeCode': 'TJKT',           # Jakarta store
    'latitude': '-6.1763897',      # Jakarta coordinates
    'longitude': '106.82667',
    'mode': 'DELIVERY',
    'districtId': '141100100'      # Jakarta district
}
```

**Note:** These are default values extracted from the browser. They might be configurable per region.

---

## Implementation Plan

### Phase 1: API Client Setup
```python
import requests
import json
from typing import Dict, List, Optional

class KlikIndomaretAPI:
    BASE_URL = "https://ap-mc.klikindomaret.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.klikindomaret.com/',
            'Origin': 'https://www.klikindomaret.com',
        })

        self.default_params = {
            'storeCode': 'TJKT',
            'latitude': '-6.1763897',
            'longitude': '106.82667',
            'mode': 'DELIVERY',
            'districtId': '141100100'
        }

    def get_categories(self) -> List[Dict]:
        """Get all categories"""
        url = f"{self.BASE_URL}/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta"

        response = self.session.get(url, params=self.default_params)
        response.raise_for_status()

        data = response.json()
        return data.get('data', [])

    def get_products(self, page: int = 0, size: int = 50, category_id: Optional[str] = None) -> Dict:
        """Get products with pagination"""
        url = f"{self.BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"

        params = {
            **self.default_params,
            'page': page,
            'size': size,
            'categories': category_id or ''
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        return response.json()
```

---

### Phase 2: Scraper Implementation

```python
import pytz
import logging
import shortuuid
from datetime import datetime
from tqdm import tqdm

from db import DBSTATE
from util import cleanUpCurrency

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

db = DBSTATE

def scrape_klikindomaret_api():
    """Main scraping function using API"""
    api = KlikIndomaretAPI()

    newItems = 0
    totalItems = 0
    newPrices = 0
    newDiscounts = 0

    # Get current time in Asia/Jakarta
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_today = now.strftime("%Y-%m-%d")
    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Step 1: Get all categories
        logging.info("Fetching categories...")
        categories = api.get_categories()
        logging.info(f"Found {len(categories)} categories")

        # Step 2: Loop through categories
        for category in tqdm(categories, desc="Scraping categories"):
            category_id = category.get('id')
            category_name = category.get('label', 'Unknown')

            logging.info(f"Processing category: {category_name} (ID: {category_id})")

            # Step 3: Get first page to determine total pages
            first_page = api.get_products(page=0, size=50, category_id=category_id)
            total_pages = first_page.get('totalPages', 1)
            total_elements = first_page.get('totalElements', 0)

            logging.info(f"Category {category_name} has {total_elements} products across {total_pages} pages")

            # Step 4: Loop through all pages
            for page in tqdm(range(total_pages), desc=f"Pages for {category_name}", leave=False):
                # Get products for this page
                if page == 0:
                    result = first_page  # Reuse first page
                else:
                    result = api.get_products(page=page, size=50, category_id=category_id)

                products = result.get('data', [])

                # Step 5: Process each product
                for product in products:
                    totalItems += 1

                    # Extract product data
                    product_id = product.get('id')
                    product_name = product.get('name')
                    product_sku = product.get('sku', product_id)
                    product_image = product.get('mainImage', '')
                    product_link = f"https://www.klikindomaret.com/xpress/{product_id}"

                    # Extract price data
                    prices_data = product.get('prices', [])
                    if prices_data and len(prices_data) > 0:
                        price_info = prices_data[0]
                        product_price = price_info.get('price', 0)
                        original_price = price_info.get('originalPrice', product_price)
                        discount_pct = price_info.get('discount', '')
                    else:
                        product_price = 0
                        original_price = 0
                        discount_pct = ''

                    # Check if item exists in database
                    reqQuery = {
                        'script': "SELECT id FROM items WHERE sku=? OR name=?",
                        'values': (product_sku, product_name)
                    }
                    checkIdItem = db.execute(**reqQuery)
                    idItem = shortuuid.uuid()

                    if len(checkIdItem) == 0:
                        # Insert new item
                        db["items"].insert(
                            idItem, product_sku, product_name,
                            category_name, product_image, product_link,
                            'klikindomaret', datetime_today
                        )
                        newItems += 1
                    else:
                        idItem = checkIdItem[0][0]

                    # Check if price exists for today
                    reqQuery = {
                        'script': "SELECT id FROM prices WHERE items_id=? AND created_at LIKE ? AND price=?",
                        'values': (idItem, f'{date_today}%', product_price)
                    }
                    checkItemIdinPrice = db.execute(**reqQuery)

                    if len(checkItemIdinPrice) == 0:
                        db["prices"].insert(
                            shortuuid.uuid(), idItem, product_price, "", datetime_today
                        )
                        newPrices += 1

                    # Check if discount exists for today
                    if original_price > product_price:
                        reqQuery = {
                            'script': "SELECT id FROM discounts WHERE items_id=? AND created_at LIKE ? AND discount_price=? AND original_price=?",
                            'values': (idItem, f'{date_today}%', product_price, original_price)
                        }
                        checkItemIdinDiscount = db.execute(**reqQuery)

                        if len(checkItemIdinDiscount) == 0:
                            db["discounts"].insert(
                                shortuuid.uuid(), idItem, product_price,
                                original_price, discount_pct, "", datetime_today
                            )
                            newDiscounts += 1

        logging.info(f"=== Finished scraping {totalItems} items")
        logging.info(f"=== Added {newItems} new items, {newPrices} prices, {newDiscounts} discounts")

        return {
            'totalItems': totalItems,
            'newItems': newItems,
            'newPrices': newPrices,
            'newDiscounts': newDiscounts
        }

    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    scrape_klikindomaret_api()
```

---

## Advantages Over HTML Scraping

| Aspect | HTML Scraping | API Scraping |
|--------|---------------|--------------|
| **Speed** | Slow (parse HTML) | Fast (JSON) |
| **Reliability** | Breaks on HTML changes | Stable structure |
| **Data Quality** | Messy, needs cleanup | Clean, structured |
| **Pagination** | Complex form params | Simple page numbers |
| **Maintenance** | High (CSS selectors) | Low (JSON keys) |
| **Bot Detection** | High risk | Lower risk |

---

## Testing Strategy

### 1. Test Category API
```python
def test_category_api():
    api = KlikIndomaretAPI()
    categories = api.get_categories()

    print(f"Total categories: {len(categories)}")
    for cat in categories:
        print(f"  - {cat.get('label')} (ID: {cat.get('id')})")
```

### 2. Test Product API (Single Page)
```python
def test_product_api():
    api = KlikIndomaretAPI()
    result = api.get_products(page=0, size=10)

    print(f"Total products: {result.get('totalElements')}")
    print(f"Total pages: {result.get('totalPages')}")
    print(f"Products in this page: {len(result.get('data', []))}")

    for product in result.get('data', [])[:3]:
        print(f"\n  Product: {product.get('name')}")
        print(f"  SKU: {product.get('sku')}")
        print(f"  Price: {product.get('prices', [{}])[0].get('price', 0)}")
```

### 3. Test with Category Filter
```python
def test_category_filter():
    api = KlikIndomaretAPI()

    # Get categories first
    categories = api.get_categories()
    first_category = categories[0]

    print(f"Testing category: {first_category.get('label')}")

    # Get products for that category
    result = api.get_products(page=0, size=10, category_id=first_category.get('id'))
    print(f"Products in category: {result.get('totalElements')}")
```

---

## Error Handling

```python
import time
import random

def api_call_with_retry(func, max_retries=3, backoff_factor=2):
    """Wrapper for API calls with retry logic"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = backoff_factor ** attempt
                logging.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:  # Server error
                wait_time = backoff_factor ** attempt
                logging.warning(f"Server error. Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.RequestException as e:
            wait_time = backoff_factor ** attempt
            logging.warning(f"Request failed. Waiting {wait_time}s before retry {attempt+1}/{max_retries}")
            time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} retries")
```

---

## Rate Limiting & Delays

```python
import time
import random

class RateLimiter:
    def __init__(self, min_delay=1, max_delay=3):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request = 0

    def wait(self):
        """Wait before next request"""
        elapsed = time.time() - self.last_request
        delay = random.uniform(self.min_delay, self.max_delay)

        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request = time.time()


# Usage in API class
class KlikIndomaretAPI:
    def __init__(self):
        # ... existing init code ...
        self.rate_limiter = RateLimiter(min_delay=0.5, max_delay=2)

    def get_products(self, ...):
        self.rate_limiter.wait()
        # ... existing get_products code ...
```

---

## Data Validation

```python
from typing import Dict, Any

def validate_product(product: Dict[str, Any]) -> bool:
    """Validate product data before inserting to DB"""
    required_fields = ['id', 'name']

    # Check required fields
    for field in required_fields:
        if not product.get(field):
            logging.warning(f"Product missing required field: {field}")
            return False

    # Validate price
    prices = product.get('prices', [])
    if not prices or len(prices) == 0:
        logging.warning(f"Product {product.get('name')} has no price data")
        return False

    price = prices[0].get('price', 0)
    if price <= 0:
        logging.warning(f"Product {product.get('name')} has invalid price: {price}")
        return False

    return True
```

---

## JSON Backup

```python
import json
import os
from datetime import datetime

def save_json_backup(data: dict, vendor: str, data_type: str):
    """Save JSON backup of scraped data"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")

    backup_dir = f"data/{vendor}/{data_type}"
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"{backup_dir}/{date_str}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"Saved backup to {filename}")


# Usage
categories = api.get_categories()
save_json_backup(categories, 'klikindomaret', 'categories')
```

---

## Migration from Old Code

### Files to Update

1. **`src/crawler/klikindomaret.py`**
   - Replace `getDataCategories()` function
   - Remove all BeautifulSoup imports
   - Add API client class
   - Keep database logic (deduplication, inserts)

2. **`src/main.py`**
   - No changes needed (still calls same function)

3. **`src/config.py`**
   - Add API configuration if needed

---

## Complete Updated File

```python
# src/crawler/klikindomaret.py

import requests
import pytz
import logging
import shortuuid
import time
import random
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List, Optional

from db import DBSTATE
from util import cleanUpCurrency

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)

db = DBSTATE


class KlikIndomaretAPI:
    """API client for Klik Indomaret"""

    BASE_URL = "https://ap-mc.klikindomaret.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.klikindomaret.com/',
            'Origin': 'https://www.klikindomaret.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
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
        url = f"{self.BASE_URL}/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta"

        self._rate_limit()
        response = self.session.get(url, params=self.default_params)
        response.raise_for_status()

        data = response.json()
        return data.get('data', [])

    def get_products(self, page: int = 0, size: int = 50, category_id: Optional[str] = None) -> Dict:
        """Get products with pagination"""
        url = f"{self.BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"

        params = {
            **self.default_params,
            'page': page,
            'size': size,
            'categories': category_id or ''
        }

        self._rate_limit()
        response = self.session.get(url, params=params)
        response.raise_for_status()

        return response.json()


def getDataCategories():
    """Main scraping function - updated to use API"""
    api = KlikIndomaretAPI()

    newItems = 0
    totalItem = 0
    newPrices = 0
    newDiscounts = 0
    products = []

    # Get current time
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    date_today = now.strftime("%Y-%m-%d")
    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Get all categories
        logging.info("Fetching categories from API...")
        categories = api.get_categories()
        logging.info(f"Found {len(categories)} categories")

        # Loop through categories
        for category in tqdm(categories, desc="Scrape Category"):
            category_id = category.get('id')
            category_name = category.get('label', 'Unknown')

            # Get first page to know total pages
            first_page = api.get_products(page=0, size=50, category_id=category_id)
            total_pages = first_page.get('totalPages', 1)

            # Loop through all pages
            for page in tqdm(range(total_pages), desc=f"Scrape {category_name}", leave=False):
                if page == 0:
                    result = first_page
                else:
                    result = api.get_products(page=page, size=50, category_id=category_id)

                items = result.get('data', [])

                # Process each product
                for item in items:
                    totalItem += 1

                    product_id = item.get('id', '')
                    product_sku = item.get('sku', product_id)
                    product_name = item.get('name', '')
                    product_image = item.get('mainImage', '')
                    product_link = f"https://www.klikindomaret.com/xpress/{product_id}"

                    # Get price info
                    prices_data = item.get('prices', [])
                    if prices_data:
                        price_info = prices_data[0]
                        product_price = price_info.get('price', 0)
                        original_price = price_info.get('originalPrice', product_price)
                        discount_pct = price_info.get('discount', '')
                    else:
                        product_price = 0
                        original_price = 0
                        discount_pct = ''

                    # Check if item exists
                    reqQuery = {
                        'script': "SELECT id FROM items WHERE sku=? OR name=?",
                        'values': (product_sku, product_name)
                    }
                    checkIdItem = db.execute(**reqQuery)
                    idItem = shortuuid.uuid()

                    if len(checkIdItem) == 0:
                        db["items"].insert(
                            idItem, product_sku, product_name,
                            category_name, product_image, product_link,
                            'klikindomaret', datetime_today
                        )
                        newItems += 1
                    else:
                        idItem = checkIdItem[0][0]

                    # Check price
                    reqQuery = {
                        'script': "SELECT id FROM prices WHERE items_id=? AND created_at LIKE ? AND price=?",
                        'values': (idItem, f'{date_today}%', product_price)
                    }
                    checkItemIdinPrice = db.execute(**reqQuery)

                    if len(checkItemIdinPrice) == 0:
                        db["prices"].insert(shortuuid.uuid(), idItem, product_price, "", datetime_today)
                        newPrices += 1

                    # Check discount
                    if original_price > product_price:
                        reqQuery = {
                            'script': "SELECT id FROM discounts WHERE items_id=? AND created_at LIKE ? AND discount_price=? AND original_price=?",
                            'values': (idItem, f'{date_today}%', product_price, original_price)
                        }
                        checkItemIdinDiscount = db.execute(**reqQuery)

                        if len(checkItemIdinDiscount) == 0:
                            db["discounts"].insert(
                                shortuuid.uuid(), idItem, product_price,
                                original_price, discount_pct, "", datetime_today
                            )
                            newDiscounts += 1

                    # Add to products list
                    products.append({
                        'id': product_id,
                        'name': product_name,
                        'sku': product_sku,
                        'price': product_price,
                        'category': category_name,
                        'link': product_link,
                        'image': product_image
                    })

        logging.info(f"=== Finish scrap {totalItem} item by added {newItems} items, {newPrices} prices, {newDiscounts} discounts")

        return products

    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return []
```

---

## Next Steps

1. **Test API endpoints with requests library** (Phase 1)
2. **Update `src/crawler/klikindomaret.py`** with new code
3. **Run test scrape** with 1-2 categories
4. **Verify database insertions**
5. **Run full scrape**
6. **Monitor for rate limiting**
7. **Update Docker container**

---

## Monitoring & Alerts

```python
def report_metrics(stats: dict):
    """Report scraping metrics to SteinDB or logging"""
    logging.info("=== Scraping Metrics ===")
    logging.info(f"Total Items Processed: {stats['totalItems']}")
    logging.info(f"New Items Added: {stats['newItems']}")
    logging.info(f"New Prices Added: {stats['newPrices']}")
    logging.info(f"New Discounts Added: {stats['newDiscounts']}")

    # Optional: Send to SteinDB (if configured)
    # util.sendMetrics(stats)
```

---

## References

- **API Base:** `https://ap-mc.klikindomaret.com`
- **Category Endpoint:** `/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta`
- **Product Endpoint:** `/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result`
- **Current Code:** `src/crawler/klikindomaret.py`
- **Database:** `src/db.py`
- **Utilities:** `src/util.py`

---

**Created:** 2025-11-11
**Last Updated:** 2025-11-11
**Status:** Ready for implementation
**Estimated Time:** 2-3 hours to implement and test
