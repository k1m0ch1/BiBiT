# BiBiT - Context Summary

## What is BiBiT?
**BiBiT** (Indonesian: "sprout") is a grocery price tracking bot that monitors Indonesian e-commerce platforms (Yogya Online, Klik Indomaret, Alfagift), tracks historical prices, and provides search/comparison APIs.

## Tech Stack
- **Python 3.8** | FastAPI + Uvicorn | SQLite3 + SQLlex
- **Scraping:** BeautifulSoup4, requests, lxml
- **Data:** Pydantic v2, pytz (Asia/Jakarta timezone)
- **Tools:** schedule, tqdm, shortuuid, loguru, flake8
- **Infra:** Docker (API + crawler containers), Pipenv

## Architecture
```
src/
├── main.py              # CLI orchestrator, scheduler, FastAPI init
├── config.py            # Schedules, headers, env config
├── db.py                # SQLite wrapper (indiemart.db, crawl.db)
├── models.py            # Pydantic validation models
├── util.py              # Currency parsing, delays, health reporting
├── crawler/             # Vendor-specific scrapers
│   ├── yogyaonline.py   # HTML scraping, JS object parsing
│   ├── klikindomaret.py # Multi-level categories, form pagination
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
   - klikindomaret.com (HTML scraping)
   - alfagift.id (REST API)
2. **Monitoring:** SteinDB (spreadsheet API for health checks)

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
