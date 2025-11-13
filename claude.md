# BiBiT - Context Summary

## What is BiBiT?
**BiBiT** (Indonesian: "sprout") is a grocery price tracking bot that monitors Indonesian e-commerce platforms (Yogya Online, Klik Indomaret, Alfagift), tracks historical prices, and provides search/comparison APIs.

## Tech Stack
- **Python 3.12** | FastAPI + Uvicorn | SQLite3 + SQLlex
- **Scraping:** BeautifulSoup4, cloudscraper, requests, lxml
- **Data:** Pydantic v2, pytz (Asia/Jakarta timezone)
- **Tools:** schedule, tqdm, shortuuid, loguru
- **Linting:** Ruff (via GitHub Actions)
- **Infra:** Docker (API + crawler containers), uv (package manager)

## Current Status (2025-11-13)
✅ **All vendors operational with cloudscraper:**
- **Yogya Online** - ✅ **IMPROVED! Infinite scroll with AJAX POST (cloudscraper + rate limiting)**
- **Klik Indomaret** - ✅ **NEW! REST API (cloudscraper)** - Fully functional
- **Alfagift** - REST API (requests)

✅ **Infrastructure:**
- Python 3.12 across all environments
- CI/CD pipeline updated and passing
- Docker containers ready for deployment
- All linting errors fixed

## Check for Reference
- `.context/function.md` for the function of the services
- `.context/standard.md` for the standarization of how it work
- `.context/technology.d` for the technology that has been used

## Architecture
```
src/
├── main.py              # CLI orchestrator, scheduler, FastAPI init
├── config.py            # Schedules, headers, env config
├── db.py                # SQLite wrapper (indiemart.db, crawl.db)
├── models.py            # Pydantic validation models
├── util.py              # Currency parsing, delays, health reporting
├── api_client/          # API clients for REST-based vendors
│   ├── __init__.py      # Package initialization
│   └── klikindomaret_api.py  # Klik Indomaret API (with cloudscraper)
├── crawler/             # Vendor-specific scrapers
│   ├── yogyaonline.py   # ✅ Infinite scroll AJAX (with cloudscraper)
│   ├── yogyaonline_old.py    # Archived version without rate limiting
│   ├── yogyaonline_old_pagination.py  # Archived broken pagination version
│   ├── klikindomaret.py # ✅ REST API-based (with cloudscraper)
│   ├── klikindomaret_old.py  # Archived broken HTML scraper
│   └── alfagift.py      # REST API-based (JSON responses)
└── routes/              # FastAPI endpoints
    ├── root.py          # Product search API
    └── belanja.py       # Shopping list management (mostly disabled)
```

## Database Schema (SQLite)
```
items:      id, sku, name, category, image, link, source, created_at
prices:     id, items_id (FK), price, description, created_at
discounts:  id, items_id (FK), discount_price, original_price, percentage, description, created_at
belanja_link: id, status, secret_key, created_at, updated_at, deleted_at
belanja:    id, belanja_link_id (FK), items_id (FK), custom_price, created_at, updated_at, deleted_at
item_item:  id, item_id (FK), with_item_id (FK), status, created_at, updated_at
```

**Patterns:**
- TEXT primary keys (shortuuid)
- Daily granularity for prices/discounts
- Soft deletes (deleted_at field)
- Timezone: Asia/Jakarta
- Date format: `YYYY-MM-DD HH:MM:SS`
- Indexes on all FKs, names, SKUs, sources, dates

## Core Flows

### 1. Scraping (00:30, 06:45, 16:45)
```
Scheduler → Crawler → Fetch categories → Parse products
  → Check if item exists (by SKU/name)
  → Upsert item
  → Check if today's price exists
  → Insert price if new
  → Check if discount exists today
  → Insert discount if applicable
  → Save JSON backup (data/{vendor}/{type}/{date}.json)
  → Report metrics to SteinDB
```

### 2. Search API (POST /search)
```
User query → SQL LIKE on items.name
  → JOIN prices WHERE created_at LIKE '{today}%'
  → Filter by source (optional)
  → GROUP BY name, ORDER BY price ASC
  → Filter price > Rp 99
  → Return JSON
```

### 3. Shopping Lists (belanja)
```
Create list → Generate secret_key
  → Add items with custom_price
  → Retrieve → JOIN items + today's prices
  → Compare custom vs market price
  → Soft delete via deleted_at
```

## Key APIs
- `POST /search` - Product search by name (active)
- `GET /` - API status (active)
- `GET /belanja/{id}` - Retrieve shopping list (active)
- `POST /belanja/new`, `POST /belanja/{id}`, `PUT /belanja/{id}`, `DELETE /belanja/{id}` - CRUD (commented out)
- `GET /stat`, `POST /sama` - Placeholders

