import os
import sys
import json
import requests
import logging
import config
import time
import tweepy
from random import randint
from datetime import date, timedelta, datetime

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def RunNotifier():

    WEBHOOK_URL = "https://discordapp.com/api/webhooks/781911618702409748/QQ89_tlwWYuT-fUSEkUnPMmJDlH2ohn6rp8bbcIEhL2cHX_8fbLdtE5UGLZ4VbU4fjnR"
    logging.info("Run the Notifier")

    DATA_DIR = './data'
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    def CharacterLimit(platform=str, message=str, data=list) -> list:
        CONFIGURATION = (len(data[len(data)-1])+len(message)) < 2000 if platform == "discord" else \
            (len(data[len(data)-1])+len(message)) < 200
        if CONFIGURATION:
            data[len(data)-1] += message
        else:
            data += [message]

        return data

    def SendMessage(platform=str, dataToday=dict, dataYesterday=dict) -> str:
        ori_diff = float(dataYesterday['price']) - float(dataToday['price'])
        diff = ori_diff * -1 if ori_diff < 0 else ori_diff
        cheap = True if ori_diff > 0 else False
        logging.info(f"{dataToday['name']} is {'Cheaper' if cheap else 'Expensive'} {diff}")
        promotion = f"{dataToday['promotion']['type']} {dataToday['promotion']['description']}" if "promotion" in dataToday else ""
        if platform == "discord":
            return f"\n[{dataToday['name']}]({dataToday['link']}) is {'Cheaper' if cheap else 'Expensive'} {diff} {promotion}"
        return f"{dataToday['name']} is {'Cheaper' if cheap else 'Expensive'} {diff} {promotion}" \
            f" YESTERDAY({dataYesterday['price']}) - TODAY({dataToday['price']}) = {ori_diff} {'Cheaper' if cheap else 'Expensive'}" \
            f" {dataToday['link']}"


    if not os.path.isfile(f'{DATA_DIR}/{YESTERDAY_STRING}.json'):
        print("There is no yesterday data file, you need to wait more")
        sys.exit(0)

    TODAY_FILE = open(f"{DATA_DIR}/{TODAY_STRING}.json", 'r').read()
    YESTERDAY_FILE = open(f"{DATA_DIR}/{YESTERDAY_STRING}.json", 'r').read()

    data = {
        'yesterday': json.loads(YESTERDAY_FILE)['data'],
        'today': json.loads(TODAY_FILE)['data']
    }

    discord_message = ["Yogya Bot Price Today!\n Formula Yesterday - Today = Cheaper, Today - Yesterday = Expensive"]
    twitter_message = [""]

    for dataToday in data['today']:
        for dataYesterday in data['yesterday']:
            if dataToday['id'] in dataYesterday['id']:
                if float(dataYesterday['price']) - float(dataToday['price']) == 0:
                    continue

                curr_message = {
                    "discord": SendMessage("discord", dataToday, dataYesterday),
                    "twitter": SendMessage("twitter", dataToday, dataYesterday)
                }

                discord_message = CharacterLimit("discord", curr_message['discord'], discord_message)
                twitter_message = CharacterLimit("twitter", curr_message['twitter'], twitter_message)

    for message in discord_message:
        sendMessage = requests.post(WEBHOOK_URL, json={'content': message}, headers={"Content-Type": "application/json"})
        if not sendMessage.status_code == 204:
            logging.error(f"ERROR, with status code , the message is not sent with value {message}")
    
    auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.TWITTER_API_SECRET_KEY)
    auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    parent = api.update_status(f"Yogya Bot Price Today! {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    parent_id = parent.id_str
    logging.info("Parent Message is created")
    for message in twitter_message:
        randomize = randint(4, 10)
        logging.info(f"Sent Message to Thread {parent_id} with pause {randomize} second")
        time.sleep(randomize)
        api.update_status(message, parent_id)