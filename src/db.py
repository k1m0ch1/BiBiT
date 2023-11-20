
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqllex import SQLite3x, TEXT, NOT_NULL, INTEGER, PRIMARY_KEY, UNIQUE, FOREIGN_KEY, ALL

# engine = create_engine(
#     'sqlite:////mnt/c/Users/k1m0c/Documents/opensource/k1m0ch1/BiBiT/crawl.db', connect_args={"check_same_thread": False}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# class Item(Base):
#     __tablename__ = "items"

#     id = Column(String, primary_key=True, index=True)
#     sku = Column(String, unique=True, index=True)
#     name = Column(String, unique=True, index=True)
#     category = Column(String)
#     image = Column(String)
#     link = Column(String)
#     source = Column(String)
#     category = Column(String)
#     created_at = Column(DateTime, default=datetime.utcnow)

# class Price(Base):
#     __tablename__ = "prices"

#     id = Column(String, primary_key=True, index=True)
#     items_id = Column(String, index=True)
#     price = Column(Integer)
#     description = Column(String)
#     created_at = Column(DateTime, default=datetime.utcnow) 

#     items = relationship("Item")

# class Discount(Base):
#     __tablename__ = "discounts"

#     id = Column(String, primary_key=True, index=True)
#     items_id = Column(String, index=True)
#     discount_price = Column(Integer)
#     original_price = Column(Integer)
#     percentage = Column(String)
#     description = Column(String)
#     created_at = Column(DateTime, default=datetime.utcnow) 

#     items = relationship("Item")

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
        }
    }

DBAPI = SQLite3x(path='indiemart.db',check_same_thread=False, template=TEMPLATE_DB)

DBSTATE = SQLite3x(
    path='crawl.db',
    check_same_thread=False,
    template=TEMPLATE_DB
)

db = DBSTATE

loi = {
    "idx_items_sku": "CREATE UNIQUE INDEX idx_items_sku ON items(sku)",
    "idx_items_name": "CREATE UNIQUE INDEX idx_items_name ON items(name)", 
    "idx_items_source": "CREATE UNIQUE INDEX idx_items_source ON items(source)",
    "idx_items_created_at": "CREATE UNIQUE INDEX idx_items_created_at ON items(created_at)", 
    "idx_prices_price": "CREATE UNIQUE INDEX idx_prices_price ON prices(price)",
    "idx_prices_items_id": "CREATE UNIQUE INDEX idx_prices_items_id ON prices(items_id)",
    "idx_prices_created_at": "CREATE UNIQUE INDEX idx_prices_created_at ON prices(created_at)",
    "idx_discounts_discount_price": "CREATE UNIQUE INDEX idx_discounts_discount_price ON discounts(discount_price)",
    "idx_discounts_items_id": "CREATE UNIQUE INDEX idx_discounts_items_id ON discounts(items_id)",
    "idx_discounts_original_price": "CREATE UNIQUE INDEX idx_discounts_original_price ON discounts(original_price)",
    "idx_discounts_created_at": "CREATE UNIQUE INDEX idx_discounts_created_at ON discounts(created_at)",
    "idx_item_item_item_id": "CREATE UNIQUE INDEX idx_item_item_item_id ON item_item(item_id)",
    "idx_item_item_with_item_id": "CREATE UNIQUE INDEX idx_item_item_with_item_id ON item_item(with_item_id)",
}

listIndexes = db.execute(script="SELECT name FROM sqlite_master WHERE type='index'")

listOfIndexes = loi.keys()

for name in listIndexes:
    n = name[0]
    if n not in listOfIndexes:
        if n[0:3] == "idx":
            db.execute(script=loi[n])
        else:
            continue