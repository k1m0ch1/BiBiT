# Klik Indomaret Scraping Analysis & Plan

**Plan ID:** 843h
**Date:** 2025-11-11
**Status:** Website structure has changed - scraper needs update
**Priority:** HIGH

---

## Executive Summary

The Klik Indomaret website has undergone a complete HTML structure redesign. The current scraper in `src/crawler/klikindomaret.py` will NOT work anymore and requires a complete rewrite.

---

## Current Website Analysis (Using Playwright)

### Category Structure

**Main Categories (9 total):**
1. Perawatan Diri (Personal Care)
2. Makanan (Food)
3. Dapur & Bahan Masakan (Kitchen & Ingredients)
4. Minuman (Beverages)
5. Ibu & Anak (Mother & Baby)
6. Kesehatan & Kebersihan (Health & Hygiene)
7. Kebutuhan Rumah (Household Needs)
8. Makanan Hewan (Pet Food)
9. Lainnya (Others)

### HTML Structure Changes

#### OLD Structure (Current Code - Line 40-60)
```html
<div class="container-wrp-menu bg-white list-shadow list-category-mobile">
  <!-- Type 1: Categories without children -->
  <span class="clickMenu">
    <a href="/category/makanan">Makanan</a>
  </span>

  <!-- Type 2: Categories with children -->
  <ul class="nd-kategori">
    <li class="menu-seeall">
      <a href="/category/perawatan-diri">See All</a>
    </li>
  </ul>
</div>
```

#### NEW Structure (Current Website)
```html
<div class="mega-menu flex bg-white">
  <!-- Main category navigation -->
  <div class="menu-list-wrap h-full flex-col items-start gap-y-4 overflow-y-scroll">
    <div class="menu-list px-3.5 py-2 text-b2 capitalize">Perawatan Diri</div>
    <div class="menu-list px-3.5 py-2 text-b2 capitalize">Makanan</div>
    <!-- ... more categories ... -->
  </div>

  <!-- Subcategory links -->
  <div class="submenu-list-wrap flex-1 p-6">
    <a href="/xpress/category/perawatan-diri/wajah/pembersih-wajah">Pembersih</a>
    <a href="/xpress/category/perawatan-diri/wajah/bedak">Bedak</a>
    <!-- ... more subcategories ... -->
  </div>
</div>
```

**Key Changes:**
- Class names completely different
- URL format changed: `/category/...` → `/xpress/category/...`
- No more `clickMenu` or `nd-kategori` classes
- Now uses Tailwind CSS classes
- Menu items are `div` elements, not `span` with links

---

## Current Code Flow Analysis

### File: `src/crawler/klikindomaret.py`

#### Step 1: Get Categories (Lines 33-61)
```python
def getDataCategories():
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')

    # BROKEN: This selector doesn't exist anymore
    categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})

    # Type 1: Direct category links
    c1 = categoryClass.findAll('span', attrs={'class':'clickMenu'})
    for c1_element in c1:
        if c1_element.a is not None:
            link = c1_element.find('a')['href']
            categories.append(link)

    # Type 2: Categories with subcategories
    c2 = categoryClass.findAll('ul', attrs={'class':'nd-kategori'})
    for c2_element in c2:
        c2_element_menu = c2_element.find('li', attrs={'class':'menu-seeall'})
        if c2_element_menu is not None:
            link = c2_element_menu.a['href']
            categories.append(link)
```

**Status:** ❌ BROKEN - CSS classes don't exist

---

#### Step 2: Loop Through Categories (Lines 65-77)
```python
for category in tqdm(categories, desc="Scrape Category"):
    category_name = category.split("/")[2]  # Extract from URL
    category_url = TARGET_URL + category
    getPage = requests.get(category_url)
    parser = BeautifulSoup(getPage.text, 'html.parser')

    # Find pagination selector
    if parser.find("select", {"id": "ddl-filtercategory-sort"}) is not None:
        getPageList = parser.find("select", {"class": "form-control pagelist"})
        maxPage = len(getPageList.find_all('option'))
```

**Status:** ⚠️ UNKNOWN - Need to test if pagination still exists

---

#### Step 3: Pagination & Parameters (Lines 77-82)
```python
pageParam = {
    "productbrandid": "",
    "sorcol": "",
    "pagesize": 50,
    "startprice": "",
    "endproce": "",
    "attributes": "",
    "page": page+1,
    "categories": category_name
}
categoryPage = requests.get(f"{category_url}", params=pageParam)
```

**Status:** ⚠️ UNKNOWN - Parameters might have changed

---

