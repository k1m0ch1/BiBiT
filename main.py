import schedule
import time
import logging
import config
import json
import os

from scrapper import hotDealsPage
from notifier import runNotifier
from config import DATA_DIR, TODAY_STRING, YESTERDAY_STRING

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def jobScrapper():
    logging.info("=== worker is running")
    prevData = {}

    logging.info("=== start scrapping")
    currData = hotDealsPage()
    compiledData = []
    index = 2
    while not prevData == currData:
        for item in currData:
            compiledData.append(item)
        prevData = currData
        currData = hotDealsPage(page=index)
        index += 1
    
    cData = {
        'data': compiledData,
        'date': TODAY_STRING
    }

    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)

    file_object = open(f'{DATA_DIR}/{TODAY_STRING}.json', 'w+')
    file_object.write(json.dumps(cData))


if __name__ == "__main__":
    logging.info("=== si BiBiT job")
    for PRIME_TIME in config.PRIME_TIME:
        logging.info(f"=== notification worker at {PRIME_TIME} is queued")
        schedule.every().day.at(PRIME_TIME).do(runNotifier)
    
    for SCRAPPING_TIME in config.SCRAPPING_TIME:
        logging.info(f"=== scrapper worker at {SCRAPPING_TIME} is queued")
        schedule.every().day.at(SCRAPPING_TIME).do(jobScrapper)

    while True:
        schedule.run_pending()
        time.sleep(2)