## Standards (KISS & DRY)

### Code Quality
- **Linter:** Ruff (enforced via GitHub Actions), flake8 config in pyproject.toml
- **CI/CD:** GitHub Actions (`.github/workflows/main.yml`) - Python 3.12
- **Max line length:** 120 characters
- **Tests:** unittest (minimal - only alfagift_test.py)
- **Naming:**
  - Files: `lowercase_underscore.py`
  - Functions: `camelCase` (legacy) → prefer `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPERCASE`
  - DB tables: `snake_case`

### Git Conventions
- **Commits:** `{type}: {description}`
  - Types: `fix:`, `add:`, `change:`
- **Branch:** `master` (main branch)
- **Recent changes:**
  - Yogya Online scraper improvements: cloudscraper + rate limiting (2025-11-13)
  - Klik Indomaret API-based scraper implementation (2025-11-13)
  - Updated CI/CD pipeline to Python 3.12 (2025-11-13)
  - Fixed all Ruff linting errors (2025-11-13)
  - Updated Dockerfile.crawler for Python 3.12 + cloudscraper (2025-11-13)
  - Python 3.12 upgrade & cloudscraper integration (2025-11-12)
  - Klik Indomaret API client implementation (2025-11-12)
  - Migrated from ORM to raw SQL (commit: dd5a133)
  - Added metric recording (commit: 9cd9442)
  - Fixed linting (commit: 9ae395e)

### Database Rules
- Always check existence before insert (deduplication)
- Use `LIKE '{date}%'` for daily queries
- Soft delete user data (never hard delete)
- Index all FKs and frequently queried fields
- Store dates in Asia/Jakarta timezone

### API Rules
- Validate all input with Pydantic models
- Use secret keys for sensitive operations
- Return standard HTTP status codes
- POST for search (allows complex filters)

### Docker
- `Dockerfile.API` - Port 8000, runs FastAPI (Python 3.12)
- `Dockerfile.crawler` - Per-vendor scraper (Python 3.12-slim)
- Build args: `PLATFORM`, `STEINDB_URL`, `STEINDB_USERNAME`, `STEINDB_PASSWORD`
- Default PLATFORM: `klikindomaret` (for easy testing)

### DRY Violations to Address
- Currency parsing → use `util.cleanUpCurrency()`
- Date formatting → centralize datetime helpers
- Deduplication logic → extract to shared method
- Insert patterns → create generic `upsert()` function

### KISS Principles
- ✅ Flat structure (max 2 levels)
- ✅ One crawler per file
- ✅ Direct SQL over heavy ORM
- ❌ Delete commented-out code or use feature flags
- ❌ Clean up duplicate database files (.copy)

## Environment Variables
- `STEINDB_URL` - Health monitoring endpoint
- `STEINDB_USERNAME`, `STEINDB_PASSWORD` - SteinDB auth
- `DATA_DIR` - Data file location override
- `PLATFORM` - Target crawler (yogyaonline|klikindomaret|alfagift)

## External Integrations
1. **E-commerce Sites:**
   - yogyaonline.co.id (HTML scraping)
   - klikindomaret.com (✅ **REST API via cloudscraper** - bot detection bypassed!)
   - alfagift.id (REST API)
2. **Monitoring:** SteinDB (spreadsheet API for health checks)

---

## ✅ Klik Indomaret API Discovery & Bot Detection [RESOLVED] (2025-11-11 → 2025-11-12)

### Discovery Summary
**Found:** Klik Indomaret uses a REST API at `https://ap-mc.klikindomaret.com` for all product/category data (discovered via Playwright network inspection).

**Status:** ✅ **RESOLVED** (2025-11-12) - Cloudscraper successfully bypasses Cloudflare bot detection!

### API Endpoints Discovered

#### Base URL
```
https://ap-mc.klikindomaret.com
```

#### 1. Category Metadata API
```
GET /assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta
```

**Parameters:**
- `storeCode=TJKT` (Jakarta store)
- `latitude=-6.1763897`
- `longitude=106.82667`
- `mode=DELIVERY`
- `districtId=141100100`

**Response:** JSON with 9 categories (Perawatan Diri, Makanan, Dapur & Bahan Masakan, Minuman, Ibu & Anak, Kesehatan & Kebersihan, Kebutuhan Rumah, Makanan Hewan, Lainnya)

#### 2. Product Search API
```
GET /assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result
```

