import os
import sys
import json
import requests
from datetime import date, timedelta

def RunNotifier():
    WEBHOOK_URL = "https://discordapp.com/api/webhooks/781911618702409748/QQ89_tlwWYuT-fUSEkUnPMmJDlH2ohn6rp8bbcIEhL2cHX_8fbLdtE5UGLZ4VbU4fjnR"
    print("Run the Notifier")

    DATA_DIR = './data'
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    YESTERDAY_STRING = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    if not os.path.isfile(f'{DATA_DIR}/{YESTERDAY_STRING}.json'):
        print("There is no yesterday data file, you need to wait more")
        sys.exit(0)

    TODAY_FILE = open(f"{DATA_DIR}/{TODAY_STRING}.json", 'r').read()
    YESTERDAY_FILE = open(f"{DATA_DIR}/{YESTERDAY_STRING}.json", 'r').read()

    data = {
        'yesterday': json.loads(YESTERDAY_FILE)['data'],
        'today': json.loads(TODAY_FILE)['data']
    }

    item_message = ["Yogya Bot Price Today!\n Formula Yesterday - Today = Cheaper, Today - Yesterday = Expensive"]

    for dataToday in data['today']:
        for dataYesterday in data['yesterday']:
            if dataToday['id'] in dataYesterday['id']:
                if float(dataYesterday['price']) > float(dataToday['price']):
                    diff = float(dataYesterday['price']) - float(dataToday['price'])
                    curr_message = f"\n[{dataToday['name']}]({dataToday['link']}) is Cheaper {diff}"
                    curr_message += f" {dataToday['promotion']['type']} {dataToday['promotion']['description']}" if "promotion" in dataToday else ""
                    #curr_message += f"--{dataYesterday['price']} - {dataToday['price']} = {diff} CHEAPER"
                    if len(item_message) == 0:
                        item_message.append(curr_message)
                    if (len(item_message[len(item_message)-1])+len(curr_message)) < 2000:
                        item_message[len(item_message)-1] += curr_message
                    else:
                        item_message.append(curr_message)
                    print(f"{dataToday['name']} is Cheaper {diff}")
                elif float(dataYesterday['price']) < float(dataToday['price']):
                    diff = float(dataToday['price']) - float(dataYesterday['price'])
                    curr_message = f"\n[{dataToday['name']}]({dataToday['link']}) is Expensive {diff}"
                    curr_message += f" {dataToday['promotion']['type']} {dataToday['promotion']['description']}" if "promotion" in dataToday else ""
                    #curr_message += f"\n||{dataToday['price']} - {dataYesterday['price']} = {diff} EXPENSIVE||"
                    if len(item_message) == 0:
                        item_message.append(curr_message)
                    if (len(item_message[len(item_message)-1])+len(curr_message)) < 2000:
                        item_message[len(item_message)-1] += curr_message
                    else:
                        item_message.append(curr_message)
                    print(f"{dataToday['name']} is Expensive {diff}")

    for item in item_message:
        sendMessage = requests.post(WEBHOOK_URL, json={'content': item}, headers={"Content-Type": "application/json"})
        if not sendMessage.status_code == 204:
            print(f"ERROR, with status code , the message is not sent with value {message}")