import re
import pytz
import requests
import logging
import shortuuid

from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime

from db import DBSTATE
from util import cleanUpCurrency


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
    newItems = 0
    totalItem = 0
    newPrices = 0
    newDiscounts = 0
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
    if categoryClass is None:
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

    for category in tqdm(categories, desc="Scrape Category"):
        category_name = category.split("/")[2]
        category_url = TARGET_URL+category
        getPage = requests.get(category_url)
        parser = BeautifulSoup(getPage.text, 'html.parser')
        if parser.find("select", {"id": "ddl-filtercategory-sort"}) is not None:
            getPageList = parser.find("select", {"class": "form-control pagelist"})
            if getPageList is None:
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
                    if container.find('span', {'class': 'strikeout disc-price'}) is None:
                        productOldPrice = 0
                    else:
                        mantap = container.find('span', {'class': 'strikeout disc-price'}).text.split("\n")
                        if len(mantap)>2:
                            productOldPrice = mantap[2]
                        else:
                            print(f"{mantap} - DUDE INI ANEH SIH")
                            productOldPrice = 0
                        

                    # productOldPrice = 0 if container.find('span', {'class': 'strikeout disc-price'}) is None else cleanUpCurrency(container.find('span', {'class': 'strikeout disc-price'}).text.split("\n")[2])
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
                    totalItem += 1


                    now = datetime.now(pytz.timezone("Asia/Jakarta"))
                    date_today = now.strftime("%Y-%m-%d")
                    datetime_today = now.strftime("%Y-%m-%d %H:%M:%S")

                    reqQuery = {
                        'script': "SELECT id FROM items WHERE sku=? OR name=?",
                        'values': (item['id'], item['name'])
                    }
                    checkIdItem = db.execute(**reqQuery)
                    idItem = shortuuid.uuid()

                    if len(checkIdItem) == 0:
                        db["items"].insert(idItem, item['id'], item['name'], 
                                           item['sub_category'], item['image'], item['link'], 
                                           'klikindomaret', datetime_today)
                        newItems += 1
                    else:
                        idItem = checkIdItem[0][0]

                    reqQuery = {
                        'script': "SELECT id FROM prices WHERE items_id=? AND created_at LIKE ? AND price=?",
                        'values': (idItem, f'{date_today}%', item['price'])
                    }
                    checkItemIdinPrice = db.execute(**reqQuery)
                    
                    if len(checkItemIdinPrice) == 0:
                        db["prices"].insert(shortuuid.uuid(), idItem, item['price'], "", datetime_today)
                        newPrices += 1

                    reqQuery = {
                        'script': "SELECT id FROM discounts WHERE items_id=? AND created_at LIKE ? AND discount_price=? AND original_price=?",
                        'values': (idItem, f'{date_today}%', item['price'], productOldPrice)
                    }
                    checkItemIdinDiscount = db.execute(**reqQuery)

                    if len(checkItemIdinDiscount) == 0:
                        db["discounts"].insert(shortuuid.uuid(), idItem, item['price'], productOldPrice, productPromotion, "", datetime_today)
                        newDiscounts += 1
                    
                    if productID not in product_Ids:
                        product_Ids.append(productID)

                        products.append(item)
                    else:
                        # logging.info(f"Product {productName} is already exist, skip this item")
                        continue
    logging.info(f"=== Finish scrap {totalItem} item by added {newItems} items, {newPrices} prices, {newDiscounts} discounts")
    if newItems ==0 & newPrices==0 & newDiscounts==0:
        logging.info("=== i guess nothing different today")
    return products
