import requests
import re
import json
import os
import sys
import logging
from bs4 import BeautifulSoup
from config import DATA_DIR

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def scrap(URL, index):
    TARGET_URL = f"{URL}?p={index}&product_list_limit=80"
    dataProduct = []
    list_ids = []
    # logging.info(f"Run the Scrapper {URL} page {index}")
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
    for index, grouped_item in enumerate(data_raw):
        dataEcommerce = grouped_item['ecommerce']
        for item in dataEcommerce['impressions']:
            if item['id'] not in list_ids:
                dataProduct.append(item)
                list_ids.append(item['id'])
            else:
                logging.info(f"{item['name']} already exist")
                productLink.pop(index)

    for key, value in enumerate(productLink):
        dataProduct[key]['link'] = value
        dataProduct[key]['promotion'] = promotion[key]

    return dataProduct


def getCategories():
    TARGET_URL = "https://www.yogyaonline.co.id/"
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find_all("li", {"id": re.compile('vesitem-*')})
    categories = []
    for cat in categoryClass:
        if cat.find('a').get('href') == "https://www.yogyaonline.co.id/blog-yogya-online":
            continue
        if cat.find('a').get('href') not in categories:
            categories.append(cat.find('a').get('href'))
    
    compiledData = []

    for index, category in enumerate(categories):
        logging.info(f"get {category} from {index+1}/{len(categories)}")
        prevData = {}
        cData = {}
        index = 2
        currData = scrap(category, 1)
        compiledData += currData
        while not prevData == currData:
            logging.info(f"Scrap {category} page {index} with current {len(compiledData)} items")
            prevData = currData
            currData = scrap(category, index)
            index += 1
            compiledData += currData
    return compiledData
    
    

def hotDealsPage(page=1, limit=80):
    TARGET_URL = f"https://www.yogyaonline.co.id/hotdeals.html?p={page}&product_list_limit={limit}"
    dataHotDealsProduct = []
    list_ids = []
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
    for index, grouped_item in enumerate(data_raw):
        dataEcommerce = grouped_item['ecommerce']
        for item in dataEcommerce['impressions']:
            if item['id'] not in list_ids:
                dataHotDealsProduct.append(item)
                list_ids.append(item['id'])
            else:
                logging.info(f"{item['name']} already exist")
                productLink.pop(index)

    for key, value in enumerate(productLink):
        dataHotDealsProduct[key]['link'] = value
        dataHotDealsProduct[key]['promotion'] = promotion[key]

    return dataHotDealsProduct

def hotDeals():
    prevData = {}
    cData = {}
    compiledData = []
    index = 2
    currData = compiledData
    while not prevData == currData:
        for item in currData:
            compiledData.append(item)
        prevData = currData
        currData = hotDealsPage(index)
        index += 1
    return compiledData

