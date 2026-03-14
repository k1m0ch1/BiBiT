from fastapi import APIRouter, Query
from db import DBAPI
import sqllex as sx
from sqllex.constants import  ON, LIKE
import shortuuid
from pydantic import BaseModel
from typing import Union
from datetime import datetime, timedelta
import pytz


db = DBAPI

router = APIRouter()

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

@router.get("/search")
def search(
    query: str = Query(...),
    source: Union[str, None] = Query(default=None),
    date: Union[str, None] = Query(default=None),
):
    now = datetime.now(pytz.timezone("Asia/Jakarta"))

    if date == "yesterday":
        date_filter = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date is not None and date not in ("today",):
        # specific date passed as YYYY-MM-DD
        date_filter = date
    else:
        # default: today
        date_filter = now.strftime("%Y-%m-%d")

    querySearch = f'%{query}%'
    date_start = f'{date_filter} 00:00:00'
    date_end = f'{date_filter} 23:59:59'

    # Base condition: name search + date range filter
    searchCondition = (db['items']['name'] |LIKE| querySearch) & \
                      (db['prices']['created_at'] >= date_start) & \
                      (db['prices']['created_at'] <= date_end)

    # Source filter: if user specifies source, use it; otherwise exclude alfacart (deprecated source)
    if source is not None and len(source) > 0:
        searchCondition = searchCondition & (db['items']['source'] == source)
    else:
        # No source specified: exclude deprecated alfacart source
        searchCondition = searchCondition & (db['items']['source'] != 'alfacart')
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
