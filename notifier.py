import os
import sys
import json
import requests
from datetime import date, timedelta



WEBHOOK_URL = "https://discordapp.com/api/webhooks/781911618702409748/QQ89_tlwWYuT-fUSEkUnPMmJDlH2ohn6rp8bbcIEhL2cHX_8fbLdtE5UGLZ4VbU4fjnR"
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

message = {
    'content': ""
}

for dataToday in data['today']:
    for dataYesterday in data['yesterday']:
        if dataToday['id'] in dataYesterday['id']:
            if float(dataYesterday['price']) > float(dataToday['price']):
                diff = float(dataYesterday['price']) - float(dataToday['price'])
                message['content'] = f"{message['content']}\n{dataToday['name']} is Cheaper {diff}"
                print(f"{dataToday['name']} is Cheaper {diff}")
            elif float(dataYesterday['price']) < float(dataToday['price']):
                diff = float(dataToday['price']) - float(dataYesterday['price'])
                message['content'] = f"{message['content']}\n{dataToday['name']} is Expensive {diff}"
                print(f"{dataToday['name']} is Expensive {diff}")

sendMessage = requests.post(WEBHOOK_URL, json=message, headers={"Content-Type": "application/json"})