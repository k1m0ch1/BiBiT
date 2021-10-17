import requests
import logging
import sys
from bs4 import BeautifulSoup
from inspect import currentframe, getframeinfo

from util import cleanUpCurrency
from discordhook import sendMessage

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
TARGET_URL = "https://www.klikindomaret.com"
pageParam = "?productbrandid=&sortcol=&pagesize=50&startprice=&endprice=&attributes="


def getDataCategories():
    resp = requests.get(TARGET_URL)
    parser = BeautifulSoup(resp.text, 'html.parser')
    categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
    if categoryClass is None:
        frameinfo = getframeinfo(currentframe())
        sM = sendMessage("Scrapper klikindomaret ga berfungsi", f"Error di {frameinfo.filename} {frameinfo.lineno}", "I can't get the categories data on klikindomaret.com probably class `container-wrp-menu bg-white list-shadow list-category-mobile` is changed, go check klikindomaret.com on the categories list")
        return []
    categories = [link.get('href') for link in categoryClass.find_all('a')]
    products = []
    product_Ids = []

    for category in categories:
        category_name = category.split("/")[2]
        category_url = f"{TARGET_URL}{category}"
        getPage = requests.get(category_url)
        logging.info(category_url)
        parser = BeautifulSoup(getPage.text, 'html.parser')
        if parser.find("select", {"id": "ddl-filtercategory-sort"}) is not None:
            getPageList = parser.find("select", {"class": "form-control pagelist"})
            if getPageList is None:
                frameinfo = getframeinfo(currentframe())
                sM = sendMessage("Scrapper klikindomaret ga berfungsi", f"Error di {frameinfo.filename} {frameinfo.lineno}", f"I can't get the PageList from {TARGET_URL}{category}, probably have no data, but please check it first")
                continue
            maxPage = len(getPageList.find_all('option'))

            for page in range(0, maxPage):
                logging.info(f"{category_url}{pageParam}&page={page+1}")
                categoryPage = requests.get(f"{category_url}{pageParam}&page={page+1}&categories={category_name}")
                parser = BeautifulSoup(categoryPage.text, 'html.parser')

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

                    if productID not in product_Ids:
                        product_Ids.append(productID)

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