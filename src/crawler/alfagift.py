import requests
import sys
import shortuuid
from tqdm import tqdm
from datetime import datetime
from db import DBSTATE
import logging
import pytz
from sqllex import LIKE

db = DBSTATE
HOST = "https://webcommerce-gw.alfagift.id/v2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Origin": "https://alfagift.id",
    "Referer": "https://alfagift.id/",
    "Devicemodel": "Chrome",
    "Devicetype": "Web",
    "Fingerprint": "5xJ5r/SKUXZKqQOBwVL9TS9r9MTR6B34kkwc3Qaivyao4H6445IWBgP8TNRWiTjs"
}

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def getCatalog():
    getAllCategories = requests.get(f"{HOST}/categories", headers=HEADERS)
    categories = []

    for category in getAllCategories.json()['categories']:
        categories.append(category['categoryId'])
        if category['subCategories'] is not None:
            for cat in category['subCategories']:
                categories.append(cat['categoryId'])
                if cat['subCategories'] is not None:
                    for c in cat['subCategories']:
                        categories.append(c['categoryId'])
    return categories

def catalog():
    categories = getCatalog()
    PARAMS = {
        "sortDirection": "asc",
        "start": 0,
        "limit": 0
    }
    newItems = 0
    totalItem = 0
    newPrices = 0
    newDiscounts = 0
    for category in tqdm(categories, desc="get Categories"):
        PARAMS['limit'] = 1
        getTotalData = requests.get(f"{HOST}/products/category/{category}", params=PARAMS, headers=HEADERS)

        if getTotalData.status_code >= 400:
            print("ERROR getTotalData")
            sys.exit()

        categoryData = getTotalData.json()

        PARAMS['limit'] = categoryData['totalData']
        getAllItem = requests.get(f"{HOST}/products/category/{category}", params=PARAMS, headers=HEADERS)

        if getAllItem.status_code >= 400:
            print("ERROR getAllItem")
            sys.exit()
        totalItem += len(getAllItem.json()['products'])

        for item in tqdm(getAllItem.json()['products'], desc=f"get {categoryData['currentCategoryName']} items", leave=False):
            
            checkIdItem = db.select(TABLE='items', SELECT='id', WHERE=(db['items']['sku'] == item['sku']) | (db['items']['name'] == item['productName']))
            now = datetime.now(pytz.timezone("Asia/Jakarta"))
            date_today = now.strftime("%Y-%m-%d")
            datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")
            idItem = item['productId']
            
            if len(checkIdItem) == 0:
                db["items"].insert(item['productId'], 
                                   item['sku'], item['productName'], categoryData['currentCategoryName'], item['image'], f"https://alfagift.id/p/{item['productId']}", 'alfagift', datetime_today)
                newItems += 1

            else:
                idItem = checkIdItem[0][0]

            checkItemIdinPrice = db.select(TABLE='prices',
                                           SELECT='id', 
                                           WHERE=(db['prices']['items_id'] == idItem) & 
                                           (db['prices']['created_at'] | LIKE | f'{date_today}%') & 
                                           (db['prices']['price'] == item['finalPrice']))
            if len(checkItemIdinPrice) == 0:
                    db["prices"].insert(shortuuid.uuid(), idItem, item['finalPrice'], "", datetime_today)
                    newPrices += 1

            checkItemIdinDiscount = db.select(TABLE='discounts', 
                                              SELECT='id', 
                                              WHERE=(db['discounts']['items_id'] == idItem) &
                                                (db['discounts']['created_at'] | LIKE | f'{date_today}%') &
                                                (db['discounts']['discount_price'] == item['finalPrice']) &
                                                (db['discounts']['original_price'] == item['basePrice'])
                                             )
            if len(checkItemIdinDiscount) == 0:
                db["discounts"].insert(shortuuid.uuid(), idItem, item['finalPrice'], item['basePrice'], item['discountPercent'], "", datetime_today)                
                newDiscounts += 1

    logging.info(f"=== Finish scrap {totalItem} item by added {newItems} items, {newPrices} prices, {newDiscounts} discounts")
    if newItems ==0 & newPrices==0 & newDiscounts==0:
        logging.info("=== i guess nothing different today")


        
    
    
            
                