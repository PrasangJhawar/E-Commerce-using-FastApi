from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.auth.dependencies import get_current_user_id
from app.orders import schemas
from app.orders.models import Order

import logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])

#viewing order history
@router.get("/", response_model=list[schemas.OrderSummaryResponse])
def get_order_history(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    return orders

# get order detials
@router.get("/{order_id}", response_model=schemas.OrderDetailResponse)
def get_order_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
