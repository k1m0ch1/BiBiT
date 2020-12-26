import schedule
import time
import logging
import config
import json
import os
import argparse

from datetime import date, timedelta
from notifier import runNotifier
from yogyaonline import hotDealsPage
from klikindomaret import promosiMingguIni
from alfacart import promotion
from config import DATA_DIR

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def jobScrapper(target: str = 'all'):
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    logging.info("=== worker is running")
    prevData = {}

    if target in ['yogyaonline', 'all']:
        logging.info("=== start scrapping yogya")
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

        if not os.path.isdir(f"{DATA_DIR}/yogyaonline"):
            os.mkdir(f"{DATA_DIR}/yogyaonline")

        file_object = open(f'{DATA_DIR}/yogyaonline/{TODAY_STRING}.json', 'w+')
        file_object.write(json.dumps(cData))

        logging.info(f"== scrapping success, saved to {DATA_DIR}/{TODAY_STRING}.json")

    if target in ['klikindomaret', 'all']:
        logging.info("=== start scrapping indomaret")    
        cData = {
            'data': promosiMingguIni(),
            'date': TODAY_STRING
        }

        if not os.path.isdir(f"{DATA_DIR}/indomaret"):
            os.mkdir(f"{DATA_DIR}/indomaret")

        file_object = open(f'{DATA_DIR}/indomaret/{TODAY_STRING}.json', 'w+')
        file_object.write(json.dumps(cData))

        logging.info(f"== scrapping indomaret success, saved to {DATA_DIR}/indomaret/{TODAY_STRING}.json")

    if target in ['alfacart', 'all']:
        logging.info("=== start scrapping alfacart")    
        cData = {
            'data': promotion(),
            'date': TODAY_STRING
        }

        if not os.path.isdir(f"{DATA_DIR}/alfacart"):
            os.mkdir(f"{DATA_DIR}/alfacart")

        file_object = open(f'{DATA_DIR}/alfacart/{TODAY_STRING}.json', 'w+')
        file_object.write(json.dumps(cData))

        logging.info(f"== scrapping alfacart success, saved to {DATA_DIR}/alfacart/{TODAY_STRING}.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process the BiBiT Job')
    parser.add_argument('command', 
        metavar ='command', 
        type=str, 
        choices=['notification', 'scrapping', 'do.notif', 'do.scrap'],
        help='a command to run the bibit Job')
    
    parser.add_argument('--target', 
        metavar ='all, yogyaonline, klikindomaret, alfacart', 
        type=str, 
        default='all',
        choices=['all', 'yogyaonline', 'klikindomaret', 'alfacart'],
        help='choices the target to be scrapped')

    args = parser.parse_args()

    if args.command == 'notification':
        for PRIME_TIME in config.PRIME_TIME:
            logging.info(f"=== notification worker at {PRIME_TIME} is queued")
            schedule.every().day.at(PRIME_TIME).do(runNotifier)

    if args.command == 'scrapping':
        for SCRAPPING_TIME in config.SCRAPPING_TIME:
            logging.info(f"=== scrapper worker at {SCRAPPING_TIME} is queued")
            schedule.every().day.at(SCRAPPING_TIME).do(jobScrapper)

    if args.command == 'do.notif':
        runNotifier()

    if args.command == 'do.scrap':
        jobScrapper(args.target)

    while True:
        schedule.run_pending()
        time.sleep(2)
