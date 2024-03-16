# BiBiT

<p align='center'>
    <img height=250 width=250 src="https://pbs.twimg.com/profile_images/1334873212824375296/fFV1qAdP_400x400.jpg">
</p>

## Introduction

BiBiT or sprout in english, the main purpose of this bot is to send the notification when the groceries price in `yogyaonline.co.id` `alfacart.com` and `klikindomaret.com` is changed within expensive or cheaper, the main feature of this bot is to scrap wether is `all item` or `only promotion` items in the website.

## How the bot work ?

This section is explain how the scrapper work, there is a two type of items "promotion" and "catalog" where the promotion only have an information that items have a promotion, the different with catalog is storing all information about the items.

The vendor have a different format of name, but this scrapper is using the same model data

```
[
    "data": [
        {
            "name": "string",
            "id": "string",
            "price": "string",
            "brand": "string nullable",
            "category": "string enum",
            "list": "string enum",
            "position": int,
            "link": "string",
            "promotion": {
                "type": "string enum discount/promo",
                "description": "",
                "original_price": ""
            }
        }
    ]
]
```

and after data is compiled, it will be saved as date file name with JSON format (ex: `2020-12-12.json`) with the format json as explained above.


## The Difference between online and offline store

so far I just fo to the 1 store offline, the online and offline have a different from 1000 - 15000

## How to use

I recommended export the variable `DATA_DIR` where the data file will be stored

run the following command `python3 src/main.py -h` will show the help like this

```
usage: main.py [-h] [--target all, yogyaonline, klikindomaret, alfacart] [--scrap all, promo, catalog] command

Process the BiBiT Job

positional arguments:
  command               a command to run the bibit Job, the choices is `notif`, `scrap`, `do.notif` and `do.scrap`

optional arguments:
  -h, --help            show this help message and exit
  --target all, yogyaonline, klikindomaret, alfacart
                        choices the target to be scrapped
  --scrap all, promo, catalog
                        choices the items type you want to get
```

## Command

### scrap

if you run `python3 src/main.py scrap` you will be scheduler scrapping following with the optinal arguments

### notif

if you run `python3 src/main.py notif` you will be scheduler notification to discord and twitter following with the optinal arguments

### do.scrap

if you run `python3 src/main.py do.scrap`, the program will scrapping following with the optinal arguments

### do.notif

if you run `python3 src/main.py do.notif`, the program will sent notification following with the optinal arguments

# List todo

1. made a public discord bot
