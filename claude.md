# BiBiT - Context Summary

## What is BiBiT?
**BiBiT** (Indonesian: "sprout") is a grocery price tracking bot that monitors Indonesian e-commerce platforms (Yogya Online, Klik Indomaret, Alfagift), tracks historical prices, and provides search/comparison APIs.

## Tech Stack
- **Python 3.12** | FastAPI + Uvicorn | SQLite3 + SQLlex
- **Scraping:** BeautifulSoup4, cloudscraper, requests, lxml
- **Data:** Pydantic v2, pytz (Asia/Jakarta timezone)
- **Tools:** schedule, tqdm, shortuuid, loguru, flake8
- **Infra:** Docker (API + crawler containers), uv (package manager)

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
│   └── klikindomaret_api.py  # Klik Indomaret API (with cloudscraper)
├── crawler/             # Vendor-specific scrapers
│   ├── yogyaonline.py   # HTML scraping, JS object parsing
│   ├── klikindomaret.py # ⚠️ BROKEN - needs replacement with API version
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
- **Linter:** flake8 (enforced)
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
- `Dockerfile.API` - Port 8000, runs FastAPI
- `Dockerfile.crawler` - Per-vendor scraper
- Build args: `PLATFORM`, `STEINDB_URL`, `STEINDB_USERNAME`, `STEINDB_PASSWORD`

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

**Files Created:**
1. `.context/plan/96g2-2025-11-11-klikindomaret-api-scraping.md` - Full API implementation plan
2. `.context/plan/96g2-2025-11-11-CRITICAL-BOT-DETECTION-ISSUE.md` - Bot detection documentation
3. `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md` - **Complete solution documentation**
4. `src/api_client/klikindomaret_api.py` - API client (✅ working with cloudscraper)
5. `src/test/test_klikindomaret_api.py` - Test script (archived)

**Status:**
- ✅ Phase 1: API endpoints identified
- ✅ Phase 2: Test scripts and API client created
- ✅ Phase 3: **COMPLETE** - Cloudscraper installed and working!
- ✅ Phase 4: Python upgraded to 3.12, compatibility verified
- ⏭️ Phase 5: Backup old scraper (next step)
- ⏭️ Phase 6: Replace with API-based production scraper (next step)

### Old Scraper Issues

The current `src/crawler/klikindomaret.py` is **broken** because:
1. HTML structure changed completely (classes renamed)
2. URL format changed: `/category/...` → `/xpress/category/...`
3. No more `clickMenu`, `nd-kategori` classes
4. Now uses Tailwind CSS
5. JavaScript-heavy rendering

**Old selectors that don't work:**
```python
# ❌ This doesn't exist anymore:
categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
```

### Advantages of API Approach

| Aspect | Old (HTML) | New (API) |
|--------|------------|-----------|
| Speed | Slow | Fast |
| Reliability | Breaks often | Stable |
| Data Quality | Messy | Clean JSON |
| Pagination | Complex | Simple |
| Maintenance | High | Low |

### Next Steps (Plan 96g2 Continuation)

**Phase 5 - Backup Old Scraper:**
```bash
cp src/crawler/klikindomaret.py src/crawler/klikindomaret_old.py
```

**Phase 6 - Create API-Based Production Scraper:**
1. Create new `src/crawler/klikindomaret.py` using API client
2. Follow pattern from `src/crawler/alfagift.py` (also uses REST API)
3. Import: `from src.api_client.klikindomaret_api import KlikIndomaretAPI`
4. Map API fields to BiBiT database schema (see field mapping table above)
5. Implement deduplication logic (check by `plu` or `productName`)
6. Add daily price/discount checks

**Phase 7 - Testing:**
1. Test scrape on 1-2 categories
2. Verify database insertions
3. Check JSON backups
4. Verify SteinDB metrics reporting

**Phase 8 - Deployment:**
1. Update Docker build
2. Test in staging
3. Deploy to production
4. Monitor for issues

### References

- **Original Plan:** `.context/plan/96g2-2025-11-11-klikindomaret-api-scraping.md`
- **Bot Detection Issue:** `.context/plan/96g2-2025-11-11-CRITICAL-BOT-DETECTION-ISSUE.md`
- **✨ Complete Solution Doc:** `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md`
- **API Client:** `src/api_client/klikindomaret_api.py`
- **Tests (archived):** `src/test/test_klikindomaret_api.py`

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
