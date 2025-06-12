from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.products import models, schemas

router = APIRouter(prefix="/products", tags=["public-products"])

#product listing
@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = Query(None, regex="^(price|name)_(asc|desc)$"),
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    query = db.query(models.Product)

    # filtering logic
    if category:
        query = query.filter(models.Product.category == category)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    # sorting
    if sort_by:
        field, direction = sort_by.split("_")
        column = getattr(models.Product, field)
        if direction == "desc":
            column = column.desc()
        query = query.order_by(column)

    """# Pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()
    return products"""


# searching
@router.get("/search", response_model=List[schemas.ProductResponse])
def search_products(
    keyword: str,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(
        (models.Product.name.ilike(f"%{keyword}%")) |
        (models.Product.description.ilike(f"%{keyword}%"))
    )
    return query.all()


#view details
@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
