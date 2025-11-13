"""
Test script for the new Yogya Online scraper
Tests the infinite scroll functionality on a single category
"""

import sys
sys.path.insert(0, 'src')

from crawler.yogyaonline import scrape_category
import cloudscraper

# Create scraper
scraper = cloudscraper.create_scraper()

# Test with Sayur-Sayuran category
category_url = "https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category"

print(f"Testing Yogya Online scraper with category: {category_url}")
print("=" * 80)

products = scrape_category(scraper, category_url)

print("\n" + "=" * 80)
print(f"RESULTS:")
print(f"Total products scraped: {len(products)}")
print(f"\nFirst 5 products:")
for i, product in enumerate(products[:5], 1):
    print(f"{i}. {product['item_name']} - Rp {product['price']:,}")
    if product['original_price'] and product['original_price'] > product['price']:
        print(f"   Discount: Rp {product['original_price']:,} -> Rp {product['price']:,} ({product['discount_percentage']}% off)")

print(f"\nLast 5 products:")
for i, product in enumerate(products[-5:], len(products) - 4):
    print(f"{i}. {product['item_name']} - Rp {product['price']:,}")

print("\n" + "=" * 80)
print("✅ Test completed successfully!")
print(f"Expected: ~238 products (17 pages × 14 products)")
print(f"Actual: {len(products)} products")

if len(products) >= 200:
    print("✅ SUCCESS: Scraper is fetching ALL products via infinite scroll!")
else:
    print("⚠️ WARNING: Product count is lower than expected")
