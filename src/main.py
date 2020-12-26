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

def dataScrap(target: str):
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    prevData = {}
    cData = {}
    if target == 'yogyaonline':
        currData = hotDealsPage()
        compiledData = []
        index = 2
        while not prevData == currData:
            for item in currData:
                compiledData.append(item)
            prevData = currData
            currData = hotDealsPage(page=index)
            index += 1
        cData = {'data': compiledData, 'date': TODAY_STRING }
    
    if target == 'klikindomaret':
        cData = {'data': promosiMingguIni(), 'date': TODAY_STRING }

    if target == 'alfacart':
        cData = {'data': promotion(), 'date': TODAY_STRING }

    if not os.path.isdir(f"{DATA_DIR}/{target}"):
        os.mkdir(f"{DATA_DIR}/{target}")

    file_object = open(f'{DATA_DIR}/{target}/{TODAY_STRING}.json', 'w+')
    file_object.write(json.dumps(cData))

    logging.info(f"== scrapping {target} success, saved to {DATA_DIR}/{target}/{TODAY_STRING}.json")

def jobScrapper(target: str = 'all'):
    logging.info("=== worker is running")

    if target == 'all':
        for itemTarget in ['yogyaonline', 'alfacart', 'klikindomaret']:
            job = dataScrap(itemTarget)
            if not job:
                log.Println("Fail Scrapping")
    else:
        job = dataScrap(target)
        if not job:
            log.Println("Fail Scrapping")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process the BiBiT Job')
    parser.add_argument('command', 
        metavar ='command', 
        type=str, 
        choices=['notif', 'scrap', 'do.notif', 'do.scrap'],
        help='a command to run the bibit Job')
    
    parser.add_argument('--target', 
        metavar ='all, yogyaonline, klikindomaret, alfacart', 
        type=str, 
        default='all',
        choices=['all', 'yogyaonline', 'klikindomaret', 'alfacart'],
        help='choices the target to be scrapped')

    args = parser.parse_args()

    if args.command == 'notif':
        for PRIME_TIME in config.PRIME_TIME:
            logging.info(f"=== notification worker at {PRIME_TIME} is queued")
            schedule.every().day.at(PRIME_TIME).do(runNotifier)

    if args.command == 'scrap':
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
