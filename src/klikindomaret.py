import requests
import logging
from bs4 import BeautifulSoup

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def promosiMingguIni():

    TARGET_URL = "https://www.klikindomaret.com"
    pageParam = "?categories=&productbrandid=&sortcol=&pagesize=50&startprice=&endprice=&attributes="

    def cleanUpCurrency(price: str) -> int:
        return int(price.replace("Rp", "").replace(".",""))

    def findPromosiLink():
        TARGET_URL = "https://www.klikindomaret.com"
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
                "promotion": {
                    "type": productPromotion,
                    "original_price": productOldPrice
                }
            })
    return products
