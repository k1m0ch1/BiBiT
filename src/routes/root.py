from config import DATA_DIR
from fastapi import APIRouter
from datetime import date
from typing import Optional

import json

root = APIRouter()

@root.get("/")
async def index(start: Optional[int] = 0, end: Optional[int] = 50, date: Optional[str] = date.today().strftime("%Y-%m-%d")):
    TARGETDB = json.loads(open(f"{DATA_DIR}/yogyaonline/catalog/{date}.json", 'r').read())['data']
    return {
        "message": f"Success fetch data",
        "data": TARGETDB[start:end]
    }
