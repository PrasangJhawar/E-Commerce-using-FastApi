from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.products import models, schemas
from app.auth.dependencies import admin_required
from app.core.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/admin/products", tags=["admin-products"])

#add products
@router.post("/", response_model=schemas.ProductResponse, dependencies=[Depends(admin_required)])
def create_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        logger.debug("Creating product: %s", product_in.name)
        #unpacks a dict
        product = models.Product(**product_in.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info("Product created: %s", product.id)
        return product
    except Exception as e:
        logger.exception("Error while creating product: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#get all products
@router.get("/", response_model=List[schemas.ProductResponse], dependencies=[Depends(admin_required)])
def list_products(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    try:
        logger.debug("Listing products: skip=%d, limit=%d", skip, limit)
        products = db.query(models.Product).offset(skip).limit(limit).all()
        logger.info("Listed %d products", len(products))
        return products
    except Exception as e:
        logger.exception("Error while listing products: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#get a product by id
@router.get("/{product_id}", response_model=schemas.ProductResponse, dependencies=[Depends(admin_required)])
def get_product(product_id: str, db: Session = Depends(get_db)):
    try:
        logger.debug("Fetching product: %s", product_id)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.warning("Product not found: %s", product_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product
    except Exception as e:
        logger.exception("Error while fetching product %s: %s", product_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#update
@router.put("/{product_id}", response_model=schemas.ProductResponse, dependencies=[Depends(admin_required)])
def update_product(product_id: str, product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        logger.debug("Updating product: %s", product_id)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.warning("Product not found for update: %s", product_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        for field, value in product_in.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)
        logger.info("Product updated: %s", product_id)
        return product
    except Exception as e:
        logger.exception("Error while updating product %s: %s", product_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

#delete
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_required)])
def delete_product(product_id: str, db: Session = Depends(get_db)):
    try:
        logger.debug("Deleting product: %s", product_id)
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            logger.warning("Product not found for deletion: %s", product_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        db.delete(product)
        db.commit()
        logger.info("Product deleted: %s", product_id)
    except Exception as e:
        logger.exception("Error while deleting product %s: %s", product_id, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")