**Additional Parameters:**
- `page=0` (0-indexed pagination)
- `size=50` (products per page)
- `categories=` (category ID filter, empty for all)

**Response:** JSON with product data including id, name, sku, mainImage, prices (with discounts)

### Critical Issue: Bot Detection

**Problem:** API has Cloudflare protection that blocks Python HTTP requests:
```
403 Client Error: Forbidden
```

**What Works:**
- ✅ Playwright browser (tested, works)
- ✅ Real browser requests
- ✅ MCP Playwright tool

**What Doesn't Work:**
- ❌ Python `requests` library
- ❌ Direct HTTP calls
- ❌ Current scraper approach

---

## ✅ SOLUTION IMPLEMENTED (2025-11-12)

### Python 3.12 Upgrade & Cloudscraper Integration

**Status:** ✅ **COMPLETE** - Bot detection bypassed, API client fully functional!

### What We Did

1. **Upgraded Python:** 3.8.1 → 3.12 (required for cloudscraper)
   - Analyzed entire codebase for breaking changes
   - Confirmed all dependencies compatible
   - Updated `pyproject.toml`

2. **Installed Cloudscraper:**
   ```bash
   uv add cloudscraper
   ```

3. **Updated API Client:**
   - Replaced `requests.Session()` with `cloudscraper.create_scraper()`
   - Fixed response structure handling (nested `data.content[]`)
   - Fixed field name mapping (`productName`, `plu`, `productId`)

### Test Results

✅ **No more 403 Forbidden errors!**

```
Found: 9 categories
Retrieved: 5,233 products in "Perawatan Diri" category
Sample product:
  - Name: Sunlight Pencuci Piring Berry & Lime 675g
  - PLU/SKU: 20139948
  - Price: Rp 13,900
```

### API Response Structure (Actual)

**Categories Response:**
```json
{
  "data": [
    {
      "id": 345,
      "name": "Perawatan Diri",
      "level": 1,
      "permalink": "perawatan-diri",
      "imageUrl": "...",
      "categories": [...]
    }
  ]
}
```

**Products Response:**
```json
{
  "data": {
    "content": [
      {
        "productId": 21494587,
        "plu": "20139948",
        "productName": "Sunlight Pencuci Piring...",
        "price": 13900,
        "finalPrice": null,
        "discountText": null,
        "imageUrl": "...",
        "permalink": "..."
      }
    ],
    "totalElements": 5233,
    "totalPages": 105
  }
}
```

### Key Field Mappings

| BiBiT Schema | Klik Indomaret API |
|--------------|-------------------|
| `id` | `productId` |
| `sku` | `plu` |
| `name` | `productName` |
| `image` | `imageUrl` |
| `price` | `price` (direct field, not array) |
| `link` | `permalink` (needs prefix) |

### Documentation

📄 **Full Documentation:** `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md`

Contains:
- Complete Python 3.12 compatibility analysis
- Cloudscraper installation guide
- API structure documentation
- Usage examples
- Field mapping reference
- Integration guide for BiBiT database

### Solutions (Archive - For Reference)

#### Option 1: cloudscraper (Recommended)
```bash
uv add cloudscraper
```

**Pros:** Drop-in replacement for requests, fast, lightweight
**Code change:** Replace `requests.Session()` with `cloudscraper.create_scraper()`

#### Option 2: playwright
```bash
uv add playwright
playwright install chromium
```

**Pros:** Confirmed working, handles JS rendering
**Cons:** Slower, higher resource usage

#### Option 3: curl_cffi
```bash
uv add curl_cffi
```

**Pros:** Fast Cloudflare bypass
**Cons:** Less popular, may need C compiler

### Current Implementation Status

**Files Created/Modified:**
1. `.context/plan/96g2-2025-11-11-klikindomaret-api-scraping.md` - Full API implementation plan
2. `.context/plan/96g2-2025-11-11-CRITICAL-BOT-DETECTION-ISSUE.md` - Bot detection documentation
3. `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md` - Complete solution documentation
4. `src/api_client/__init__.py` - Package initialization (✅ created 2025-11-13)
5. `src/api_client/klikindomaret_api.py` - API client (✅ working with cloudscraper)
6. `src/crawler/klikindomaret.py` - **NEW API-based scraper** (✅ complete 2025-11-13)
7. `src/crawler/klikindomaret_old.py` - Archived broken HTML scraper
8. `Dockerfile.crawler` - Updated to Python 3.12 + cloudscraper (✅ 2025-11-13)
9. `.github/workflows/main.yml` - Updated to Python 3.12 (✅ 2025-11-13)
10. `requirements.txt` - Added cloudscraper dependency (✅ 2025-11-13)

