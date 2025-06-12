from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.auth.dependencies import get_current_user_id
from app.cart.models import CartItem
from app.orders.models import Order, OrderItem
from app.products.models import Product

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def checkout(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # fetching cart items here
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    #calculating the stock
    total_amount = 0
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product '{product.name}'"
            )

        total_amount += item.quantity * product.price

    #order creation
    order = Order(user_id=user_id, total_amount=total_amount)
    db.add(order)
    db.flush()  # ensures order.id is available

    #dealing with order items table, creating stock
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        #stock deduction
        product.stock -= item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price,
        )
        db.add(order_item)

    #clearing the cart
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()


    db.commit()

    return {
        "message": "Order placed successfully",
        "order_id": order.id,
        "total": total_amount
    }
