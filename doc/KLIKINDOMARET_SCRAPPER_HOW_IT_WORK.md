# Klikindomaret scrapper, how it work ?

## getDataCategories()

in the first you will get the data html from index website `https://www.klikindomaret.com` and you need to get all the item categories 

```
    categoryClass = parser.find("div", {"class": "container-wrp-menu bg-white list-shadow list-category-mobile"})
    categories = [link.get('href') for link in categoryClass.find_all('a')]
```

from each categories, go to the link, and scrape all the product to get the data