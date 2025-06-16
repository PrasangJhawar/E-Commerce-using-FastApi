from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.cart.models import CartItem
from app.cart.schemas import CartItemCreate, CartItemUpdate, CartItemResponse
from app.auth.models import User                     
from app.products.models import Product               
from app.auth.dependencies import get_current_user
from app.auth.dependencies import user_required   
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("/", response_model=CartItemResponse, dependencies=[Depends(user_required)])
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug("Adding to cart: user=%s, product=%s, qty=%d", current_user.id, item.product_id, item.quantity)

        product = db.query(Product).filter_by(id=item.product_id).first()
        if not product:
            logger.warning("Product not found: %s", item.product_id)
            raise HTTPException(status_code=404, detail="Product not found")

        if product.stock < item.quantity:
            logger.warning("Insufficient stock for product %s", item.product_id)
            raise HTTPException(status_code=400, detail="Not enough stock available")

        cart_item = db.query(CartItem).filter_by(
            user_id=current_user.id, product_id=item.product_id
        ).first()

        if cart_item:
            total_quantity = cart_item.quantity + item.quantity
            if product.stock < (total_quantity - cart_item.quantity):
                logger.warning("Stock too low to update cart item: %s", item.product_id)
                raise HTTPException(status_code=400, detail="Not enough stock to update cart item")
            cart_item.quantity = total_quantity
            logger.info("Updated quantity for cart item: %s", item.product_id)
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(cart_item)
            logger.info("Added new item to cart: %s", item.product_id)

        db.commit()
        db.refresh(cart_item)
        return cart_item

    except Exception as e:
        logger.exception("Error while adding to cart: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
@router.get("/", response_model=list[CartItemResponse], dependencies=[Depends(user_required)])
def view_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug("Fetching cart for user: %s", current_user.id)
        cart_items = (
            db.query(CartItem)
            .filter_by(user_id=current_user.id)
            .join(Product)
            .all()
        )
        logger.info("Fetched %d items from cart for user: %s", len(cart_items), current_user.id)
        return cart_items
    except Exception as e:
        logger.exception("Error while viewing cart: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#router-> logging and exceptions
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug("Removing product %s from cart for user %s", product_id, current_user.id)
        cart_item = db.query(CartItem).filter_by(
            user_id=current_user.id, product_id=product_id
        ).first()

        if not cart_item:
            logger.warning("Cart item not found: product=%s, user=%s", product_id, current_user.id)
            raise HTTPException(status_code=404, detail="Cart item not found")

        db.delete(cart_item)
        db.commit()
        logger.info("Removed cart item: product=%s, user=%s", product_id, current_user.id)

    except Exception as e:
        logger.exception("Error while removing from cart: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")



@router.put("/{product_id}", response_model=CartItemResponse)
def update_quantity(
    product_id: UUID,
    item: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.debug("Updating quantity for product %s in cart for user %s", product_id, current_user.id)
        cart_item = db.query(CartItem).filter_by(
            user_id=current_user.id, product_id=product_id
        ).first()

        if not cart_item:
            logger.warning("Cart item not found: product=%s", product_id)
            raise HTTPException(status_code=404, detail="Cart item not found")

        product = db.query(Product).filter_by(id=product_id).first()
        if not product:
            logger.warning("Product not found while updating cart: %s", product_id)
            raise HTTPException(status_code=404, detail="Product not found")

        quantity_diff = item.quantity - cart_item.quantity

        if quantity_diff > 0 and product.stock < quantity_diff:
            logger.warning("Insufficient stock to increase quantity for product %s", product_id)
            raise HTTPException(status_code=400, detail="Not enough stock available")

        cart_item.quantity = item.quantity
        db.commit()
        db.refresh(cart_item)
        logger.info("Updated quantity for product %s in user %s's cart", product_id, current_user.id)
        return cart_item

    except Exception as e:
        logger.exception("Error while updating cart item quantity: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")