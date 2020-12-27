import requests
import re
import json
import os
import sys
import logging
from bs4 import BeautifulSoup
from config import DATA_DIR

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

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

    for category in categories:
        logging.info(category)
        prevData = {}
        cData = {}
        index = 1
        currData = compiledData
        while not prevData == currData:
            for item in currData:
                compiledData.append(item)
            prevData = currData
            
            TARGET_URL = f"{category}?p={index}&product_list_limit=80"
            dataHotDealsProduct = []
            logging.info(f"Run the Scrapper page {index}")
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

            index += 1

            compiledData += dataHotDealsProduct

    return compiledData
    
    

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
