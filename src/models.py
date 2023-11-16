from typing import List, Union
from pydantic import BaseModel
from db import Price

class ItemBase(BaseModel):
    sku: str
    name: str
    category: str
    image: str
    link: str
    source: str
    category: str

class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    prices: List[Price] = []

    class Config:
        orm_mode = True

class PriceBase(BaseModel):
    price: int
    description: Union[str, None] = None

class PriceCreate(PriceBase):
    pass

class Price(PriceBase):
    id: int

    class Config:
        orm_mode = True

class DiscountBase(BaseModel):
    price: int
    description: Union[str, None] = None

class DiscountCreate(DiscountBase):
    pass

class Discount(DiscountBase):
    id: int

    class Config:
        orm_mode = True