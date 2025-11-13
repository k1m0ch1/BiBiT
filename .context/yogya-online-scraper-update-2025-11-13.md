# Yogya Online Scraper Update - November 13, 2025

## Problem

The Yogya Online scraper stopped working because the website underwent a complete restructure:

**Old Structure:**
- Domain: `www.yogyaonline.co.id`
- Static category pages
- JavaScript data: `var dl4Objects`
- Selectors: `li[id^='vesitem-']`, `ol.products.list.items.product-items`

**New Structure:**
- Domain: `supermarket.yogyaonline.co.id` (subdomain)
- Dynamic category menu (JavaScript-loaded)
- No `dl4Objects` in JavaScript
- New selectors: `div.product-item.box-shadow-light`

## Investigation Process

### 1. Initial Discovery (Playwright Browser Investigation)
- Used MCP Playwright tool to navigate the new website
- Discovered subdomain structure: `supermarket.yogyaonline.co.id`
- Found category URLs follow pattern: `/supermarket/{category-path}/category`
- Confirmed products display correctly with new HTML structure

### 2. HTML Structure Analysis
Created test scripts to understand the new page structure:

```python
# Key findings:
- Product containers: <div class="product-item box-shadow-light">
- Product data extracted from onclick attributes: viewProduct('SKU', null, 'BRAND', 'NAME')
- Prices in: <div class="product-price">
- Discounts in: <span class="badge bg-danger">-10%</span>
```

### 3. Category URL Extraction
Found 9 working category URLs from the homepage HTML:
```
https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category
https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-buahbuahan/category
https://supermarket.yogyaonline.co.id/supermarket/hot-deals-promo-minggu-ini-harbolnas/category
https://supermarket.yogyaonline.co.id/supermarket/hot-deals-flash-sale-12-13/category
https://supermarket.yogyaonline.co.id/supermarket/hot-deals-produk-terbaru/category
https://supermarket.yogyaonline.co.id/supermarket/hot-deals-produk-rekomendasi/category
https://supermarket.yogyaonline.co.id/supermarket/makanan-bahan-masakan-cooking-oil/category
https://supermarket.yogyaonline.co.id/supermarket/produk-import-makanan-import-cemilan/category
https://supermarket.yogyaonline.co.id/supermarket/official-store-yoa-pasti-hemat-pasti-hemat/category
```

## Solution Implemented

### Updated Scraper: `src/crawler/yogyaonline.py`

**Key Changes:**

1. **Removed JavaScript Parsing**
   ```python
   # OLD: Parse dl4Objects from JavaScript
   pattern = re.compile(r'var dl4Objects = (.*);')

   # NEW: Parse HTML directly
   product_divs = parser.find_all("div", class_="product-item box-shadow-light")
   ```

2. **New Product Extraction Function**
   ```python
   def _extract_product_from_html(div):
       """Extract product data from HTML div element"""
       # Extract from onclick attribute
       onclick = name_link.get('onclick', '')
       match = re.search(r"viewProduct\('([^']+)',\s*null,\s*'([^']*)',\s*'([^']*)'\)", onclick)

       sku = match.group(1)
       brand = match.group(2)
       name = match.group(3)

       # Extract prices
       price_divs = div.find_all("div", class_="product-price")

       # Extract discount badge
       discount_badge = div.find("span", class_="badge bg-danger")
   ```

3. **Hardcoded Category URLs**
   ```python
   def getCategories():
       """Uses hardcoded category URLs from new supermarket subdomain"""
       categories = [
           "https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category",
           # ... 8 more categories
       ]
   ```

4. **Simplified Parsing Flow**
   ```python
   # OLD: Extract links, images, promotions, JavaScript data separately
   # NEW: Single pass extraction from HTML divs

   def _parse_page(html_content, counter):
       product_divs = parser.find_all("div", class_="product-item box-shadow-light")
       for div in product_divs:
           product = _extract_product_from_html(div)
           _save_product_to_db(product, counter)
   ```

### Updated Database Insertion

Modified `_save_product_to_db()` to work with new product structure:

