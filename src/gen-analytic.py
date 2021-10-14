import json
import os
import config
from os import listdir
from datetime import date
from os.path import isfile, join

if __name__ == "__main__":
    for target in ['yogyaonline']:
        print(target)
        getLatestDate = date.today().strftime("%Y-%m-%d")
        FILENAME = f'./{target}-analytics.json'
        dataCompile = {"latest_date": ""}
        if os.path.exists(FILENAME):
            file_object = open(FILENAME).read()
            getLatestDate = json.loads(file_object)["latest_date"]
            dataCompile = json.loads(file_object)
        else:
            file_object = open(f'./{target}-analytics.json', 'w+')
            file_object.write("")

        for tipe in ['catalog', 'promo']:
            print(f"Generate data {tipe}")
            dirr = f"{config.DATA_DIR}/{target}/{tipe}"
            listfiles = [filename for filename in listdir(dirr) if isfile(join(dirr, filename))]
            print("I will merge all of this file")

            for filename in listfiles:

                NOW = filename.split(".json")[0]

                FILE = open(f"{dirr}/{filename}", "r").read()
                print(f"Load File {dirr}/{filename}")
                each_file = json.loads(FILE)

                for dataToday in each_file['data']:
                    if dataToday['name'] not in dataCompile:
                        dataCompile[dataToday['name']] = {
                            NOW: dataToday['price']
                        }
                    dataCompile[dataToday['name']][each_file['date']] = dataToday['price']
                    dataCompile["latest_date"] = NOW

                file_object = open(f'./{target}-analytics.json', 'w+')
                file_object.write(json.dumps(dataCompile))



