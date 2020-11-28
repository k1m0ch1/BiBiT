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

def scrapper(page=1, limit=80):
    TARGET_URL = f"https://www.yogyaonline.co.id/hotdeals.html?p={page}&product_list_limit={limit}"
    logging.info(f"Run the Scrapper page {page} and limit {limit}")
    req = requests.get(TARGET_URL)

    parse = BeautifulSoup(req.text, 'html.parser')

    p = re.compile('var dlObjects = (.*);')
    found = ""
    for script in parse.find_all("script", {"src":False}):
        if script:
           m = p.search(script.string)
           if m is not None:
               found = m.group().replace("var dlObjects =", "")
               found = found.replace(";", "")

    dataEcommerce = json.loads(found)[0]['ecommerce']
    dataHotDealsProduct = dataEcommerce['impressions']
    return dataHotDealsProduct

if __name__ == "__main__":
    prevData = {}
    currData = scrapper()
    compiledData = []
    index = 2
    while not prevData == currData:
        for item in currData:
            compiledData.append(item)
        prevData = currData
        currData = scrapper(page=index)
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

logging.error(f"I'm at {__name__}")
