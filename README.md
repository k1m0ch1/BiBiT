# BiBiT

<p align='center'>
    <img height=250 width=250 src="https://pbs.twimg.com/profile_images/1334873212824375296/fFV1qAdP_400x400.jpg">
</p>

## Introduction

BiBiT or sprout in english, the bot in purpose to send the notification when the groceries price in `yogyaonline.co.id` is cheaper than yesterday, if you asking what is yogyaonline.co.id is the store that available online or offline, and yogya is one of the big group groceries mall in indonesia, they have Yogya, Griya and Yomart, so to get the groceries price in `yogyaonline.co.id` is the relevan source.

## How the bot work ?

The bot is simply scrap from the page `https://www.yogyaonline.co.id/hotdeals.html` and store this everyday, so you will get a new price everyday. I don't believe with the discount price they offer to us, so to understant if the price is "real" discount, I just simply compare the today price with yesterday price

## The Difference between online and offline store

so far I just fo to the 1 store offline, the online and offline have a different from 1000 - 15000

## List to do

1. prevent the twitter from mark the post as spam
2. made a summary of product list with image and text
2.1 every image held up to 15 item
2.2 using PIL
3. Command
3.1 cheapest item today (with comparison)
3.2 expensive item today (with comparison)
4. SEMBAKO
4.1 List the SEMBAKO ITEM
4.2 analytic the SEMBAKO ITEM in yogya