#### Step 4: Extract Product Data (Lines 84-117)
```python
# Find products by ID pattern
getItem = parser.find_all("div", {"id": re.compile("^categoryFilterProduct-")})

for item in getItem:
    # Extract product details
    productID = item.find("div", {'class': 'sendby oksendby classsendby{index+1}'}).get('selecteds')
    container = item.find('div', {'class': 'wrp-content'})

    # Price extraction
    productPrice = container.find('span', {'class': 'normal price-value'}).get_text()
    productOldPrice = container.find('span', {'class': 'strikeout disc-price'})
    productPromotion = container.find('span', {'class': 'discount'})

    # Build item object
    item = {
        'name': container.find('div', {'class': 'title'}).get_text().replace("\n", ""),
        'id': productID,
        'sub_category': category_name.replace("-1","").replace("-"," "),
        'price': cleanUpCurrency(productPrice),
        'link': f"{TARGET_URL}{item.find('a').get('href')}",
        'image': item.find('img').get('data-src'),
        "promotion": {
            "type": productPromotion,
            "original_price": productOldPrice
        }
    }
```

**Status:** ❌ BROKEN - Product listing selectors need verification

---

#### Step 5: Database Operations (Lines 121-158)

##### Deduplication Pattern
```python
# Check if item exists (by SKU OR name)
reqQuery = {
    'script': "SELECT id FROM items WHERE sku=? OR name=?",
    'values': (item['id'], item['name'])
}
checkIdItem = db.execute(**reqQuery)
```

##### Insert Item
```python
if len(checkIdItem) == 0:
    db["items"].insert(idItem, item['id'], item['name'],
                       item['sub_category'], item['image'], item['link'],
                       'klikindomaret', datetime_today)
    newItems += 1
else:
    idItem = checkIdItem[0][0]
```

##### Insert Price (Daily)
```python
reqQuery = {
    'script': "SELECT id FROM prices WHERE items_id=? AND created_at LIKE ? AND price=?",
    'values': (idItem, f'{date_today}%', item['price'])
}
checkItemIdinPrice = db.execute(**reqQuery)

if len(checkItemIdinPrice) == 0:
    db["prices"].insert(shortuuid.uuid(), idItem, item['price'], "", datetime_today)
    newPrices += 1
```

##### Insert Discount
```python
reqQuery = {
    'script': "SELECT id FROM discounts WHERE items_id=? AND created_at LIKE ? AND discount_price=? AND original_price=?",
    'values': (idItem, f'{date_today}%', item['price'], productOldPrice)
}
checkItemIdinDiscount = db.execute(**reqQuery)

if len(checkItemIdinDiscount) == 0:
    db["discounts"].insert(shortuuid.uuid(), idItem, item['price'], productOldPrice, productPromotion, "", datetime_today)
    newDiscounts += 1
```

**Status:** ✅ WORKING - Database logic is good, just needs correct data

---

## Issues Identified

### 1. HTML Structure Completely Changed
- **Impact:** HIGH
- **Lines Affected:** 40-60 (category extraction)
- **Solution Required:** Rewrite selectors for new structure

### 2. URL Format Changed
- **Old:** `/category/makanan`
- **New:** `/xpress/category/perawatan-diri/wajah/pembersih-wajah`
- **Impact:** HIGH
- **Solution Required:** Update URL construction logic

### 3. Potential Bot Detection
- **Evidence:** Category pages timeout (60s) when accessed
- **Impact:** CRITICAL
- **Solution Required:** Use Playwright/Selenium with proper headers/delays

### 4. Static Scraping (requests/BeautifulSoup)
- **Issue:** Modern sites use JavaScript rendering
- **Impact:** MEDIUM
- **Solution Required:** Switch to Playwright for dynamic content

### 5. Error Handling
- **Lines 73-75:** Generic error message, continues loop
- **Issue:** Doesn't capture enough debug info
- **Impact:** LOW
- **Solution Required:** Better logging

---

## Scraping Flow (What Actually Happens)

### Current Flow
```
1. GET https://www.klikindomaret.com
   └─> Parse HTML for categories
       └─> Extract category links
           └─> For each category:
               ├─> GET category page
               ├─> Find max pages
               └─> For each page:
                   ├─> GET page with params
                   ├─> Extract products
                   └─> For each product:
                       ├─> Check if exists
                       ├─> Insert/update item
                       ├─> Insert price (if new today)
                       └─> Insert discount (if applicable)
```

### Key Patterns

#### Deduplication Strategy
- **Items:** Check by `sku=? OR name=?`
- **Prices:** Check by `items_id + date + price`
- **Discounts:** Check by `items_id + date + discount_price + original_price`

#### Daily Granularity
```python
date_today = now.strftime("%Y-%m-%d")          # "2025-11-11"
datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")  # "2025-11-11 14:30:45"

# Query pattern:
"SELECT ... WHERE created_at LIKE '2025-11-11%'"
```

#### Data Storage
```python
items = {
    'id': shortuuid,
    'sku': product_id,
    'name': product_name,
    'category': sub_category,
    'image': image_url,
    'link': product_url,
    'source': 'klikindomaret',
    'created_at': datetime_today
}

prices = {
    'id': shortuuid,
    'items_id': FK to items,
    'price': integer,
    'description': "",
    'created_at': datetime_today
}

discounts = {
    'id': shortuuid,
    'items_id': FK to items,
    'discount_price': integer,
    'original_price': integer,
    'percentage': "Hemat 20%",
    'description': "",
    'created_at': datetime_today
}
```

