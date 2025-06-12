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

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("/", response_model=CartItemResponse, dependencies=[Depends(user_required)])
def add_to_cart(
    item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter_by(id=item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    cart_item = db.query(CartItem).filter_by(
        user_id=current_user.id, product_id=item.product_id
    ).first()

    if cart_item:
        total_quantity = cart_item.quantity + item.quantity
        if product.stock < (total_quantity - cart_item.quantity):  # additional quantity
            raise HTTPException(status_code=400, detail="Not enough stock to update cart item")
        cart_item.quantity = total_quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(cart_item)

    # Deduct stock
    product.stock -= item.quantity

    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.get("/", response_model=list[CartItemResponse], dependencies=[Depends(user_required)])
def view_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_items = (
        db.query(CartItem)
        .filter_by(user_id=current_user.id)
        .join(Product)
        .all()
    )
    return cart_items

#router-> logging and exceptions
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = db.query(CartItem).filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    #restoring product stock
    product = db.query(Product).filter_by(id=product_id).first()
    if product:
        product.stock += cart_item.quantity

    db.delete(cart_item)
    db.commit()


@router.put("/{product_id}", response_model=CartItemResponse)
def update_quantity(
    product_id: UUID,
    item: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart_item = db.query(CartItem).filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    quantity_diff = item.quantity - cart_item.quantity

    if quantity_diff > 0 and product.stock < quantity_diff:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    product.stock -= quantity_diff
    cart_item.quantity = item.quantity

    db.commit()
    db.refresh(cart_item)
    return cart_item
