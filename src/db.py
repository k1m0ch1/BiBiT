
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

DBAPI = SQLite3x(path='indiemart.db',check_same_thread=False)

DBSTATE = SQLite3x(
    path='crawl.db',
    check_same_thread=False,
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