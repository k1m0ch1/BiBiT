# Project Standards

## Code Quality & Linting

### Linter Configuration
- **Tool:** flake8
- **Plugins:** pycodestyle, pyflakes, mccabe
- **Enforcement:** Active (recent commit: "fix: lint error" - 9ae395e)
- **Pre-commit:** Not configured (manual linting)

### Testing Standards
- **Framework:** unittest (Python standard library)
- **Coverage:** Minimal (only `src/test/crawler/alfagift_test.py` exists)
- **Test Pattern:**
  ```python
  class Test{Module}(unittest.TestCase):
      def test_{feature}(self):
          # Assertions here
  ```
- **Run Tests:** `python -m unittest discover`
- **Required:** Tests for new crawlers (validate API availability, category fetching)

## Naming Conventions

### Files & Directories
- **Python files:** `lowercase_underscore.py`
- **Directories:** `lowercase` (e.g., `crawler/`, `routes/`)
- **Data files:** `{vendor}/{type}/{YYYY-MM-DD}.json`

### Code Naming
- **Functions:** `camelCase` for entry points (e.g., `getCategories`, `getDataCategories`)
- **Variables:** Mixed `camelCase` and `snake_case` (inconsistent - prefer `snake_case`)
- **Constants:** `UPPERCASE` (e.g., `TARGET_URL`, `HEADERS`)
- **Database tables:** `snake_case` (e.g., `belanja_link`, `item_item`)
- **Classes:** `PascalCase` (e.g., `ItemBase`, `PriceCreate`)

## Database Standards

### Schema Patterns
- **Primary Keys:** TEXT (shortuuid), always UNIQUE
- **Foreign Keys:** `{table}_id` format (e.g., `items_id`, `belanja_link_id`)
- **Timestamps:** `created_at`, `updated_at`, `deleted_at` (TEXT format: `YYYY-MM-DD HH:MM:SS`)
- **Soft Deletes:** Use `deleted_at` field, never hard delete user data
- **Indexing:** Always index FKs, frequently queried fields (name, sku, source, dates)

### Date Handling
- **Timezone:** Always Asia/Jakarta (`pytz.timezone('Asia/Jakarta')`)
- **Storage Format:** `YYYY-MM-DD HH:MM:SS` as TEXT
- **Query Pattern:** Use `LIKE '{date}%'` for daily granularity checks
- **Never:** Store as UNIX timestamp or without timezone context

### Query Standards
- **Recent Migration:** From ORM to raw SQL (commit: dd5a133)
- **Pattern:** Use SQLlex wrapper for queries
- **Deduplication:** Always check existence before insert:
  ```python
  check = DBAPI.execute(f"SELECT id FROM items WHERE sku = '{sku}' AND source = '{source}'")
  if check.result:
      return check.result[0][0]
  else:
      # Insert new item
  ```

## Git & Version Control

### Branch Strategy
- **Main Branch:** `master`
- **Pattern:** Not enforced (direct commits to master visible)
- **Recommendation:** Use feature branches for new crawlers/features

### Commit Message Format
- **Convention:** `{type}: {description}`
- **Types observed:**
  - `fix:` - Bug fixes
  - `add:` - New features
  - `change:` - Modifications to existing code
- **Examples from history:**
  - `fix: lint error`
  - `add: metric recording`
  - `change: using raw SQL instead of fucking stupid ORM`
  - `change: from ORM to just SQL query`
  - `fix: the counter problem`

### Commit Standards
- Keep commits atomic (one logical change)
- Reference issue numbers if applicable
- Avoid profanity in production commit messages

## Environment & Configuration

### Environment Variables
- **Required:**
  - `STEINDB_URL` - Health monitoring endpoint
  - `STEINDB_USERNAME` - SteinDB auth
  - `STEINDB_PASSWORD` - SteinDB auth
- **Optional:**
  - `DATA_DIR` - Override data file location
  - `PLATFORM` - Crawler target (yogyaonline|klikindomaret|alfagift)

### Configuration Files
- **Never commit:** Credentials, API keys, `.env` files
- **Externalize:** All vendor-specific constants to `config.py`
- **Headers:** Store User-Agent strings centrally

## Docker Standards

### Container Naming
- `Dockerfile.API` - API server container
- `Dockerfile.crawler` - Scraper worker container

### Build Arguments
- Use `ARG` for environment-specific values
- Pass secrets via build args, not in image layers
- Example:
  ```dockerfile
  ARG PLATFORM
  ARG STEINDB_URL
  ```

