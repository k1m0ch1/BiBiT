from fastapi import APIRouter, Query
from db import DBAPI
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
        date_filter = date
    else:
        date_filter = now.strftime("%Y-%m-%d")

    date_start = f'{date_filter} 00:00:00'
    date_end = f'{date_filter} 23:59:59'

    if source is not None and len(source) > 0:
        sql = """
            SELECT items.id, items.name, items.link, items.source, items.image, prices.price
            FROM items
            INNER JOIN prices ON items.id = prices.items_id
            WHERE items.name LIKE ?
              AND prices.created_at >= ?
              AND prices.created_at <= ?
              AND items.source = ?
            GROUP BY items.name
            ORDER BY prices.price ASC
        """
        params = (f'%{query}%', date_start, date_end, source)
    else:
        sql = """
            SELECT items.id, items.name, items.link, items.source, items.image, prices.price
            FROM items
            INNER JOIN prices ON items.id = prices.items_id
            WHERE items.name LIKE ?
              AND prices.created_at >= ?
              AND prices.created_at <= ?
              AND items.source != 'alfacart'
            GROUP BY items.name
            ORDER BY prices.price ASC
        """
        params = (f'%{query}%', date_start, date_end)

    items = db.execute(script=sql, values=params)

    result = []
    for item in items:
        if item[5] > 99:
            result.append({
                "id": item[0],
                "name": item[1],
                "link": item[2],
                "source": item[3],
                "image": item[4],
                "prices": item[5]
            })
    return result
