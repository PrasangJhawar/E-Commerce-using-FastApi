from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.auth.dependencies import get_current_user_id
from app.orders import schemas
from app.orders.models import Order
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=list[schemas.OrderSummaryResponse])
def get_order_history(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        logger.debug("Fetching order history for user: %s", user_id)
        orders = (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        logger.info("Fetched %d orders for user: %s", len(orders), user_id)
        return orders
    except Exception as e:
        logger.exception("Error while fetching order history for user %s: %s", user_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}", response_model=schemas.OrderDetailResponse)
def get_order_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    try:
        logger.debug("Fetching order detail for order %s by user %s", order_id, user_id)
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order:
            logger.warning("Order %s not found for user %s", order_id, user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        logger.info("Order %s retrieved successfully for user %s", order_id, user_id)
        return order
    except Exception as e:
        logger.exception("Error while fetching order detail for order %s: %s", order_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")