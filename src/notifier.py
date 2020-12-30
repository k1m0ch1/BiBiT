import os
import sys
import json
import requests
import logging
import config
import time
import tweepy
from random import randint
from datetime import datetime, timedelta, date
from config import DATA_DIR

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def runNotifier(target: str):
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    logging.info(f"== run the Notifier for {target}")

    def CharacterLimit(platform=str, message=str, data=list) -> list:
        CONFIGURATION = (len(data[len(data)-1])+len(message)) < 2000 if platform == "discord" else \
            (len(data[len(data)-1])+len(message)) < 280
        if CONFIGURATION:
            data[len(data)-1] += message
        else:
            data += [message]

        return data

    def SendMessage(platform=str, dataToday=dict, dataYesterday=dict) -> str:
        ori_diff = float(dataYesterday['price']) - float(dataToday['price'])
        diff = -ori_diff if ori_diff < 0 else ori_diff
        cheap = True if ori_diff > 0 else False
        cheap_text = 'Cheaper 🤑' if cheap else 'Expensive 🙄'
        promotion = f"{dataToday['promotion'].get('type', '')} {dataToday['promotion'].get('description', '')}" if "promotion" in dataToday else ""
        promotion = promotion.replace("\n", "")
        if platform == "discord":
            return f"\n🛒 [{dataToday['name']}]({dataToday['link']}) is {cheap_text} {diff} {promotion}"
        return f"🛒{dataToday['name']} is {cheap_text} {diff} {promotion}" \
            f"\n\n🧮 my calculation is YESTERDAY({dataYesterday['price']}) - TODAY({dataToday['price']}) = {diff} {cheap_text}" \
            f" {dataToday['link']}"


    if not os.path.isfile(f'{DATA_DIR}/{target}/catalog/{YESTERDAY_STRING}.json'):
        print("There is no yesterday data file, you need to wait more")
        return

    TODAY_FILE = open(f"{DATA_DIR}/{target}/catalog/{TODAY_STRING}.json", 'r').read()
    YESTERDAY_FILE = open(f"{DATA_DIR}/{target}/catalog/{YESTERDAY_STRING}.json", 'r').read()

    data = {
        'yesterday': {
            'data': json.loads(YESTERDAY_FILE)['data'],
            'id': [ data['id'] for data in json.loads(YESTERDAY_FILE)['data']]
        },
        'today': {
            'data': json.loads(TODAY_FILE)['data'],
            'id': [ data['id'] for data in json.loads(TODAY_FILE)['data']]
        }
    }

    discord_message = [f"{target.capitalize()} Bot Price Today!\n Formula Yesterday - Today = Cheaper, Today - Yesterday = Expensive"]
    twitter_message = [""]
    

    message_tmp = []

    for dataToday in data['today']['data']:
        if dataToday['id'] in data['yesterday']['id']:
            index = data['yesterday']['id'].index(dataToday['id'])
            diff = float(data['yesterday']['data'][index]['price']) - float(dataToday['price'])
            if diff == 0: 
                continue 
            
            curr_message = {
                "discord": SendMessage("discord", dataToday, data['yesterday']['data'][index]),
                "twitter": SendMessage("twitter", dataToday, data['yesterday']['data'][index])
            }

            if curr_message['discord'] in message_tmp:
                # logging.info("Already Exist, Skip")
                continue

            logging.info(f"{dataToday['name']} is {'Cheap' if diff > 0 and diff != 0 else 'Expensive'} {diff}")

            message_tmp.append(curr_message['discord'])

            discord_message = CharacterLimit("discord", curr_message['discord'], discord_message)
            twitter_message = CharacterLimit("twitter", curr_message['twitter'], twitter_message)

    if config.DISCORD_NOTIFICATION:
        logging.info("== sent to discord")
        for index, message in enumerate(discord_message):
            while True:
                randomize = randint(10, 20)
                if index%5 == 0:
                    randomize = 30
                time.sleep(randomize)
                sendMessage = requests.post(config.DISCORD_WEBHOOK_URL, json={'content': message}, headers={"Content-Type": "application/json"})
                if not sendMessage.status_code == 204:
                    logging.error(f"ERROR, with status code , the message is not sent with value {message}")
                    logging.info("I'll retry send the message")
                else:
                    break
    else:
        logging.info("== sent discord is disabled")
    
    if config.TWITTER_NOTIFICATION:
        logging.info("== sent to twitter")
        auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.TWITTER_API_SECRET_KEY)
        auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)
        
        try:
            parent = api.update_status(f"{target.capitalize()} Price Today! {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} comparison with yesterday")
            parent_id = parent.id_str
            logging.info("Parent Message is created")
            for index, message in enumerate(twitter_message):
                randomize = randint(10, 20)
                if index%5 == 0:
                    randomize = 30    
                logging.info(f"Sent Message to Thread {parent_id} with pause {randomize} second")
                time.sleep(randomize)
                post = api.update_status(message, parent_id)
                parent_id = post.id_str
        except tweepy.TweepError as e:
            logging.info(f"got error code {e.message[0]['code']} with message {e.message[0]['message']} when I want to post for the very first time, I think I'll exit to send to twitter")
    else:
        logging.info("== sent twitter is disabled")

def sendNotification():
    for target in ['yogyaonline', 'alfacart', 'klikindomaret']:
        runNotifier(target)
