from config import DATA_DIR
from fastapi import APIRouter
from datetime import date
from typing import Optional
import os 

import json

root = APIRouter()

@root.get("/")
async def index(start: Optional[int] = 0, end: Optional[int] = 50, date: Optional[str] = date.today().strftime("%Y-%m-%d")):
    FILENAME = f"{DATA_DIR}/yogyaonline/catalog/{date}.json"
    if not os.path.exists(FILENAME):
        return {"message": f"the data on this date is not exist"}
    TARGETDB = json.loads(open(FILENAME, 'r').read())['data']
    return {
        "message": f"Success fetch data",
        "data": TARGETDB[start:end]
    }