```python
# Product dictionary structure:
{
    'item_id': sku,
    'item_name': name,
    'item_list_name': brand,
    'price': final_price or original_price,
    'original_price': original_price,
    'discount_price': final_price if original_price else None,
    'discount_percentage': discount_pct,
    'discount_description': discount_desc,
    'link': link,
    'image': image,
}
```

## Test Results

### Scraper Performance
```
✅ 9 categories scraped
✅ 252 products found (first run)
✅ 47 new items added
✅ 123 prices recorded
✅ 61 discounts tracked
```

### Database Verification
```bash
uv run python src/test/yogya_verification.py
```

Output:
```
Total Yogya Online items: 14,539
Total prices: 35,808
Total discounts: 37,023
```

## Files Changed

### Main Implementation
- **`src/crawler/yogyaonline.py`** - Complete rewrite with HTML parsing
- **`src/crawler/yogyaonline_old.py`** - Backup of old JavaScript-based scraper

### Test/Verification
- **`src/test/yogya_verification.py`** - Database verification script

## Usage

### Run Scraper
```bash
uv run python src/main.py --target yogyaonline do.scrap
```

### Verify Results
```bash
uv run python src/test/yogya_verification.py
```

## Technical Details

### New HTML Selectors

| Element | Selector | Purpose |
|---------|----------|---------|
| Product Container | `div.product-item.box-shadow-light` | Main product wrapper |
| Product Name | `a.product-name` | Name and link |
| Product Data | `onclick="viewProduct(...)"` | SKU, brand, name |
| Image | `img.product-image` | Product image |
| Price | `div.product-price` | Regular/discounted price |
| Discount Badge | `span.badge.bg-danger` | Discount percentage |

### Price Extraction Logic

```python
# Single price = regular price
if len(price_divs) == 1:
    final_price = clean_price(price_divs[0])

# Two prices = original + discounted
if len(price_divs) >= 2:
    original_price = clean_price(price_divs[0])
    final_price = clean_price(price_divs[1])
```

### Discount Calculation

```python
# Extract from badge if available
if discount_badge:
    pct_match = re.search(r'-(\d+)%', discount_text)

# Otherwise calculate from prices
if original_price > final_price:
    discount_pct = int(((original_price - final_price) / original_price) * 100)
```

## Advantages Over Old Scraper

| Aspect | Old Scraper | New Scraper |
|--------|-------------|-------------|
| **Reliability** | ❌ Broke when JS changed | ✅ HTML more stable |
| **Speed** | Moderate | Same |
| **Maintenance** | High (JS parsing) | Low (direct HTML) |
| **Data Quality** | Good | ✅ Better (direct extraction) |
| **Error Handling** | Complex | ✅ Simpler |

## Future Considerations

### Adding More Categories

The current implementation uses 9 hardcoded categories. To add more:

1. Navigate to `https://supermarket.yogyaonline.co.id/`
2. Inspect the category dropdown menu
3. Find URLs matching pattern: `/supermarket/{path}/category`
4. Add to `categories` list in `getCategories()` function

### Monitoring for Changes

Watch for:
- Changes to `div.product-item.box-shadow-light` class name
- Changes to `onclick` attribute format
- URL structure changes
- New subdomain migrations

### Performance Optimization

Current performance is good with rate limiting. If needed:
- Increase `product_list_limit` parameter (currently 640)
- Adjust rate limiting delays (currently 1.0-2.5s)
- Consider async/concurrent requests

## Related Documentation

- **Main Context:** `CLAUDE.md` (updated with current status)
- **Python Upgrade:** `.context/plan/96g2-2025-11-12-python-upgrade-cloudscraper-integration.md`
- **Klik Indomaret Fix:** `.context/plan/96g2-2025-11-11-klikindomaret-api-scraping.md`

## Lessons Learned

1. **Website Changes:** E-commerce sites frequently restructure
2. **HTML > JavaScript:** Parsing HTML is more reliable than extracting from JS variables
3. **Browser Tools:** MCP Playwright is invaluable for investigating dynamic sites
4. **Hardcoded URLs:** Sometimes simpler than dynamic discovery for small category lists
5. **Incremental Testing:** Test small parts before full integration

---

**Status:** ✅ Complete and Working
**Date:** November 13, 2025
**Author:** Claude (assisted by k1m0ch)
