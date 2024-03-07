import requests
import re
import json
import logging
import sys
from bs4 import BeautifulSoup
from config import HEADERS
from fp.fp import FreeProxy
from datetime import datetime
import pytz
import shortuuid
from util import cleanUpCurrency

from db import DBSTATE

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

db = DBSTATE

def scrap(URL, index):
    # understand the item limit, right now upto 640
    # is it possible to make the limit bigger like 9999
    TARGET_URL = f"{URL}?p={index}&product_list_limit=640"
    dataProduct = []
    list_ids = []
    # logging.info(f"Run the Scrapper {URL} page {index}")
    req = requests.get(TARGET_URL)

    parser = BeautifulSoup(req.text, 'html.parser')

    productLink = [item['href'] for item in parser.find_all("ol", {"class": "products list items product-items"})[0].find_all("a", {"class": "product-item-link"}, href=True)]

    print(len(productLink))
    productImages = [item.get('data-original') for item in parser.find_all("img", {"class": "product-image-photo lazy"})]
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

    p = re.compile('var dl4Objects = (.*);')
    found = ""
    for script in parser.find_all("script", {"src":False}):
        if script:
            m = p.search(script.string)
            if m is not None:
                found = m.group().replace("var dl4Objects =", "")
                found = found.replace(";", "")
    
    data_raw = json.loads(found)

    for index, grouped_item in enumerate(data_raw):
        dataEcommerce = grouped_item['ecommerce']
        for item in dataEcommerce['items']:
            if item['item_id'] not in list_ids:
                dataProduct.append(item)
                list_ids.append(item['item_id'])
            else:
                logging.info(f"{item['name']} already exist")
                productLink.pop(index)

    for key, value in enumerate(productLink):
        dataProduct[key]['link'] = value
        dataProduct[key]['promotion'] = promotion[key]
        dataProduct[key]['image'] = productImages[key]
        now = datetime.now(pytz.timezone("Asia/Jakarta"))
        checkIdItem = db.select(TABLE='items', SELECT='id', WHERE=(db['items']['sku'] == dataProduct[key]['item_id']) | (db['items']['name'] == dataProduct[key]['item_name']))
        if len(checkIdItem) > 0:
            idItem = checkIdItem[0][0]
            # harus di cek lagi, hari ini datanya sama atau tidak
            # kalau hari ini datanya sama, ga usah simpen data harga sama diskon
            db["prices"].insert(shortuuid.uuid(), idItem, cleanUpCurrency(dataProduct[key]['price']), "", now.strftime("%Y-%m-%d %H:%M:%S"))
            db["discounts"].insert(shortuuid.uuid(), idItem, dataProduct[key]['price'], cleanUpCurrency(dataProduct[key]['promotion']['original_price']), dataProduct[key]['promotion']['description'], "", now.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            idItem = shortuuid.uuid()
            db["items"].insert(idItem, dataProduct[key]['item_id'], dataProduct[key]['item_name'], dataProduct[key]['item_list_name'], dataProduct[key]['image'], dataProduct[key]['link'], 'yogyaonline', now.strftime("%Y-%m-%d %H:%M:%S"))
            db["prices"].insert(shortuuid.uuid(), idItem, cleanUpCurrency(dataProduct[key]['price']), "", now.strftime("%Y-%m-%d %H:%M:%S"))
            db["discounts"].insert(shortuuid.uuid(), idItem, dataProduct[key]['price'], cleanUpCurrency(dataProduct[key]['promotion']['original_price']), dataProduct[key]['promotion']['description'], "", now.strftime("%Y-%m-%d %H:%M:%S"))

    return dataProduct


def getCategories():
    TARGET_URL = "https://www.yogyaonline.co.id/"
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find_all("li", {"id": re.compile('vesitem-*')})
    categories = []
    for cat in categoryClass:
        if cat.find('a').get('href') == "https://yogyaonline.co.id/blog-yogya-online":
            continue
        if cat.find('a').get('href') == "https://yogyaonline.co.id/hotdeals.html":
            continue
        if cat.find('a').get('href') == "#":
            continue
        if cat.find('a').get('href') not in categories:
            categories.append(cat.find('a').get('href'))
    
    compiledData = []

    for index, category in enumerate(categories):
        logging.info(f"get {category} from {index+1}/{len(categories)}")
        prevData = {}
        index = 2
        currData = scrap(category, 1)
        compiledData += currData
        while not prevData == currData:
            logging.info(f"Scrap {category} page {index} with current {len(compiledData)} items")
            prevData = currData
            currData = scrap(category, index)
            index += 1
            compiledData += currData
        
        sys.exit()

    return compiledData
    
    

def hotDealsPage(page=1, limit=80):
    proxy = FreeProxy(google=True).get()
    TARGET_URL = f"https://www.yogyaonline.co.id/hotdeals.html?p={page}&product_list_limit={limit}"
    dataHotDealsProduct = []
    list_ids = []
    logging.info(f"Run the Scrapper page {page} and limit {limit}")
    req = requests.get(TARGET_URL, headers=HEADERS, proxies={'http': proxy})

    parser = BeautifulSoup(req.text, 'html.parser')

    productLink = [item['href'] for item in parser.find_all("ol", {"class": "products list items product-items"})[0].find_all("a", {"class": "product-item-link"}, href=True)]
    
    productImages = [item.get('data-original') for item in parser.find_all("img", {"class": "product-image-photo lazy"})]
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
        dataHotDealsProduct[key]['image'] = productImages[key]

    return dataHotDealsProduct

def hotDeals():
    prevData = {}
    cData = {}
    compiledData = []
    index = 1
    currData = compiledData
    # blocked at page 6
    while not prevData == currData:
        for item in currData:
            compiledData.append(item)
        prevData = currData
        currData = hotDealsPage(index)
        index += 1
        if index == 5:
            break
    return compiledData

