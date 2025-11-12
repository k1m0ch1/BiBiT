"""
Check the actual type and structure of the data field
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

# Test products with specific category
url = f"{BASE_URL}/assets-klikidmcore/api/get/catalog-xpress/api/webapp/search/result"
params = {**default_params, 'page': 0, 'size': 5, 'categories': '345'}
response = session.get(url, params=params, timeout=30)
products_data = response.json()

print("Full Response:")
print(json.dumps(products_data, indent=2, ensure_ascii=False))