**Status:**
- ✅ Phase 1: API endpoints identified
- ✅ Phase 2: Test scripts and API client created
- ✅ Phase 3: Cloudscraper installed and working
- ✅ Phase 4: Python upgraded to 3.12, compatibility verified
- ✅ Phase 5: Old scraper backed up to klikindomaret_old.py
- ✅ Phase 6: **NEW API-based production scraper implemented**
- ✅ Phase 7: All Ruff linting errors fixed
- ✅ Phase 8: **READY FOR DEPLOYMENT**

### Old Scraper Issues (Archived)

The archived `src/crawler/klikindomaret_old.py` was **broken** because:
1. HTML structure changed completely (classes renamed)
2. URL format changed: `/category/...` → `/xpress/category/...`
3. No more `clickMenu`, `nd-kategori` classes
4. Now uses Tailwind CSS
5. JavaScript-heavy rendering

**Old selectors that didn't work:**
```python
# ❌ This doesn't exist anymore:
categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
```

**Solution:** The new `src/crawler/klikindomaret.py` uses the REST API instead of HTML scraping.

### Advantages of API Approach

| Aspect | Old (HTML) | New (API) |
|--------|------------|-----------|
| Speed | Slow | Fast |
| Reliability | Breaks often | Stable |
| Data Quality | Messy | Clean JSON |
| Pagination | Complex | Simple |
| Maintenance | High | Low |

### Implementation Summary (Completed 2025-11-13)

**What Was Built:**

1. **API Client** (`src/api_client/klikindomaret_api.py`):
   - Uses cloudscraper to bypass Cloudflare bot detection
   - Fetches categories and products via REST API
   - Handles pagination automatically
   - Rate limiting built-in

2. **New Scraper** (`src/crawler/klikindomaret.py`):
   - Uses `KlikIndomaretAPI` client
   - Follows same pattern as `alfagift.py`
   - Proper field mapping (productId→id, plu→sku, etc.)
   - Deduplication by PLU/name
   - Daily price/discount tracking
   - Error handling per category

3. **Infrastructure Updates:**
   - Python 3.12 across all environments
   - Cloudscraper added to dependencies
   - Dockerfile.crawler updated
   - CI/CD pipeline updated
   - All linting errors fixed

**Testing & Deployment:**
```bash
# Test locally with Docker
docker build -f Dockerfile.crawler -t bibit-crawler-test .
docker run --rm -e PLATFORM=klikindomaret bibit-crawler-test

# Deploy to production
docker build -f Dockerfile.crawler \
  --build-arg PLATFORM=klikindomaret \
  --build-arg STEINDB_URL=<url> \
  --build-arg STEINDB_USERNAME=<user> \
  --build-arg STEINDB_PASSWORD=<pass> \
  -t bibit-crawler-klikindomaret .
```

### Implementation References

- **Original Plan:** `.context/plan/96g2-2025-11-11-klikindomaret-api-scraping.md`
- **Bot Detection Issue:** `.context/plan/96g2-2025-11-11-CRITICAL-BOT-DETECTION-ISSUE.md`
- **Complete Solution Doc:** `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md`
- **API Client:** `src/api_client/klikindomaret_api.py:1`
- **Klik Indomaret Scraper:** `src/crawler/klikindomaret.py:1`
- **Klik Indomaret Old:** `src/crawler/klikindomaret_old.py:1`
- **Yogya Online Scraper:** `src/crawler/yogyaonline.py:1`
- **Yogya Online Old:** `src/crawler/yogyaonline_old.py:1`

---

## ✅ Yogya Online Scraper - Infinite Scroll Fix (2025-11-13)

### Summary
Fixed the Yogya Online scraper to use **infinite scroll AJAX POST requests** instead of broken pagination. The old pagination method (`?p={page_num}`) only fetched ~2 pages (~28 products), while the new method fetches **all products** (e.g., 208 products from Sayur-Sayuran category).

### The Problem

**Old Approach (BROKEN):**
- ❌ Used URL pagination: `?p={page_num}&product_list_limit=640`
- ❌ Only scraped 2 pages per category (~28 products)
- ❌ Missed hundreds of products due to infinite scroll

**Discovery:**
- Website uses **infinite scroll** with AJAX POST to `/load-more-product`
- Payload: `{current_page: N, brands: [], category_id: ID}`
- Requires **XSRF token** from cookie
- Response: JSON with HTML fragment + pagination metadata

### What Was Fixed

