import requests
import json
import os
import logging
import sys

from datetime import date, timedelta
from math import ceil
from config import DATA_DIR
from util import randomWait

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def retry(reqa):
    logging.error("Weird Errror, here is the error")
    print(reqa.status_code)
    print(reqa.text)
    logging.info("I'll retry and lets relax")
    randomWait(60, 90)

def promotion():
    TARGET_URL = "https://mapigo.alfacart.com/v5/promotion"
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "application": "web",
        "DNT": "1",
        "Host": "mapigo.alfacart.com",
        "id": "testzikki",
        "token": "_fXEbpLRVYsAn4IQzeWhnsJdfWbCART_sFfMZ14ggF42NnnO0vyJJkE=",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    BODY = {
        "qtext": "beli-banyak-lebih-murah",
        "filter": [],
        "page": 1,
        "fetch_promotion": True,
        "sort":
        {
            "label": "position",
            "direction": "asc"
        },
        "rows": 999999
    }
    PROMO_CODE = [
        "groceries-great-sale",
        "duniabundadansikecil",
        "minyak-goreng",
        "minumansegardanhemat",
        "cemilansehatdanhemat",
        "kesehatanperawatantubuh",
        "kebutuhandapurbunda",
        "kebutuhanrumahtangga",
        "beli-banyak-lebih-murah"
    ]

    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    try:
        requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass

    compiledData = {
        "data": [],
        "listIds": []
    }

    for code in PROMO_CODE:
        logging.info(code)
        BODY['qtext'] = code
        req = requests.post(TARGET_URL, json=BODY, headers=HEADERS, verify=False)
        data_raw = req.json()
        data = req.json()["result"]["result_products"]
        logging.info(f'{req.json()["result"]["result_count"]} and actual {len(data)}')
        if len(compiledData) == 0:
            compiledData['data'] += data
            for itemData in data:
                compiledData['listIds'].append(itemData["id"])
        else:
            for itemData in data:
                if itemData["id"] not in compiledData['listIds']:
                    compiledData['data'].append(itemData)
                    compiledData['listIds'].append(itemData["id"])
                else:
                    continue

    return compiledData['data']


def catalog():
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    TARGET_URL = "https://mapigo.alfacart.com/v5/list/catalog"
    CATALOG_URL = "https://mapigo.alfacart.com/v5/home/categories"
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "application": "web",
        "DNT": "1",
        "Host": "mapigo.alfacart.com",
        "id": "testzikki",
        "token": "_fXEbpLRVYsAn4IQzeWhnsJdfWbCART_sFfMZ14ggF42NnnO0vyJJkE=",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    BODY = {
        "category_id":799,
        "filter":[],
        "page":1,
        "fetch_promotion":True,
        "sort":{
            "label":"position",
            "direction":"asc"
        },
        "rows": 200
    }

    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    try:
        requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass

    compiledData = {
        "data": [],
        "listIds": [],
        "categories_id": []
    }

    resp_category = requests.get(CATALOG_URL, headers=HEADERS, verify=False)
    categories = resp_category.json()['categories']
    compiledData['categories_id'] += categories

    for categories in compiledData['categories_id']:
        logging.info(categories['id'])
        BODY['category_id'] = categories['id']
        randomWait(5, 10)
        req = requests.post(TARGET_URL, json=BODY, headers=HEADERS, verify=False)
        data_raw = req.json()
        result = req.json()["result"]
        data = result["result_products"]
        result_count = result["result_count"]
        logging.info(f'{result_count} and actual {len(data)}')
        if len(compiledData) == 0:
            compiledData['data'] += data
            for itemData in data:
                compiledData['listIds'].append(itemData["id"])
        else:
            for itemData in data:
                if itemData["id"] not in compiledData['listIds']:
                    compiledData['data'].append(itemData)
                    compiledData['listIds'].append(itemData["id"])
                else:
                    continue

        if result_count > len(data):
            max_page = ceil(result_count/200)
            logging.info(f'Get {result_count} in total from {max_page} page') 
            for page in range(1, max_page):
                BODY['page'] = page+1
                logging.info(BODY)
                while True:
                    # if BODY['page'] % 3 == 0:
                    #     randomWait()
                    reqa = requests.post(TARGET_URL, json=BODY, headers=HEADERS, verify=False)
                    if reqa.status_code == 200:
                        if "result" in reqa.json():
                            data = reqa.json()["result"]["result_products"]
                            for itemData in data:
                                if itemData["id"] not in compiledData['listIds']:
                                    compiledData['data'].append(itemData)
                                    compiledData['listIds'].append(itemData["id"])
                            break
                        else:
                            retry(reqa)
                            continue
                    else:
                        retry(reqa)
                        continue
                        
                    
    return compiledData['data']

'''
{
    'id': 114759, 
    'sku': 'A10480000010', 
    'type': 'simple', 
    'name': 'SARI ROTI Roti Isi Cokelat 72gr', 
    'price': 6000, 
    'special_price': 6000, 
    'min_sale_qty': 1, 
    'max_sale_qty': 999, 
    'increment_qty': 1, 
    'show_price_flag': False, 
    'strike_through_flag': False, 
    'discount_percent': 0, 
    'discount_percent_flag': False, 
    'is_new': False, 
    'image': 'https://cs1.alfacart.com/product/1/1_A10480000010_20201216184729166_small.jpg', 
    'desc': '<li>Roti isi pasta cokelat yang lezat</li><li>Dibuat dari paduan tepung terigu dan bahan pilihan</li><li>Mengenyangkan karena kandungan karbohidrat sebesar 40gr</li>', 
    'special_date_start': '2020-12-16 05:33:00', 
    'special_date_end': '2020-12-31 23:59:00', 
    'created_at': '2016-06-26 16:35:48', 
    'url': 'https://www.alfacart.com/product/sari-roti-roti-isi-cokelat-72gr-114759', 
    'rating': 5, 
    'rating_count': 0, 
    'seller_id': 5659, 
    'seller_title': 'Alfamart', 
    'seller_url': 'https://www.alfacart.com/seller/alfamart-5659', 
    'flash_start_date': '', 
    'flash_end_date': '', 
    'flash_start_time': '', 
    'flash_end_time': '', 
    'flash_start_time_l': 0, 
    'flash_end_time_l': 0, 
    'flash_min': 0, 
    'is_flash': False, 
    'flash_max_usage': 0, 
    'flash_usage': 0, 
    'reviews': [], 
    'brand': 'SARI ROTI', 
    'temp_cart_qty': 0, 
    'loading': False, 
    'max_qty_per_day': 999}
'''

