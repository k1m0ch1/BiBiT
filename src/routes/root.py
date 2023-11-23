from fastapi import APIRouter, Depends
from db import DBAPI
import sqllex as sx
from sqllex.constants import  ON, LIKE
import shortuuid
from pydantic import BaseModel
from typing import Union
from datetime import date, timedelta
from datetime import datetime


db = DBAPI

router = APIRouter()

class Search(BaseModel):
    query: str
    source: Union[str, None] = None
    date: Union[str, None] = None

class Sama(BaseModel):
    item_id: str
    with_item_id: str

@router.get("/")
def lol():
    return {"message": "Misi bwang, API bikinan k1m0ch1 ama r17x"}

@router.get("/stat")
def stat():
    return {"message": "Misi bwang, API bikinan k1m0ch1 ama r17x"}

#@router.post("/sama")
def sama(sama: Sama):
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    db["item_item"].insert(
        shortuuid.uuid(), 
        sama.item_id, sama.with_item_id, "PROPOSED", now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S"))

@router.post("/search")
def search(search: Search):
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    today = now.strftime("%Y-%m-%d")
    querySearch = f'%{search.query}%'
    searchCondition =  (db['items']['source'] != 'alfacart') & (db['items']['name'] |LIKE| querySearch) & (db['prices']['created_at'] |LIKE| f'{today}%')
    if search.source is not None:
        searchCondition = (searchCondition & (db['items']['source'] == search.source)) if len(search.source) > 0 else searchCondition
    items = db.select(
        TABLE='items',
        SELECT=[
            db['items']['id'],
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
        WHERE=searchCondition,
        ORDER_BY=(db['prices']['price'], 'ASC'),
        GROUP_BY=[
            db['items']['name']
        ]
    )
    result = []
    for item in items:
        dataModels = {
            "id": item[0],
            "name": item[1],
            "link": item[2],
            "source": item[3],
            "image": item[4],
            "prices": item[5]
        }
        if item[5] > 99:
            result.append(dataModels)
    return result