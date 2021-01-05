import json
import os
import config
from os import listdir
from os.path import isfile, join

if __name__ == "__main__":
    for target in ['yogyaonline', 'alfacart', 'klikindomaret']:
        print(target)
        dataCompile = {}
        for tipe in ['catalog', 'promo']:
            dirr = f"{config.DATA_DIR}/{target}/{tipe}"
            listfiles = [filename for filename in listdir(dirr) if isfile(join(dirr, filename))]
            print("I will merge all of this file")
            print(listfiles)

            dataYesterday = []
            dataToday = []
            for filename in listfiles:

                FILE = open(f"{dirr}/{filename}", "r").read()
                print(f"Load File {dirr}/{filename}")
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
        
        file_object = open(f'./{target}-analytics.json', 'w+')
        file_object.write(json.dumps(dataCompile))



