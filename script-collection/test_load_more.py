import cloudscraper
import json
import re
from bs4 import BeautifulSoup

# Create a scraper session
scraper = cloudscraper.create_scraper()

# First, visit the category page to get CSRF token and cookies
category_url = 'https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category'
print(f'Visiting category page: {category_url}')
response = scraper.get(category_url, timeout=30)
print(f'Category page status: {response.status_code}')

# Parse the page to find CSRF token and category ID
parser = BeautifulSoup(response.text, 'html.parser')
csrf_token = None
category_id = None

# Look for CSRF token in meta tag
meta_tag = parser.find('meta', {'name': 'csrf-token'})
if meta_tag:
    csrf_token = meta_tag.get('content')
    print(f'Found CSRF token: {csrf_token[:20]}...')

# Try to find category ID from JavaScript or HTML
# Look for category_id in the page source
cat_id_match = re.search(r'category_id["\']?\s*[:=]\s*["\']?(\d+)', response.text)
if cat_id_match:
    category_id = int(cat_id_match.group(1))
    print(f'Found category_id in page: {category_id}')

# If not found, try to extract from URL structure or other places
if not category_id:
    # Look for data-category-id attribute
    cat_elem = parser.find(attrs={'data-category-id': True})
    if cat_elem:
        category_id = int(cat_elem['data-category-id'])
        print(f'Found category_id from data attribute: {category_id}')

# Default to 2921 if not found
if not category_id:
    category_id = 2921
    print(f'Using default category_id: {category_id}')

print(f'\nCookies: {list(scraper.cookies.keys())}')
print(f'XSRF-TOKEN cookie: {scraper.cookies.get("XSRF-TOKEN", "Not found")[:50]}...')

# Now test the load-more-product endpoint with proper headers
url = 'https://supermarket.yogyaonline.co.id/load-more-product'
payload = {
    'current_page': 2,
    'brands': [],
    'category_id': category_id
}

# Get XSRF token from cookie (decode it)
import urllib.parse
xsrf_token = scraper.cookies.get('XSRF-TOKEN')
if xsrf_token:
    xsrf_token = urllib.parse.unquote(xsrf_token)
    print(f'\nXSRF Token (decoded): {xsrf_token[:50]}...')

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': category_url,
}

# Use XSRF token from cookie instead of CSRF meta tag
if xsrf_token:
    headers['X-XSRF-TOKEN'] = xsrf_token

print(f'\nMaking POST request to: {url}')
print(f'Payload: {payload}')
print(f'Headers: {headers}')
response = scraper.post(url, json=payload, headers=headers, timeout=30)
print(f'\nStatus Code: {response.status_code}')
print(f'Response Length: {len(response.text)}')

# Try to parse as JSON
try:
    data = response.json()
    print(f'\nJSON Keys: {data.keys() if isinstance(data, dict) else "Not a dict"}')
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'html':
                print(f'{key}: <HTML content, length {len(value)} chars>')
                # Parse the HTML to count products
                html_parser = BeautifulSoup(value, 'html.parser')
                products = html_parser.find_all('div', class_='product-item')
                print(f'  -> Found {len(products)} products in HTML')
            else:
                print(f'{key}: {type(value)} = {value}')
except Exception as e:
    print(f'\nNot JSON: {e}')
    print(f'Response text: {response.text[:500]}')
