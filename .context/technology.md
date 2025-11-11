# Technology Stack

## Core Technology
- **Language:** Python 3.8
- **Package Manager:** Pipenv
- **Container:** Docker (multi-container setup)

## Web Framework & Server
- **API Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Data Validation:** Pydantic v2

## Database
- **DBMS:** SQLite3
- **ORM/Wrapper:** SQLlex (lightweight SQL wrapper)
- **Databases:**
  - `indiemart.db` - API data (items, prices, discounts, shopping lists)
  - `crawl.db` - Crawler state tracking
- **Migration Status:** Recently moved from ORM to raw SQL queries (commit: dd5a133)

## Web Scraping Stack
- **HTTP Client:** requests
- **HTML Parser:** BeautifulSoup4
- **XML/HTML Parser:** lxml
- **API-based:** alfagift uses direct REST API calls

## Scheduling & Utilities
- **Job Scheduler:** schedule library
- **Progress Bars:** tqdm
- **Timezone:** pytz (Asia/Jakarta)
- **ID Generation:** shortuuid
- **Logging:** loguru

## Code Quality
- **Linter:** flake8 (pycodestyle, pyflakes, mccabe)
- **Testing:** unittest (minimal coverage - only alfagift_test.py exists)

## External Services
- **Health Monitoring:** SteinDB (spreadsheet-based API for health checks)
  - Endpoint configured via `STEINDB_URL`
  - Authentication: username/password

## Infrastructure & Deployment
- **Containerization:**
  - `Dockerfile.API` - Runs FastAPI server on port 8000
  - `Dockerfile.crawler` - Runs scraper jobs per platform
- **Build Arguments:**
  - `PLATFORM` - Target crawler (yogyaonline|klikindomaret|alfagift)
  - `STEINDB_USERNAME`, `STEINDB_PASSWORD`, `STEINDB_URL`

## Data Storage
- **Databases:** SQLite files in project root
- **Backup Files:** JSON exports in `data/{vendor}/{type}/{date}.json`

## Dependencies (key packages)
```
fastapi
uvicorn
pydantic>=2.0
requests
beautifulsoup4
lxml
schedule
tqdm
pytz
shortuuid
loguru
sqlex
flake8
```

## Integration Points
1. **External E-commerce Sites:**
   - yogyaonline.co.id (HTML scraping)
   - klikindomaret.com (HTML scraping)
   - alfagift.id (REST API)

2. **Monitoring:**
   - SteinDB REST API for health metrics

## Version Notes
- Python 3.8 is specified (consider upgrading - EOL Oct 2024)
- Pydantic v2 indicates recent upgrade from v1
- SQLlex wrapper suggests custom/lightweight ORM preference
