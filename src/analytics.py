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
        dataCompile = {"latest_date": ""}
        if os.path.exists(FILE_NAME):
            file_object = open(FILE_NAME).read()
            data = json.loads(file_object)
            if "latest_date" in data:
                getLatestDate = json.loads(file_object)["latest_date"]
            dataCompile = json.loads(file_object)
        else:
            file_object = open(f'./{target}-analytics.json', 'w+')
            file_object.write(json.dumps({"latest_date": ""}))
            file_object.close()

        for tipe in ['catalog']:
            print(f"Generate data {tipe}")
            dirr = f"{config.DATA_DIR}/{target}/{tipe}"
            listfiles = [filename for filename in listdir(dirr) if isfile(join(dirr, filename))]
            print("I will merge all of this file")

            for filename in listfiles[:10]:

                file_object = open(FILE_NAME).read()
                data = json.loads(file_object)
                getLatestDate = date.today().strftime("%Y-%m-%d")
                if "latest_date" in data:
                    getLatestDate = "1990-10-10" if data["latest_date"] == "" else data["latest_date"]
                dataCompile = json.loads(file_object)

                NOW = filename.split(".json")[0]
                NOWDATE = datetime.strptime(NOW, '%Y-%m-%d')
                LASTDATE = datetime.strptime(getLatestDate, '%Y-%m-%d')

                if NOWDATE <= LASTDATE and getLatestDate != "":
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
                    dataCompile["latest_date"] = NOW

                file_object = open(f'./{target}-analytics.json', 'w+')
                file_object.write(json.dumps(dataCompile))


if __name__ == "__main__":
    genAnalytic()

