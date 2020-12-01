import requests
import re
import json
import os
import sys
import logging
from datetime import date
from bs4 import BeautifulSoup

from notifier import RunNotifier

DATA_DIR = './data'
TODAY_STRING = date.today().strftime("%Y-%m-%d")
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def hotDealsPage(page=1, limit=80):
    TARGET_URL = f"https://www.yogyaonline.co.id/hotdeals.html?p={page}&product_list_limit={limit}"
    dataHotDealsProduct = []
    logging.info(f"Run the Scrapper page {page} and limit {limit}")
    req = requests.get(TARGET_URL)

    parser = BeautifulSoup(req.text, 'html.parser')

    productLink = [item['href'] for item in parser.find_all("ol", {"class": "products list items product-items"})[0].find_all("a", {"class": "product-item-link"}, href=True)]
    promotion = []
    for item in parser.find_all("div", {"class": "price-box price-final_price"}):
        tType = ""
        description = ""
        if len(item.find_all("div", {"class": "label-promo custom"})) > 0:
            tType = "promo"
            description = item.find_all("div", {"class": "label-promo custom"})[0].get_text().replace(" ","").replace("\r\n", "")

        if len(item.find_all("div", {"class": "product product-promotion"})) > 0:
            tType = "discount"
            description = item.find_all("div", {"class": "product product-promotion"})[0].get_text().replace(" ","").replace("\r\n", "")
            
        promotion.append({
            "type": tType,
            "description": description,
            "original_price": item.find_all("span", {"class": "price"})[0].get_text()
        })

    if not len(promotion) == 80:
        for index in range(len(promotion), 80):
            promotion.append({
                "type": "",
                "description": "",
                "original_price": ""
            })

    p = re.compile('var dlObjects = (.*);')
    found = ""
    for script in parser.find_all("script", {"src":False}):
        if script:
           m = p.search(script.string)
           if m is not None:
               found = m.group().replace("var dlObjects =", "")
               found = found.replace(";", "")
    
    data_raw = json.loads(found)
    for grouped_item in data_raw:
        dataEcommerce = grouped_item['ecommerce']
        dataHotDealsProduct += dataEcommerce['impressions']

    for key, value in enumerate(productLink):
        dataHotDealsProduct[key]['link'] = value
        dataHotDealsProduct[key]['promotion'] = promotion[key]

    return dataHotDealsProduct


if __name__ == "__main__":
    prevData = {}
    currData = hotDealsPage()
    compiledData = []
    index = 2
    while not prevData == currData:
        for item in currData:
            compiledData.append(item)
        prevData = currData
        currData = hotDealsPage(page=index)
        index += 1
    
    cData = {
        'data': compiledData,
        'date': TODAY_STRING
    }

    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    file_object = open(f'{DATA_DIR}/{TODAY_STRING}.json', 'w+')
    file_object.write(json.dumps(cData))

    RunNotifier()

    sys.exit(0)
