import sys
import time
import config
import logging
from datetime import datetime
import schedule
import argparse
import requests

from crawler.yogyaonline import getCategories as yogyaCategories
from crawler.klikindomaret import getDataCategories as indoCategories
from crawler.alfagift import catalog as alfaCatalog
from util import addRowHealth

import uvicorn

from fastapi import FastAPI
from routes import root, belanja

app = FastAPI(redoc_url=None, docs_url=None)

app.include_router(root.router)
app.include_router(belanja.router)
#app.include_router(yogyaonline.router)

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def dataScrap(target: str):
  
    started_at= datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if target == 'yogyaonline':
       output= yogyaCategories() 
   
    if target == 'klikindomaret':
       output= indoCategories()

    if target == 'alfagift':
       output= alfaCatalog()

    finished_at= datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    running_at = requests.get("https://ipinfo.io/ip")

    addRowHealth({
        "task": f"Crawling {target}",
        "status": "Completed",
        "output": "" if len(output) == 0 else output,
        "running_at": running_at.text,
        "health_of": target,
        "started_at": started_at,
        "finished_at": finished_at
    })

    return True

def jobScrapper(target: str = 'all'):
    logging.info(f"=== worker target to {target} is running")

    if target == 'all':
        for itemTarget in ['yogyaonline', 'alfagift', 'klikindomaret']:
            job = dataScrap(itemTarget)
            if not job:
                logging.error("Fail Scrapping")
    else:
        job = dataScrap(target)
        if not job:
            logging.error("Fail Scrapping")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process the BiBiT Job')
    parser.add_argument('command', 
        metavar ='command', 
        type=str, 
        choices=['do.scrap', 'web.api'],
        help='a command to run the bibit Job, the choices is `notif`, `scrap`, `do.notif` and `do.scrap` ')
    
    parser.add_argument('--target', 
        metavar ='all, yogyaonline, klikindomaret, alfagift', 
        type=str, 
        default='all',
        choices=['all', 'yogyaonline', 'klikindomaret', 'alfagift'],
        help='choices the target to be scrapped')

    args = parser.parse_args()
    
    logging.info(f"=== The scrapper for {args.target} is running")

    if args.command == 'scrap':
        for SCRAPPING_TIME in config.SCRAPPING_TIME:
            logging.info(f"=== scrapper worker at {SCRAPPING_TIME} is queued")
            schedule.every().day.at(SCRAPPING_TIME).do(jobScrapper, target=args.target)

    if args.command == 'do.scrap':
        jobScrapper(args.target)
        sys.exit(1)

    if args.command == 'web.api':
        uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level="info", reload=True)
        sys.exit()

    while True:
        schedule.run_pending()
        time.sleep(2)
