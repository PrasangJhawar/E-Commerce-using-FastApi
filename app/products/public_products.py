from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.products import models, schemas
from app.core.logger import setup_logger

logger = setup_logger(__name__)
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
    try:
        logger.debug("Listing products: category=%s, min_price=%s, max_price=%s, sort_by=%s, page=%d, page_size=%d",
                     category, min_price, max_price, sort_by, page, page_size)

        query = db.query(models.Product)

        #filtering logic
        if category:
            query = query.filter(models.Product.category == category)
        if min_price is not None:
            query = query.filter(models.Product.price >= min_price)
        if max_price is not None:
            query = query.filter(models.Product.price <= max_price)

        if sort_by:
            field, direction = sort_by.split("_")
            column = getattr(models.Product, field)
            if direction == "desc":
                column = column.desc()
            query = query.order_by(column)

        #Using pagination to split the data to multiple pages
        offset = (page - 1) * page_size
        products = query.offset(offset).limit(page_size).all()

        logger.info("Returned %d products", len(products))
        return products

    except Exception as e:
        logger.exception("Error while listing products: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


#seraching
@router.get("/search", response_model=List[schemas.ProductResponse])
def search_products(
    keyword: str,
    db: Session = Depends(get_db)
):
    try:
        logger.debug("Searching products with keyword: %s", keyword)
        query = db.query(models.Product).filter(
            (models.Product.name.ilike(f"%{keyword}%")) |
            (models.Product.description.ilike(f"%{keyword}%"))
        )
        results = query.all()
        logger.info("Search returned %d products for keyword: %s", len(results), keyword)
        return results
    except Exception as e:
        logger.exception("Error while searching products: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


#view details
@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    try:
        logger.debug("Fetching products by ID: %s", product_id)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.warning("Product not found: %s", product_id)
            raise HTTPException(status_code=404, detail="Product not found")
        logger.info("Product fetched: %s", product_id)
        return product
    except Exception as e:
        logger.exception("Error while fetching product %s: %s", product_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")