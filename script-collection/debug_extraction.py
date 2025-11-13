import cloudscraper
import json
import urllib.parse
import re
from bs4 import BeautifulSoup

def cleanUpCurrency(value):
    """Clean up currency string"""
    if not value:
        return 0
    # Remove Rp, spaces, dots, and commas
    cleaned = re.sub(r'[Rp\s\.]', '', str(value))
    cleaned = cleaned.replace(',', '')
    try:
        return int(cleaned)
    except:
        return 0

# Create a scraper session
scraper = cloudscraper.create_scraper()

# Visit category page
category_url = 'https://supermarket.yogyaonline.co.id/supermarket/fresh-buah-sayur-sayursayuran/category'
response = scraper.get(category_url, timeout=30)

# Extract category ID
parser = BeautifulSoup(response.text, 'html.parser')
cat_elem = parser.find(attrs={'data-category-id': True})
category_id = int(cat_elem['data-category-id']) if cat_elem else None

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
data = response.json()

html_content = data.get('html', '')
html_parser = BeautifulSoup(html_content, 'html.parser')
product_divs = html_parser.find_all('div', class_='product-item')

print(f'Found {len(product_divs)} products')
print('\\nTrying to extract first product...\\n')

# Try to extract first product
div = product_divs[0]

# Look for product name link
name_link = div.find('a', class_='product-name')
print(f'Found name_link (product-name class): {name_link is not None}')

# Alternative: look for any link with viewProduct onclick
all_links = div.find_all('a')
print(f'Found {len(all_links)} links in product div')

for idx, link in enumerate(all_links):
    onclick = link.get('onclick', '')
    if 'viewProduct' in onclick:
        print(f'\\nLink {idx} has viewProduct:')
        print(f'  onclick: {onclick}')
        print(f'  class: {link.get("class")}')
        print(f'  href: {link.get("href")}')

# Try to find product name directly
product_name_div = div.find('div', class_='product-name')
print(f'\\nFound product-name div: {product_name_div is not None}')
if product_name_div:
    span = product_name_div.find('span')
    if span:
        print(f'Product name text: {span.get_text(strip=True)}')
        # Try to find onclick on parent
        onclick = product_name_div.get('onclick', '')
        print(f'Div onclick: {onclick}')

# Find image
img_tag = div.find('img', class_='product-image')
print(f'\\nFound product-image: {img_tag is not None}')
if img_tag:
    print(f'Image src: {img_tag.get("src")}')

# Find prices
price_divs = div.find_all('div', class_='product-price')
print(f'\\nFound {len(price_divs)} product-price divs')
for idx, price_div in enumerate(price_divs):
    print(f'Price {idx}: {price_div.get_text(strip=True)}')
