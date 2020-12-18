import requests
import json
import os
import sys
import logging
import urllib3

from bs4 import BeautifulSoup
from math import ceil
from config import DATA_DIR, TODAY_STRING, YESTERDAY_STRING

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

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
        "qtext":"beli-banyak-lebih-murah",
        "filter":[],
        "page": 1,
        "fetch_promotion": True,
        "sort":
        {
            "label":"position",
            "direction":"asc"
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

    cData = {
        'data': compiledData['data'],
        'date': TODAY_STRING
    }

    if not os.path.isdir(f"{DATA_DIR}/alfacart"):
        os.mkdir(f"{DATA_DIR}/alfacart")

    file_object = open(f'{DATA_DIR}/alfacart/{TODAY_STRING}.json', 'w+')
    file_object.write(json.dumps(cData))

    print(f"Total data gathered {len(compiledData['data'])}")
    return compiledData['data']


def catalog():
    TARGET_URL = "https://mapigo.alfacart.com/v5/list/catalog"
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
    CATEGORY_ID = [
        723,
        2277,
        # 2276,
        # 918,
        # 788,
        # 2045,
        # 789,
        # 793,
        # 794,
        # 807,
        # 928,
        # 814,
        # 815,
        # 864
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

    for ID in CATEGORY_ID:
        logging.info(ID)
        BODY['category_id'] = ID
        req = requests.post(TARGET_URL, json=BODY, headers=HEADERS, verify=False)
        data_raw = req.json()
        data = req.json()["result"]["result_products"]
        result_count = req.json()["result"]["result_count"]
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
            logging.info(f'Get All Data')
            max_page = ceil(result_count/200)
            for page in range(1, max_page):
                BODY['page'] = page+1
                logging.info(f'Page {page+1}')
                reqa = requests.post(TARGET_URL, json=BODY, headers=HEADERS, verify=False)
                data = req.json()["result"]["result_products"]
                for itemData in data:
                    if itemData["id"] not in compiledData['listIds']:
                        compiledData['data'].append(itemData)
                        compiledData['listIds'].append(itemData["id"])
                    else:
                        logging.info(f"{itemData['id']} already exist {compiledData['listIds']}")
                        continue
                    

    cData = {
        'data': compiledData['data'],
        'date': TODAY_STRING
    }

    if not os.path.isdir(f"{DATA_DIR}/alfacart"):
        os.mkdir(f"{DATA_DIR}/alfacart")

    file_object = open(f'{DATA_DIR}/alfacart/{TODAY_STRING}-catalog.json', 'w+')
    file_object.write(json.dumps(cData))

    print(f"Total data gathered {len(compiledData['data'])}")

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

