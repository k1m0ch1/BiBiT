from config import DATA_DIR
from fastapi import APIRouter
from datetime import date
from typing import Optional
import os 

import json

router = APIRouter()

@router.get("/yogyaonline/catalog")
async def catalog(start: Optional[int] = 0, end: Optional[int] = 50, date: Optional[str] = date.today().strftime("%Y-%m-%d")):
    FILENAME = f"{DATA_DIR}/yogyaonline/catalog/{date}.json"
    if not os.path.exists(FILENAME):
        return {"message": f"the data on this date is not exist"}
    TARGETDB = json.loads(open(FILENAME, 'r').read())['data']
    return {
        "message": f"Success fetch data",
        "data": TARGETDB[start:end]
    }

@router.get("/yogyaonline/catalog/available")
async def availabilityCatalog():
    DIRPATH = f"{DATA_DIR}/yogyaonline/catalog"

    files = next(os.walk(DIRPATH), (None, None, []))[2]
    return {
        "message": f"Success fetch data",
        "data": files
    }