---

## Playwright Browser Findings

### Successful Actions
- ✅ Navigate to homepage
- ✅ Take screenshot
- ✅ Extract category names via JavaScript
- ✅ Identify mega menu structure

### Failed Actions
- ❌ Navigate to `/xpress/category/*` pages (timeout after 60s)
- ❌ Navigate to `/category/*` pages (timeout after 60s)

### Possible Reasons for Timeout
1. Bot detection (Cloudflare, WAF)
2. Requires user interaction (click, scroll)
3. Requires cookies/session
4. Geo-blocking

---

## Recommended Solution

### Option A: Update BeautifulSoup Scraper (Quick Fix)
**Pros:**
- Minimal code changes
- Faster execution
- Lower resource usage

**Cons:**
- Won't work if site is JavaScript-heavy
- Limited by static HTML
- May hit bot detection

**Effort:** 2-4 hours

---

### Option B: Migrate to Playwright (Robust Solution)
**Pros:**
- Handles JavaScript rendering
- Can interact with dynamic elements
- Better bot evasion (real browser)
- Easier debugging (screenshots, videos)

**Cons:**
- Slower execution
- Higher resource usage
- More complex code

**Effort:** 4-8 hours

---

### Option C: Hybrid Approach (Recommended)
**Pros:**
- Use Playwright to discover structure
- Extract category URLs with Playwright
- Use requests/BeautifulSoup for product pages (if static)
- Fallback to Playwright if detection occurs

**Cons:**
- More complex architecture
- Need to maintain both methods

**Effort:** 6-10 hours

---

## Implementation Plan

### Phase 1: Investigation (CURRENT)
- [x] Analyze current code
- [x] Test homepage with Playwright
- [x] Identify structure changes
- [ ] Test product listing page access
- [ ] Verify if pages are static or dynamic

### Phase 2: Prototype
- [ ] Create new category extraction logic
- [ ] Test product page scraping
- [ ] Verify pagination works
- [ ] Test with 1-2 categories only

### Phase 3: Full Implementation
- [ ] Update `getDataCategories()` function
- [ ] Add retry logic with exponential backoff
- [ ] Add proper error logging
- [ ] Add progress tracking
- [ ] Test with all categories

### Phase 4: Testing
- [ ] Run scraper in dry-run mode
- [ ] Verify database insertions
- [ ] Check for duplicates
- [ ] Validate price/discount accuracy
- [ ] Monitor for rate limiting

### Phase 5: Deployment
- [ ] Update Docker containers
- [ ] Update schedule in `config.py`
- [ ] Deploy to production
- [ ] Monitor first runs

---

## Technical Recommendations

### 1. Use Playwright for Category Discovery
```python
from playwright.sync_api import sync_playwright

def get_categories_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.klikindomaret.com')

        # Click category menu
        page.click('.mega-menu')

        # Extract links
        links = page.evaluate('''() => {
            const submenu = document.querySelector('.submenu-list-wrap');
            const links = submenu.querySelectorAll('a');
            return Array.from(links).map(a => ({
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }));
        }''')

        browser.close()
        return links
```

### 2. Add Request Headers
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.klikindomaret.com/',
}
```

### 3. Add Delays
```python
import time
import random

def random_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))
```

### 4. Better Error Handling
```python
import traceback

try:
    # scraping code
except Exception as e:
    logging.error(f"Error scraping {category_url}: {str(e)}")
    logging.error(traceback.format_exc())
    # Save error to database or file
```

---

## Questions to Answer Before Proceeding

1. **Do product listing pages load with JavaScript?**
   - Need to test with Playwright
   - Compare requests HTML vs browser HTML

2. **Are there API endpoints we can use?**
   - Check Network tab for XHR/Fetch requests
   - Might be easier than HTML parsing

3. **What's the rate limit?**
   - Test with increasing request frequency
   - Add exponential backoff if needed

4. **Do we need authentication?**
   - Test if logged-in users see different data
   - Check if prices/availability differ

---

## Next Steps

**Immediate Actions:**
1. Test product listing page with Playwright
2. Check if page content is static or dynamic
3. Inspect Network tab for API endpoints
4. Create minimal working prototype for 1 category

**Decision Point:**
Based on findings, choose:
- Option A (BeautifulSoup) if pages are static
- Option B (Playwright) if pages are dynamic
- Option C (Hybrid) if mixed

---

## References

- **Current Code:** `src/crawler/klikindomaret.py`
- **Database Schema:** `src/db.py`
- **Utilities:** `src/util.py` (cleanUpCurrency)
- **Screenshot:** `.playwright-mcp/klikindomaret_homepage.png`

---

**Created:** 2025-11-11
**Last Updated:** 2025-11-11
**Playwright Browser Test:** ✅ Homepage accessible, category pages timeout
**Recommendation:** Investigate with Network tab inspection before choosing implementation approach
