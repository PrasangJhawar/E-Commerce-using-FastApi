from pydantic import BaseModel
from uuid import UUID
from typing import List
from app.products.schemas import ProductResponse

class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int

#future flexibility, so we have separation of concerns
class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    product: ProductResponse 

    class Config:
        orm_mode = True