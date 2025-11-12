"""
Test products API with specific category
"""
import cloudscraper
import json

BASE_URL = "https://ap-mc.klikindomaret.com"

session = cloudscraper.create_scraper()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.klikindomaret.com/',
    'Origin': 'https://www.klikindomaret.com',
})

default_params = {
    'storeCode': 'TJKT',
    'latitude': '-6.1763897',
    'longitude': '106.82667',
    'mode': 'DELIVERY',
    'districtId': '141100100'
}

print("=" * 60)
print("Testing Product API with Category ID 345 (Perawatan Diri)")
print("=" * 60)

# Test products with specific category
url = f"{BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"
params = {**default_params, 'page': 0, 'size': 5, 'categories': '345'}
response = session.get(url, params=params, timeout=30)
products_data = response.json()

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse Keys: {products_data.keys()}")
print(f"\nTotal Products: {len(products_data.get('data', []))}")

if 'data' in products_data and len(products_data['data']) > 0:
    print(f"\nFirst product:")
    product = products_data['data'][0]
    print(json.dumps(product, indent=2, ensure_ascii=False))

    print(f"\n\nSummary of first product:")
    print(f"  ID: {product.get('id')}")
    print(f"  Name: {product.get('name')}")
    print(f"  SKU: {product.get('sku')}")
    print(f"  Main Image: {product.get('mainImage')}")

    if 'prices' in product and len(product['prices']) > 0:
        price_info = product['prices'][0]
        print(f"\n  Price Info:")
        print(f"    Price: Rp {price_info.get('price', 0):,}")
        print(f"    Original Price: Rp {price_info.get('originalPrice', 0):,}")
        if price_info.get('discount'):
            print(f"    Discount: {price_info.get('discount')}")
else:
    print("\n[WARNING] No products found for category 345")
    print("Response data:")
    print(json.dumps(products_data, indent=2, ensure_ascii=False))