### Port Exposure
- API: Port 8000 (standard)
- Health checks: Implement `/` endpoint

## Code Architecture (KISS & DRY)

### Module Organization
```
src/
├── main.py           # Entry point, orchestration only
├── config.py         # Centralized configuration
├── db.py             # Database layer
├── models.py         # Data validation models
├── util.py           # Shared utilities
├── crawler/          # Vendor-specific scrapers
│   ├── {vendor}.py   # One file per vendor
├── routes/           # API endpoints
│   ├── {domain}.py   # Grouped by feature domain
└── test/             # Unit tests (mirror src structure)
```

### Function Size
- **Prefer:** Functions < 50 lines
- **Max:** 100 lines before refactoring
- **Pattern:** Extract repeated logic to `util.py`

### DRY Violations to Fix
- Currency parsing duplicated → use `util.cleanUpCurrency()`
- Date formatting duplicated → centralize datetime helper
- Database insert patterns → create generic `upsert()` function
- Crawler deduplication logic → extract to shared method

### KISS Principles
- ✅ Flat directory structure (2 levels max)
- ✅ One crawler per file
- ✅ Direct SQL over heavy ORM
- ❌ Avoid: Commented-out code (delete or feature-flag)
- ❌ Avoid: Multiple database copies (.copy files)

## API Standards

### Endpoint Conventions
- **REST patterns:** Use standard HTTP methods
  - GET - Retrieve
  - POST - Create/Search
  - PUT - Update
  - DELETE - Remove
- **URL structure:** `/{resource}/{id?}`
- **Search:** Use POST (allows complex body filters)

### Request/Response
- **Validation:** Always use Pydantic models
- **Response format:** JSON
- **Error handling:** Return standard HTTP status codes
- **Headers:** Accept `application/json`

### Security
- **Authentication:** Secret key pattern for sensitive operations
- **Rate limiting:** Not implemented (add if public)
- **Input validation:** Pydantic handles, add extra sanitization for SQL

## Logging Standards

### Format
```python
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    level=logging.INFO
)
```

### Log Levels
- **INFO:** Scraping progress, API calls, metrics
- **ERROR:** Failed requests, parsing errors, DB errors
- **DEBUG:** Not used (enable for troubleshooting)

### Structured Logs
- Include: timestamp, vendor, item count, status
- Example: `"2025-11-11 06:45:00 - yogyaonline: 1234 items, 567 new prices"`

## Dependencies

### Adding New Dependencies
1. Justify in plan/PR (1-2 lines)
2. Add to `requirements.txt` AND `Pipfile`
3. Pin versions for stability: `package==X.Y.Z`
4. Prefer stdlib over external libs when possible

### Dependency Review
- Avoid heavy frameworks (SQLAlchemy → SQLlex ✅)
- Check for maintenance status (last update < 1 year)
- Consider bundle size for Docker images

## Feature Development

### Feature Flags
- **Pattern:** Comment out incomplete features
- **Better:** Use environment variable toggles
  ```python
  if os.environ.get('FEATURE_SHOPPING_LISTS', 'false') == 'true':
      # Enable shopping list routes
  ```

### Backward Compatibility
- Never break existing API contracts
- Version endpoints if breaking changes needed: `/v2/search`
- Maintain database migrations (if schema changes)

## CI/CD (Not Implemented)

### Recommended Pipeline
1. **Lint:** flake8 check on all PRs
2. **Test:** Run unittest suite
3. **Build:** Docker image build test
4. **Deploy:** Manual trigger (GitHub Actions)

### Health Checks
- Implement proper liveness/readiness probes
- Currently: SteinDB external monitoring only

## Performance

### Scraping Etiquette
- **Delays:** Use `util.randomWait()` between requests
- **User-Agent:** Rotate headers to avoid blocks
- **Rate limiting:** Respect robots.txt
- **Batch size:** Pagination limits per vendor

### Database Optimization
- ✅ Indexes on FK and query fields
- ✅ Daily granularity reduces query size
- ⚠️ Consider partitioning if data > 10M rows
- ⚠️ Vacuum SQLite periodically

## Documentation

### Code Comments
- **When:** Complex logic, regex patterns, vendor quirks
- **Example:**
  ```python
  # yogyaonline embeds products in JavaScript: var dl4Objects = [...]
  # Extract via regex since JSON is malformed
  ```

### README Requirements
- Setup instructions
- Environment variables
- Running locally
- Docker commands
- API endpoint documentation

### Inline Docs
- Module-level docstrings for each file
- Function docstrings for public APIs
- Type hints where possible (Python 3.8 supports)
