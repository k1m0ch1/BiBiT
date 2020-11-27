import requests
import re
import json
import os
from datetime import date
from bs4 import BeautifulSoup

DATA_DIR = './data'
TODAY_STRING = date.today().strftime("%Y-%m-%d")

req = requests.get("https://www.yogyaonline.co.id/hotdeals.html")

soup = BeautifulSoup(req.text, 'html.parser')

p = re.compile('var dlObjects = (.*);')
found = ""
for script in soup.find_all("script", {"src":False}):
    if script:         
       m = p.search(script.string)
       if m is not None:
           found = m.group().replace("var dlObjects =", "")
           found = found.replace(";", "")

dataEcommerce = json.loads(found)[0]['ecommerce']
dataHotDealsProduct = dataEcommerce['impressions']
compiledData = {
    'data': dataHotDealsProduct,
    'date': TODAY_STRING
}

if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

file_object = open(f'{DATA_DIR}/{TODAY_STRING}.json', 'w+')
file_object.write(json.dumps(compiledData))