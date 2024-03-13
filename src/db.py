from sqllex import SQLite3x, TEXT, INTEGER, PRIMARY_KEY, UNIQUE, FOREIGN_KEY

TEMPLATE_DB = {
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
        },
        "item_item": {
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "item_id": TEXT,
            "with_item_id": TEXT,
            "status": TEXT,
            "created_at": TEXT,
            "updated_at": TEXT,
            FOREIGN_KEY: {
                "item_id": ["items", "id"],
                "with_item_id": ["items", "id"]
            }
        },
        "belanja_link":{
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "status": TEXT, # CREATED, DELETED, FINISH, BELANJA
            "created_at": TEXT,
            "updated_at": TEXT,
            "deleted_at": TEXT,
            "secret_key": [TEXT, UNIQUE]
        },
        "belanja": {
            "id": [TEXT, PRIMARY_KEY, UNIQUE],
            "belanja_link_id": TEXT,
            "items_id": TEXT,
            "custom_price": INTEGER,
            "created_at": TEXT,
            "updated_at": TEXT,
            "deleted_at": TEXT,
            FOREIGN_KEY: {
                "belanja_link_id": ["belanja_link", "id"],
                "items_id": ["items", "id"]
            }
        }
    }

DBAPI = SQLite3x(
    path='indiemart.db',
    check_same_thread=False,
    template=TEMPLATE_DB)

DBSTATE = SQLite3x(
    path='crawl.db',
    check_same_thread=False,
    template=TEMPLATE_DB)

db = DBSTATE

loi = {
    "idx_items_sku": "CREATE INDEX idx_items_sku ON items(sku)",
    "idx_items_name": "CREATE INDEX idx_items_name ON items(name)", 
    "idx_items_source": "CREATE INDEX idx_items_source ON items(source)",
    "idx_items_created_at": "CREATE INDEX idx_items_created_at ON items(created_at)", 
    "idx_prices_price": "CREATE INDEX idx_prices_price ON prices(price)",
    "idx_prices_items_id": "CREATE INDEX idx_prices_items_id ON prices(items_id)",
    "idx_prices_created_at": "CREATE INDEX idx_prices_created_at ON prices(created_at)",
    "idx_discounts_discount_price": "CREATE INDEX idx_discounts_discount_price ON discounts(discount_price)",
    "idx_discounts_items_id": "CREATE INDEX idx_discounts_items_id ON discounts(items_id)",
    "idx_discounts_original_price": "CREATE INDEX idx_discounts_original_price ON discounts(original_price)",
    "idx_discounts_created_at": "CREATE INDEX idx_discounts_created_at ON discounts(created_at)",
    "idx_item_item_item_id": "CREATE INDEX idx_item_item_item_id ON item_item(item_id)",
    "idx_item_item_with_item_id": "CREATE INDEX idx_item_item_with_item_id ON item_item(with_item_id)",
    "idx_belanja_id": "CREATE INDEX idx_belanja_id ON belanja(id)",
    "idx_belanja_belanja_link_id": "CREATE INDEX idx_belanja_belanja_link_id ON belanja(belanja_link_id)",
    "idx_belanja_items_id": "CREATE INDEX idx_belanja_items_id ON belanja(items_id)"
}

listIndexes = db.execute(script="SELECT name FROM sqlite_master WHERE type='index'")
li = []

for ll in listIndexes:
    li.append(ll[0])

listOfIndexes = loi.keys()

for name in listOfIndexes:
    if name not in li:
        db.execute(script=loi[name])
    else:
        continue