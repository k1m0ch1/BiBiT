import cloudscraper
import json
import urllib.parse
from bs4 import BeautifulSoup

# Create a scraper session
scraper = cloudscraper.create_scraper()

# First, visit the category page
category_url = 'https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category'
print(f'Visiting category page: {category_url}')
response = scraper.get(category_url, timeout=30)

# Extract category ID
parser = BeautifulSoup(response.text, 'html.parser')
cat_elem = parser.find(attrs={'data-category-id': True})
category_id = int(cat_elem['data-category-id']) if cat_elem else None
print(f'Category ID: {category_id}')

# Get XSRF token
xsrf_token = scraper.cookies.get('XSRF-TOKEN')
if xsrf_token:
    xsrf_token = urllib.parse.unquote(xsrf_token)

# Make POST request
url = 'https://supermarket.yogyaonline.co.id/load-more-product'
payload = {
    'current_page': 1,
    'brands': [],
    'category_id': category_id
}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': category_url,
}

if xsrf_token:
    headers['X-XSRF-TOKEN'] = xsrf_token

import time
time.sleep(2)

response = scraper.post(url, json=payload, headers=headers, timeout=30)
print(f'\nStatus: {response.status_code}')

data = response.json()
print(f'Response keys: {data.keys()}')
print(f'Status: {data.get("status")}')
print(f'Message: {data.get("message")}')
print(f'Total pages: {data.get("total_page")}')
print(f'Current page: {data.get("current_page")}')
print(f'Total products: {data.get("total_product")}')

html_content = data.get('html', '')
print(f'\nHTML length: {len(html_content)}')
print(f'\nFirst 1000 chars of HTML:')
print(html_content[:1000])

# Parse HTML
html_parser = BeautifulSoup(html_content, 'html.parser')
products = html_parser.find_all('div', class_='product-item')
print(f'\nFound {len(products)} product-item divs')

# Try alternative class names
products2 = html_parser.find_all('div', {'class': lambda x: x and 'product' in x})
print(f'Found {len(products2)} divs with "product" in class')

# Show all div classes in the HTML
all_divs = html_parser.find_all('div', class_=True)
print(f'\nAll div classes found (first 20):')
classes_seen = set()
for div in all_divs[:50]:
    class_str = ' '.join(div.get('class', []))
    if class_str not in classes_seen:
        classes_seen.add(class_str)
        print(f'  - {class_str}')
