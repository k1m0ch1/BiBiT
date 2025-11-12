"""
Quick test to examine the actual API response structure
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
print("Testing Category API Response Structure")
print("=" * 60)

# Test categories
url = f"{BASE_URL}/assets-klikidmgroceries/api/get/catalog-xpress/api/webapp/category/meta"
response = session.get(url, params=default_params, timeout=30)
categories_data = response.json()

print(f"\nStatus Code: {response.status_code}")
print(f"\nFull Response Keys: {categories_data.keys()}")
print(f"\nFirst category (raw):")
if 'data' in categories_data and len(categories_data['data']) > 0:
    print(json.dumps(categories_data['data'][0], indent=2))

print("\n" + "=" * 60)
print("Testing Product API Response Structure")
print("=" * 60)

# Test products
url = f"{BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"
params = {**default_params, 'page': 0, 'size': 3, 'categories': ''}
response = session.get(url, params=params, timeout=30)
products_data = response.json()

print(f"\nStatus Code: {response.status_code}")
print(f"\nFull Response Keys: {products_data.keys()}")
print(f"\nFirst product (raw):")
if 'data' in products_data and len(products_data['data']) > 0:
    print(json.dumps(products_data['data'][0], indent=2))
