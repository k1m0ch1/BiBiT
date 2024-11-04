from random import choice

import os
import time
import logging
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def randomWait(min, max):
    wait = choice([i for i in range(min, max)])
    logging.info(f"Wait for {wait} seconds")
    time.sleep(wait)

def cleanUpCurrency(price: str) -> int:
    ggwp = price.replace(" ", "").replace("Rp", "").replace(".000","000")
    if ggwp[-3:] == ".00":
        ggwp = ggwp[:-3]
    ggwp = ggwp.replace(".","").replace("\n","")
    return int(ggwp)

def addRowHealth(reqData):
    username = os.getenv("STEINDB_USERNAME", "")
    password = os.getenv("STEINDB_PASSWORD", "")
    steindb = os.getenv("STEINDB_URL", "")
    req = requests.post(f"{steindb}/Healthcheck",json=[reqData], auth=HTTPBasicAuth(username, password))
    if req.status_code > 300:
        print("dude its error")
