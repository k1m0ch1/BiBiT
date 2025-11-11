# Functional Context

## Project Purpose
**BiBiT** (Indonesian: "sprout") is a grocery price tracking and notification bot for Indonesian e-commerce platforms. It monitors prices across multiple vendors, tracks historical changes, and provides comparison/search APIs.

## Core Domains

### 1. Price Scraping & Monitoring
**Module:** `src/crawler/`

#### Supported Vendors:
1. **Yogya Online** (`yogyaonline.py`)
   - Category-based product listings
   - JavaScript object parsing (`var dl4Objects`)
   - Dynamic pagination (up to 640 items per page)
   - Extracts promotions and discounts

2. **Klik Indomaret** (`klikindomaret.py`)
   - Multi-level category navigation
   - Form-based pagination
   - Shipping info extraction
   - Discount label parsing

3. **Alfagift** (`alfagift.py`)
   - REST API-based (no HTML parsing)
   - 3-level category hierarchy
   - Direct JSON responses
   - Uses device fingerprint headers

#### Common Crawler Pattern:
```
1. Fetch categories
2. Iterate through products
3. Extract: SKU, name, price, image, link
4. Check if item exists (by SKU or name)
5. Insert/retrieve item ID
6. Check if today's price exists
7. Insert price record if new
8. Check if discount exists today
9. Insert discount if applicable
10. Log metrics (newItems, newPrices, newDiscounts)
11. Report health to SteinDB
```

### 2. Product Search API
**Module:** `src/routes/root.py`

**Endpoints:**
- `POST /search` - Search products by name
  - Filters: source vendor, price threshold (>Rp 99)
  - Returns: items with current day prices
  - Grouping: by item name, ordered by price ASC

- `GET /` - API status check
- `GET /stat` - Statistics (placeholder)
- `POST /sama` - Mark items as similar (commented out)

### 3. Shopping List Management
**Module:** `src/routes/belanja.py`

**Features:**
- Create shopping lists with secret keys
- Add items with optional custom pricing
- Retrieve lists with current market prices
- Update custom prices per item
- Soft-delete items/lists
- Secret key-based authorization

**Endpoints (most commented out):**
- `POST /belanja/new` - Create list
- `POST /belanja/{id}` - Add item
- `GET /belanja/{id}` - Retrieve list (active)
- `PUT /belanja/{id}` - Update prices
- `DELETE /belanja/{id}` - Remove items/lists

**Use Case:** Track personal shopping lists, compare custom prices with current market prices.

### 4. Data Models
**Module:** `src/models.py`

#### Core Entities:
- **Item** - Product catalog entry
  - id, sku, name, category, image, link, source, created_at

- **Price** - Historical pricing
  - id, items_id (FK), price, description, created_at

- **Discount** - Promotional pricing
  - id, items_id (FK), discount_price, original_price, percentage, description, created_at

- **Belanja (Shopping)** - User lists
  - belanja_link (list container with secret key)
  - belanja (list items with custom prices)

- **Item_Item** - Similarity tracking (proposed feature)
  - Links items that are the same product across vendors

## Data Flows

### Scheduled Scraping Flow
```
Schedule triggers (00:30, 06:45, 16:45)
  → main.py orchestrates crawler
  → Crawler fetches vendor data
  → Parse products
  → Upsert items
  → Insert prices (daily granularity)
  → Insert discounts (if applicable)
  → Save JSON backup to data/
  → Report metrics to SteinDB
```

### Search Flow
```
User → POST /search {name, source?}
  → SQL LIKE query on items.name
  → JOIN prices WHERE date = today
  → Filter by source (optional)
  → Group by name, ORDER BY price ASC
  → Filter price > Rp 99
  → Return JSON results
```

### Shopping List Flow
```
Create list → Generate secret key
  → Add items → Store items_id + custom_price
  → Retrieve list → JOIN items + today's prices
  → Compare custom_price vs market price
  → Return formatted list
```

## Key Workflows

### 1. New Vendor Integration
1. Create `src/crawler/{vendor}.py`
2. Implement `getCategories()` and scraping logic
3. Use `DBAPI` to insert items/prices/discounts
4. Follow deduplication pattern (check by SKU/name)
5. Add vendor to `main.py` orchestration
6. Update Docker build args

### 2. Price Change Detection
- Current: Passive (query by date)
- Potential: Compare today's price with yesterday's
- Notification: Prime time (09:00, 19:00) per config.py

### 3. Health Monitoring
- After each scrape: POST metrics to SteinDB
- Metrics: newItems, newPrices, newDiscounts counts
- Timezone: Asia/Jakarta

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `main.py` | CLI, scheduler, app initialization |
| `db.py` | Database connections, schema, indexing |
| `models.py` | Pydantic validation models |
| `config.py` | Environment config, schedules, headers |
| `util.py` | Currency parsing, delays, health reporting |
| `crawler/*.py` | Vendor-specific scraping logic |
| `routes/*.py` | FastAPI endpoint handlers |

## Feature Status

### Active Features:
- ✅ Multi-vendor price scraping
- ✅ Historical price storage
- ✅ Product search API
- ✅ Shopping list retrieval
- ✅ Health monitoring

### Inactive/Partial Features:
- ⚠️ Shopping list CRUD (mostly commented out)
- ⚠️ Item similarity detection (commented out)
- ⚠️ Statistics endpoint (placeholder)
- ⚠️ Price change notifications (config exists, no implementation)

## Data Retention
- **Prices:** Daily granularity, indefinite retention
- **Discounts:** Daily granularity, indefinite retention
- **Items:** Permanent (no deletion)
- **Shopping Lists:** Soft-delete pattern (deleted_at field)
- **Backups:** JSON exports per scrape run

## Security Considerations
- Shopping list access via secret_key
- No authentication on search API (public)
- SteinDB credentials via environment variables
- No rate limiting visible
- User-Agent rotation in util.py (anti-scraping)
