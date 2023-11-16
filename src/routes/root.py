from fastapi import APIRouter, Depends
from db import DBSTATE
import sqllex as sx
from sqllex.constants import LIKE, ON
from pydantic import BaseModel


db = DBSTATE

router = APIRouter()

class Search(BaseModel):
    query: str

@router.get("/lol")
def lol():
    return {"message": "Halo bang"}

@router.post("/search")
def search(search: Search):
    items = db.select(
        TABLE='items',
        SELECT=[
            db['items']['name'],
            db['items']['link'],
            db['items']['source'],
            db['items']['image'],
            db['prices']['price']
        ],
        JOIN=(
            (
                sx.INNER_JOIN, db['prices'],
                ON, db['items']['id'] == db['prices']['items_id']
            )
        ),
        WHERE=(
            (db['items']['name'] |LIKE| f'%{search.query}%')
        ),
        GROUP_BY=[
            db['items']['name']
        ]
    )
    result = []
    for item in items:
        dataModels = {
            "name": item[0],
            "link": item[1],
            "source": item[2],
            "image": item[3],
            "prices": item[4]
        }
        result.append(dataModels)
    # items = db.executescript(
    #     """
    #     SELECT DISTINCT
    #         items.name, 
    #         items.link, 
    #         items.source, 
    #         items.image, 
    #         prices.price, 
    #         prices.created_at, 
    #         discounts.discount_price, 
    #         discounts.original_price, 
    #         discounts.percentage
    #     FROM
    #         items
    #         INNER JOIN
    #         prices
    #         ON 
    #             items.id = prices.items_id
    #         INNER JOIN
    #         discounts
    #         ON 
    #             items.id = discounts.items_id
    #     WHERE
    #         items.name LIKE '%mimi%susu%'
    #     """
    # )
    # print(items)
    return result