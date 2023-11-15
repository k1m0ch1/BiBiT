
from sqllex import SQLite3x, TEXT, NOT_NULL, INTEGER, PRIMARY_KEY, UNIQUE, FOREIGN_KEY, ALL

DBSTATE = SQLite3x(
    path='crawl.db',
    template={
        "items":{
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "sku": TEXT,
            "name": TEXT,
            "category" : TEXT,
            "image": TEXT,
            "link": TEXT,
            "source": TEXT,
            "created_at" : TEXT
        },
        "prices":{
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "items_id": TEXT,
            "price": INTEGER,
            "description" : TEXT,
            "created_at" : TEXT,
            FOREIGN_KEY: {
                "items_id": ["items", "id"]
            }
        },
        "discounts":{
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "items_id": TEXT,
            "discount_price": INTEGER,
            "original_price": INTEGER,
            "percentage": TEXT,
            "description" : TEXT,
            "created_at" : TEXT,
            FOREIGN_KEY: {
                "items_id": ["items", "id"]
            }
        }
    }
)