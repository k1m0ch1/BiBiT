import json
import os
import config
from os import listdir
from os.path import isfile, join

ANALYTIC_FILE = './analytics.json'

if __name__ == "__main__":
    listfiles = [filename for filename in listdir(config.DATA_DIR) if isfile(join(config.DATA_DIR, filename))]

    dataYesterday = []
    dataToday = []
    dataCompile = {}
    for filename in listfiles:

        FILE = open(f"{config.DATA_DIR}/{filename}", "r").read()
        print(f"{config.DATA_DIR}/{filename}")
        each_file = json.loads(FILE)

        for dataToday in each_file['data']:
            if not len(dataYesterday) == 0:
                for dY in dataYesterday['data']:
                    if dataToday['id'] == dY['id']:
                        if dataToday['name'] not in dataCompile:
                            dataCompile[dataToday['name']] = {
                                dataYesterday['date']: dY['price']
                            }
                        dataCompile[dataToday['name']][each_file['date']] = dataToday['price']
        dataYesterday = each_file
    
    file_object = open(f'./analytics.json', 'w+')
    file_object.write(json.dumps(dataCompile))



