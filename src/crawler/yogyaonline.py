import re
import json
import pytz
import logging
import requests
import shortuuid

from bs4 import BeautifulSoup
# from fp.fp import FreeProxy
from datetime import datetime

from util import cleanUpCurrency
from db import DBSTATE

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logging.info("loading the yogyaonline scrapper")
db = DBSTATE
CATEGORIES = {}

def scrap(URL, index, counter):
    newItems = counter['newItems']
    newPrices = counter['newPrices']
    newDiscounts = counter['newDiscounts']
    # understand the item limit, right now upto 640
    # is it possible to make the limit bigger like 9999
    item_limit = CATEGORIES[URL]['item_limit']
    lanjut = True
    req = requests.get("https://google.com")
    while lanjut:
        TARGET_URL = f"{URL}?p={index}&product_list_limit={item_limit}"
        dataProduct = []
        list_ids = []
        # logging.info(f"Run the Scrapper {URL} page {index}")
        req = requests.get(TARGET_URL)

        if req.status_code == 503:
            item_limit = item_limit / 2
            lanjut = True
            CATEGORIES[URL]['item_limit'] = int(item_limit)
        elif req.status_code > 400:
            print(f"ERROR BANG {req.status_code}, {req.text}")
            return ""
        elif req.status_code < 299:
            lanjut = False

    parser = BeautifulSoup(req.text, 'html.parser')

    e_ListItems = parser.find_all("ol", {"class": "products list items product-items"})

    productLink = []
    if len(e_ListItems) > 0:
        productLink = [item['href'] for item in e_ListItems[0].find_all("a", {"class": "product-item-link"}, href=True)]

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

        date_today = now.strftime("%Y-%m-%d")
        datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

        reqQuery = {
            'script': "SELECT id FROM items WHERE sku=? OR name=?",
            'values': (dataProduct[key]['item_id'], dataProduct[key]['item_name'])
        }
        checkIdItem = db.execute(**reqQuery)
        idItem = shortuuid.uuid()

        if len(checkIdItem) == 0:
            db["items"].insert(idItem, dataProduct[key]['item_id'], 
                               dataProduct[key]['item_name'], dataProduct[key]['item_list_name'], 
                               dataProduct[key]['image'], dataProduct[key]['link'], 'yogyaonline', 
                               datetime_today)
            newItems += 1
        else:
            idItem = checkIdItem[0][0]

        reqQuery = {
            'script': "SELECT id FROM prices WHERE items_id=? AND created_at LIKE ? AND price=?",
            'values': (idItem, f'{date_today}%', cleanUpCurrency(dataProduct[key]['price']))
        }
        checkItemIdinPrice = db.execute(**reqQuery)
        
        if len(checkItemIdinPrice) == 0:
            db["prices"].insert(shortuuid.uuid(), idItem, 
                                cleanUpCurrency(dataProduct[key]['price']), "", 
                                datetime_today)
            newPrices += 1

        reqQuery = {
            'script': "SELECT id FROM discounts WHERE items_id=? AND created_at LIKE ? AND discount_price=? AND original_price=?",
            'values': (idItem, f'{date_today}%', cleanUpCurrency(dataProduct[key]['price']), cleanUpCurrency(dataProduct[key]['promotion']['original_price']))
        }
        checkItemIdinDiscount = db.execute(**reqQuery)

        if len(checkItemIdinDiscount) == 0:
            db["discounts"].insert(shortuuid.uuid(), idItem, 
                                   cleanUpCurrency(dataProduct[key]['price']), 
                                   cleanUpCurrency(dataProduct[key]['promotion']['original_price']), 
                                   dataProduct[key]['promotion']['description'], "", 
                                   datetime_today)
            newDiscounts += 1

    return dataProduct


def getCategories():
    TARGET_URL = "https://www.yogyaonline.co.id/"
    resp = requests.get(TARGET_URL)
    logging.info(f"{resp.status_code} for {TARGET_URL}")
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find_all("li", {"id": re.compile('vesitem-*')})
    categories = []
    for cat in categoryClass:
        if cat.find('a').get('href') == "https://yogyaonline.co.id/blog-yogya-online":
            continue
        if cat.find('a').get('href') == "#":
            continue
        if cat.find('a').get('href') not in categories:
            categories.append(cat.find('a').get('href'))
    
    compiledData = []
    counter = {
        "newItems" : 0,
        "newPrices" : 0,
        "newDiscounts" : 0
    }
    

    for index, category in enumerate(categories):
        logging.info(f"get {category} from {index+1}/{len(categories)}")
        prevData = {}
        index = 2
        CATEGORIES[category] = {
            "item_limit": 640
        }
        currData = scrap(category, 1,counter)
        compiledData += currData
        while not prevData == currData:
            # logging.info(f"Scrap {category} page {index} with current {len(compiledData)} items")
            prevData = currData
            currData = scrap(category, index,counter)
            if currData == "":
                continue
            index += 1
            compiledData += currData

    logging.info(f"=== Finish scrap {len(compiledData)} item by added {counter['newItems']} items, {counter['newPrices']} prices, {counter['newDiscounts']} discounts")
    if counter['newItems'] ==0 & counter['newPrices']==0 & counter['newDiscounts']==0:
        logging.info("=== i guess nothing different today")

    # return compiledData
    return f"=== Finish scrap {len(compiledData)} item by added {counter['newItems']} items, {counter['newPrices']} prices, {counter['newDiscounts']} discounts"
