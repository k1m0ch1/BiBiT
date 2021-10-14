import json
import os
import config
from os import listdir
from datetime import date, datetime
from os.path import isfile, join

def genAnalytic():
    for target in ['yogyaonline']:
        print(target)
        getLatestDate = date.today().strftime("%Y-%m-%d")
        FILE_NAME = f'./{target}-analytics.json'
        dataCompile = {"gathered_date": []}
        if os.path.exists(FILE_NAME):
            file_object = open(FILE_NAME).read()
            data = json.loads(file_object)
            if "gathered_date" in data:
                getLatestDate = json.loads(file_object)["gathered_date"]
            dataCompile = json.loads(file_object)
        else:
            file_object = open(f'./{target}-analytics.json', 'w+')
            file_object.write(json.dumps({"gathered_date": []}))
            file_object.close()

        for tipe in ['catalog', 'promo']:
            print(f"Generate data {tipe}")
            dirr = f"{config.DATA_DIR}/{target}/{tipe}"
            listfiles = [filename for filename in listdir(dirr) if isfile(join(dirr, filename))]
            print("I will merge all of this file")

            for filename in listfiles:

                file_object = open(FILE_NAME).read()
                data = json.loads(file_object)
                getLatestDate = date.today().strftime("%Y-%m-%d")
                if "gathered_date" in data:
                    getLatestDate = data["gathered_date"]
                dataCompile = json.loads(file_object)

                NOW = filename.split(".json")[0]

                if NOW in getLatestDate:
                    print(f"File {dirr}/{filename} already gathered, skipped")
                    continue
                
                FILEOPEN = open(f"{dirr}/{filename}", "r").read()
                print(f"Load File {dirr}/{filename}")
                each_file = json.loads(FILEOPEN)

                for dataToday in each_file['data']:
                    if dataToday['name'] not in dataCompile:
                        dataCompile[dataToday['name']] = {
                            NOW: dataToday['price']
                        }
                    dataCompile[dataToday['name']][each_file['date']] = dataToday['price']
                    if NOW not in dataCompile["gathered_date"]:
                        dataCompile["gathered_date"].append(NOW)

                file_object = open(f'./{target}-analytics.json', 'w+')
                file_object.write(json.dumps(dataCompile))


if __name__ == "__main__":
    genAnalytic()