**After:**
- ✅ **AJAX POST requests** to `/load-more-product` endpoint
- ✅ **XSRF token** extraction from cookies
- ✅ **Category ID** auto-detection from `data-category-id` attribute
- ✅ **All pages** fetched (e.g., 16 pages = 208 products)
- ✅ Rate limiting: 1.0-2.5 seconds between requests
- ✅ Reuses cloudscraper session across all requests
- ✅ Better error handling with try/except blocks
- ✅ Detailed logging for each page fetch

### Key Features

1. **Infinite Scroll AJAX:**
   ```python
   # Extract XSRF token from cookie
   xsrf_token = scraper.cookies.get('XSRF-TOKEN')
   xsrf_token = urllib.parse.unquote(xsrf_token)

   # POST request to load-more-product endpoint
   headers['X-XSRF-TOKEN'] = xsrf_token
   response = scraper.post(url, json=payload, headers=headers)

   # Parse JSON response
   data = response.json()
   html_content = data.get('html', '')
   total_pages = data.get('total_page', 0)
   ```

2. **Category ID Auto-Detection:**
   ```python
   # Extract from data-category-id attribute
   cat_elem = parser.find(attrs={'data-category-id': True})
   category_id = int(cat_elem['data-category-id'])
   ```

3. **Fixed HTML Parsing:**
   - Changed from `<a class="product-name">` to `<div class="product-name">`
   - Extract `onclick` from div instead of link
   - Get product link from `<a class="product-image-container">`

4. **Modular Functions:**
   - `scrape_category()` - Main category scraping logic
   - `_fetch_products_page()` - Fetch single page via AJAX
   - `_extract_category_id()` - Auto-detect category ID
   - `_extract_product_from_html()` - Parse product HTML
   - `_save_product_to_db()` - Database operations

### Test Results

**Sayur-Sayuran Category:**
- Old scraper: ~28 products (2 pages)
- New scraper: **208 products (16 pages)** ✅
- All products from infinite scroll now captured!

### Database Format
Same format as **alfagift** and **klikindomaret:**
- ✅ Items: sku, name, category, image, link, source
- ✅ Prices: daily tracking with deduplication
- ✅ Discounts: with percentage calculation

### Files Modified
- `src/crawler/yogyaonline.py` - **Complete rewrite for infinite scroll**
- `src/crawler/yogyaonline_old.py` - Archived version with rate limiting
- `src/crawler/yogyaonline_old_pagination.py` - Archived broken pagination version

---

## Feature Status
- ✅ Multi-vendor scraping
- ✅ Historical price storage
- ✅ Product search API
- ✅ Shopping list retrieval
- ⚠️ Shopping list CRUD (mostly commented out)
- ⚠️ Item similarity detection (commented out)
- ⚠️ Price change notifications (config exists, no implementation)

## Common Tasks

### Add New Vendor
1. Create `src/crawler/{vendor}.py`
2. Implement `getCategories()` and scraping logic
3. Use `DBAPI` for items/prices/discounts
4. Follow deduplication pattern (check by SKU/name)
5. Add to `main.py` orchestration
6. Add tests in `src/test/crawler/{vendor}_test.py`
7. Update Docker build args

### Add New API Endpoint
1. Add route to `src/routes/{domain}.py`
2. Create Pydantic models in `src/models.py`
3. Use `DBAPI` for queries
4. Return JSON responses
5. Add to router in file with `@router.get/post/put/delete`

### Database Migration
1. Update schema in `db.py`
2. Add migration SQL (manual - no ORM migrations)
3. Create indexes for new fields
4. Update models in `models.py`
5. Test with fresh database

### Run Locally
```bash
# Install dependencies
pipenv install

# Run API server
python src/main.py web.api

# Run scraper (specific vendor)
python src/main.py --target yogyaonline do.scrap

# Run tests
python -m unittest discover
```

### Docker Build
```bash
# API container
docker build -f Dockerfile.API -t bibit-api .

# Crawler container
docker build -f Dockerfile.crawler \
  --build-arg PLATFORM=yogyaonline \
  --build-arg STEINDB_URL=https://... \
  -t bibit-crawler .
```

## Key Files Reference
- `src/main.py:1` - Entry point
- `src/db.py:1` - Database initialization
- `src/config.py:1` - Configuration constants
- `src/util.py:1` - Shared utilities
- `src/crawler/yogyaonline.py:1` - Yogya scraper
- `src/crawler/klikindomaret.py:1` - Indomaret scraper
- `src/crawler/alfagift.py:1` - Alfagift scraper
- `src/routes/root.py:1` - Search API
- `src/routes/belanja.py:1` - Shopping lists
- `requirements.txt:1` - Python dependencies
