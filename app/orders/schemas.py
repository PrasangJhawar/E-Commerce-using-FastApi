from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class OrderItemBase(BaseModel):
    product_id: UUID
    quantity: int
    price: float


class OrderItemResponse(OrderItemBase):
    id: UUID

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    total_amount: float
    status: str = "processing it.."


class OrderCreate(BaseModel):
    total_amount: float
    items: List[OrderItemBase]


class OrderResponse(OrderBase):
    id: UUID
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderSummaryResponse(BaseModel):
    id: UUID
    created_at: datetime
    total_amount: float
    status: str

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderSummaryResponse):
    items: List[OrderItemResponse]
