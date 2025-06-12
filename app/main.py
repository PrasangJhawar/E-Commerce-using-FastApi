from fastapi import FastAPI
from app.auth.router import router as auth_router
from app.products.admin_router import router as admin_products_router
from app.core.database import Base, engine
from app.products.public_products import router as public_product_router
from app.cart.router import router as cart_router
from app.orders.checkout import router as checkout_router
from app.orders.router import router as orders_router


Base.metadata.create_all(bind=engine)


app = FastAPI()

app.include_router(auth_router)
app.include_router(admin_products_router)
app.include_router(public_product_router)
app.include_router(cart_router)
app.include_router(checkout_router)
app.include_router(orders_router)

#boiler-plate
@app.get("/")
def read_root():
    return {"message": "Hello World"}
