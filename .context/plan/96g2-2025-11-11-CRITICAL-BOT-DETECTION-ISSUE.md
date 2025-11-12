# CRITICAL: Bot Detection Issue

**Plan ID:** 96g2
**Date:** 2025-11-11
**Status:** **BLOCKED** - API has Cloudflare/Bot Detection
**Priority:** CRITICAL

---

## Issue

The Klik Indomaret API at `https://ap-mc.klikindomaret.com` has **Cloudflare bot detection** enabled. Direct HTTP requests from Python return:

```
403 Client Error: Forbidden
```

---

## Confirmed Working

✅ **Playwright browser** - API calls work fine in browser context (we tested this)
✅ **Website** - APIs work when called from actual browser

❌ **Python requests** - Blocked with 403 Forbidden
❌ **Simple HTTP** - Blocked by Cloudflare

---

## Solutions (Choose One)

### Option 1: Install Cloudscraper (Recommended - Easiest)
```bash
pip install cloudscraper
# or
uv add cloudscraper
```

**Pros:**
- Drop-in replacement for requests
- Handles Cloudflare automatically
- Fast and lightweight
- No browser needed

**Code Change:**
```python
# Change from:
import requests
session = requests.Session()

# To:
import cloudscraper
session = cloudscraper.create_scraper()
```

---

### Option 2: Use Playwright (Works, but slower)
```bash
pip install playwright
playwright install chromium
# or
uv add playwright
```

**Pros:**
- Confirmed working (we tested it)
- Handles JavaScript rendering
- Most reliable

**Cons:**
- Slower (launches browser)
- Higher resource usage
- More complex

**Implementation:** Already created in `src/api_client/klikindomaret_api.py` (commented version)

---

### Option 3: Use curl_cffi (Alternative)
```bash
pip install curl_cffi
```

**Pros:**
- Fast like cloudscraper
- Good Cloudflare bypass

**Cons:**
- Less popular than cloudscraper
- May need C compiler on some systems

---

## Recommended Action

**Install cloudscraper:**
```bash
cd C:\Users\k1m0c\Documents\opensource\k1m0ch1\BiBiT
uv add cloudscraper
```

Then update `src/api_client/klikindomaret_api.py`:
```python
# Line 12: Change
import requests

# To:
import cloudscraper

# Line 31: Change
self.session = requests.Session()

# To:
self.session = cloudscraper.create_scraper()
```

---

## Files Created

1. ✅ `src/test/test_klikindomaret_api.py` - Test script (shows 403 error)
2. ✅ `src/api_client/klikindomaret_api.py` - API client (needs cloudscraper)
3. ⏸️ Production scraper update - **BLOCKED** until bot detection solved

---

## Next Steps

1. **User decision:** Choose solution (cloudscraper recommended)
2. **Install dependency:** `uv add cloudscraper`
3. **Update API client:** Replace `requests` with `cloudscraper`
4. **Test again:** Run `python src/api_client/klikindomaret_api.py`
5. **Continue implementation:** Once working, proceed with scraper update

---

## Test Results

```
[FAIL]: categories - 403 Forbidden
[FAIL]: products - 403 Forbidden
[FAIL]: pagination - 403 Forbidden
```

**All tests blocked by Cloudflare protection.**

---

## References

- **Cloudscraper:** https://github.com/VeNoMouS/cloudscraper
- **Playwright:** https://playwright.dev/python/
- **API Client:** `src/api_client/klikindomaret_api.py`
- **Test Script:** `src/test/test_klikindomaret_api.py`

---

**Status:** Waiting for user to install cloudscraper or choose alternative solution.
