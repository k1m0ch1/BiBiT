from fastapi import APIRouter
from db import DBAPI
import sqllex as sx
from sqllex.constants import  ON, LIKE, NULL
import shortuuid
from pydantic import BaseModel
from typing import Union
from datetime import date, timedelta
from datetime import datetime
import pytz

db = DBAPI

router = APIRouter()

class ItemBelanja(BaseModel):
    item_id: str
    custom_price: Union[int, None] = 0
    secret_key: str

class deleteLink(BaseModel):
    secret_key: str

# need to put some ratelimit in here
@router.post("/belanja/new", status_code=201)
def newBelanjaLink():
    BELANJA_ID = shortuuid.uuid()
    SECRET_KEY = shortuuid.uuid()[:9]
    now = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    db["belanja_link"].insert(
        id=BELANJA_ID,
        status="CREATED",
        created_at=now,
        updated_at=now,
        deleted_at="KOSONG",
        secret_key=SECRET_KEY
    )
    return {"id": BELANJA_ID, "secret_key": SECRET_KEY}

# check item if exist
# check item if already inserted
@router.post("/belanja/{belanja_id}", status_code=200)
def addItemBelanja(belanja_id, item: ItemBelanja):
    now = pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    checkSecretBelanja = db.select(TABLE='belanja_link', SELECT='id', WHERE=(db['belanja_link']['secret_key'] == item.secret_key))
    if len(checkSecretBelanja) > 0:
        if belanja_id == checkSecretBelanja[0][0]:
            db["belanja"].insert(
                id=shortuuid.uuid(),
                belanja_link_id=belanja_id,
                items_id=item.item_id,
                custom_price=item.custom_price,
                created_at=now,
                updated_at=now,
                deleted_at="KOSONG"
            )
            return {"message": "success add new item to belanja list"}
    return {"message": "access denied"}

# check item if exist in items
# check item if exist at belanja
@router.delete("/belanja/{belanja_id}", status_code=200)
def deleteItemPrice(belanja_id, item: ItemBelanja):
    now = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    checkSecretBelanja = db.select(TABLE='belanja_link', SELECT='id', WHERE=(db['belanja_link']['secret_key'] == item.secret_key))
    if len(checkSecretBelanja) > 0:
        if belanja_id == checkSecretBelanja[0][0]:
            db["belanja"].update(
                SET={
                    'deleted_at' : now
                },
                WHERE=(
                    (db["belanja"]["belanja_link_id"] == belanja_id) & (db["belanja"]["items_id"] == item.item_id)
                )
            )
            return {"message": "success delete the item belanja"}
    return {"message": "access denied"}

# check item if exist in items
# check item if exist at belanja
@router.delete("/belanja/{belanja_id}/delete", status_code=200)
def deleteLink(belanja_id, key: deleteLink):
    now = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    checkSecretBelanja = db.select(TABLE='belanja_link', SELECT='id', WHERE=(db['belanja_link']['secret_key'] == key.secret_key))
    if len(checkSecretBelanja) > 0:
        if belanja_id == checkSecretBelanja[0][0]:
            db["belanja_link"].update(
                SET={
                    'deleted_at' : now
                },
                WHERE=(
                    (db["belanja_link"]["secret_key"] == key.secret_key)
                )
            )
            db["belanja"].update(
                SET={
                    'deleted_at' : now
                },
                WHERE=(
                    (db["belanja"]["belanja_link_id"] == belanja_id)
                )
            )
            return {"message": "success delete belanja"}
    return {"message": "access denied"}

# check item if exist in items
# check item if exist at belanja
@router.put("/belanja/{belanja_id}", status_code=200)
def updateItemPrice(belanja_id, item: ItemBelanja):
    now = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    checkSecretBelanja = db.select(TABLE='belanja_link', SELECT='id', WHERE=(db['belanja_link']['secret_key'] == item.secret_key))
    if len(checkSecretBelanja) > 0:
        if belanja_id == checkSecretBelanja[0][0]:
            db["belanja"].update(
                SET={
                    'custom_price' : item.custom_price,
                    'updated_at' : now
                },
                WHERE=(
                    (db["belanja"]["belanja_link_id"] == belanja_id) & (db["belanja"]["items_id"] == item.item_id)
                )
            )
            return {"message": "success update the custom price"}
    return {"message": "access denied"}

# cek kalo belanja link nya exist ga, kalo exist dan deleted jangan diliatin
@router.get("/belanja/{belanja_id}")
def getItemBelanja(belanja_id):
    now = datetime.now(pytz.timezone("Asia/Jakarta"))
    today = now.strftime("%Y-%m-%d")
    searchCondition =  (db['belanja']['deleted_at'] == "KOSONG") &(db['prices']['created_at'] |LIKE| f'{today}%')
    getItems = db.select(
        TABLE='belanja',
        SELECT=[
            db['items']['id'],
            db['items']['name'],
            db['items']['source'],
            db['prices']['price'],
            db['belanja']['custom_price']
        ],
        JOIN=(
            (
                sx.INNER_JOIN, db['items'],
                ON, db['belanja']['items_id'] == db['items']['id']
            ),
            (
                sx.INNER_JOIN, db['prices'],
                ON, db['items']['id'] == db['prices']['items_id']
            )
        ),
        WHERE=(searchCondition),
        ORDER_BY=(db['belanja']['created_at'], 'ASC'),
        GROUP_BY=[
            db['items']['id']
        ]
    )
    return getItems

# @router.delete("/belanja/{belanja_id}/{item_id}", status_code=200)
# def delItemBelanja(belanja_id, item_id):
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     db["belanja"].update(

#     )