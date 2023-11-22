import requests
import logging
import re
import sys
import shortuuid
from bs4 import BeautifulSoup
from inspect import currentframe, getframeinfo
from tqdm import tqdm
from datetime import datetime

from db import DBSTATE
from util import cleanUpCurrency
from discordhook import sendMessage

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
TARGET_URL = "https://www.klikindomaret.com"

pageParam = "?productbrandid=&sortcol=&pagesize=50&startprice=&endprice=&attributes="
pageParam = {
    "productbrandid": "",
    "sorcol": "",
    "pagesize": 50,
    "startprice": "",
    "endproce": "",
    "attributes": "",
    "page": 0,
    "categories": ""
}

db = DBSTATE


def getDataCategories():
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
    if categoryClass is None:
        frameinfo = getframeinfo(currentframe())
        # sM = sendMessage("Scrapper klikindomaret ga berfungsi", f"Error di {frameinfo.filename} {frameinfo.lineno}", "I can't get the categories data on klikindomaret.com probably class `container-wrp-menu bg-white list-shadow list-category-mobile` is changed, go check klikindomaret.com on the categories list")
        return []
    
    categories = list()
    
    # Untuk Sub_Category yang tidak ada anaknya
    c1 = categoryClass.findAll('span', attrs = {'class':'clickMenu'})
    for c1_element in c1:
        if c1_element.a is not None:
            link = c1_element.find('a')['href']
            categories.append(link)
        
    # Untuk Sub_Category yang ada anaknya
    c2 = categoryClass.findAll('ul', attrs = {'class':'nd-kategori'})
    for c2_element in c2:
        c2_element_menu = c2_element.find('li', attrs = {'class':'menu-seeall'})
        if c2_element_menu is not None:
            link = c2_element_menu.a['href']
            categories.append(link)

    products = []
    product_Ids = []

    for category in tqdm(categories, desc=f"Scrape Category"):
        category_name = category.split("/")[2]
        category_url = f"{TARGET_URL}{category}"
        getPage = requests.get(category_url)
        parser = BeautifulSoup(getPage.text, 'html.parser')
        if parser.find("select", {"id": "ddl-filtercategory-sort"}) is not None:
            getPageList = parser.find("select", {"class": "form-control pagelist"})
            if getPageList is None:
                frameinfo = getframeinfo(currentframe())
                logging.error("Scrapper klikindomaret ga berfungsi")
                # sM = sendMessage("Scrapper klikindomaret ga berfungsi", f"Error di {frameinfo.filename} {frameinfo.lineno}", f"I can't get the PageList from {TARGET_URL}{category}, probably have no data, but please check it first")
                continue
            maxPage = len(getPageList.find_all('option'))
            for page in tqdm(range(0, maxPage), desc=f"Scrape all page from {category_name}", leave=False):
                # logging.info(f"{category_url}{pageParam}&page={page+1}")
                pageParam["page"] = page+1
                pageParam["categories"] = category_name
                categoryPage = requests.get(f"{category_url}", params=pageParam)
                parser = BeautifulSoup(categoryPage.text, 'html.parser')

                getItem = parser.find_all("div", {"id": re.compile("^categoryFilterProduct-")})
                for index, item in enumerate(getItem):
                    # print(products)
                    productID = item.find("div", {'class': f'sendby oksendby classsendby{index+1}'}).get('selecteds')
                    container = item.find('div', {'class': 'wrp-content'})
                    dikirimOleh = container.find('span', {'class': 'sendbyProduct'}).find('span').get('class')
                    dikirimOleh = container.find('span', {'class': 'sendbyProduct'}).find('span', {'class': dikirimOleh})
                    productOldPrice = 0 if container.find('span', {'class': 'strikeout disc-price'}) is None else cleanUpCurrency(container.find('span', {'class': 'strikeout disc-price'}).text.split("\n")[2])
                    productPromotion = 0 if container.find('span', {'class': 'discount'}) is None else container.find('span', {'class': 'discount'}).get_text().replace("\n", "").replace(" ", "")
                    productPrice = container.find('span', {'class': 'normal price-value'}).get_text()

                    item = {
                        'name': container.find('div', {'class': 'title'}).get_text().replace("\n", ""),
                        'id': productID,
                        'sub_category':category_name.replace("-1","").replace("-"," "),
                        'price': cleanUpCurrency(productPrice),
                        'link': f"{TARGET_URL}{item.find('a').get('href')}",
                        'image': item.find('img').get('data-src'),
                        "promotion": {
                            "type": productPromotion,
                            "original_price": productOldPrice
                        }
                    }

                    now = datetime.now()

                    checkIdItem = db.select(TABLE='items', SELECT='id', WHERE=(db['items']['sku'] == item['id']) | (db['items']['name'] == item['name']))
                    if len(checkIdItem) > 0:
                        idItem = checkIdItem[0][0]
                        db["prices"].insert(shortuuid.uuid(), idItem, cleanUpCurrency(productPrice), "", now.strftime("%Y-%m-%d %H:%M:%S"))
                        db["discounts"].insert(shortuuid.uuid(), idItem, item['price'], productOldPrice, productPromotion, "", now.strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        idItem = shortuuid.uuid()
                        db["items"].insert(idItem, item['id'], item['name'], item['sub_category'], item['image'], item['link'], 'klikindomaret', now.strftime("%Y-%m-%d %H:%M:%S"))
                    
                    
                    if productID not in product_Ids:
                        product_Ids.append(productID)

                        products.append(item)
                    else:
                        # logging.info(f"Product {productName} is already exist, skip this item")
                        continue
    return products
        

def promosiMingguIni():
    def findPromosiLink():
        indexPage = requests.get(TARGET_URL)

        parser = BeautifulSoup(indexPage.text, 'html.parser')

        promosiCaption = parser.find_all("div", {"class": "text-top-promo clearfix"})

        for item in promosiCaption:
            getCaption = item.find("div", {"class": "tagline col-xs-6"}).get_text().replace("\n", "")
            if getCaption == "Promosi Minggu Ini":
                getLink = item.find("div", {"class": "seemore col-xs-6 text-right"})
                return getLink.find('a').get('href')

    promosiLink = findPromosiLink()

    import pdb; pdb.set_trace()

    # need to validate if the link is valid

    getPage = requests.get(f"{promosiLink}")

    parser = BeautifulSoup(getPage.text, 'html.parser')

    getPageList = parser.find("select", {"class": "form-control pagelist"})
    maxPage = len(getPageList.find_all('option'))

    products = []
    for page in range(0, maxPage):
        logging.info(f"{promosiLink}{pageParam}&page={page+1}")
        promotionPage = requests.get(f"{promosiLink}{pageParam}&page={page+1}")
        parser = BeautifulSoup(promotionPage.text, 'html.parser')

        getItem = parser.find_all("div", {"class": "box-item clearfix"})
        for index, item in enumerate(getItem[0].find_all("div", {"class": "item"})):
            link = f"{TARGET_URL}{item.find('a').get('href')}"
            image = item.find('img').get('data-src')
            productID = item.find("div", {'class': f'sendby oksendby classsendby{index+1}'}).get('selecteds')
            container = item.find('div', {'class': 'wrp-content'})
            dikirimOleh = container.find('span', {'class': 'sendbyProduct'}).find('span').get('class')
            dikirimOleh = container.find('span', {'class': 'sendbyProduct'}).find('span', {'class': dikirimOleh})
            productName = container.find('div', {'class': 'title'}).get_text().replace("\n", "")
            productOldPrice = "" if container.find('span', {'class': 'strikeout disc-price'}) is None else cleanUpCurrency(container.find('span', {'class': 'strikeout disc-price'}).text.split("\n")[0])
            productPromotion = "" if container.find('span', {'class': 'discount'}) is None else container.find('span', {'class': 'discount'}).get_text().replace("\n", "")
            productPrice = container.find('span', {'class': 'normal price-value'}).get_text().replace("\n", "")

            products.append({
                'name': productName,
                'id': productID,
                'price': cleanUpCurrency(productPrice),
                'link': link,
                'image': image,
                "promotion": {
                    "type": productPromotion,
                    "original_price": productOldPrice
                }
            })
    return products
