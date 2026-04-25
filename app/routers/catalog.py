import logging
from typing import Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Product, Category

logger = logging.getLogger("CATALOG")
router = APIRouter(tags=["Catalog"])

def get_proxy_url(request: Request, images_list: list) -> Optional[str]:
    if not images_list or not isinstance(images_list, list) or len(images_list) == 0:
        return None
    image_val = images_list[0]
    if not image_val:
        return None
    if str(image_val).startswith("http"):
        return image_val
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/proxy-image?url={image_val}"

@router.get("/categories")
def get_categories(lang: str = "ru", db: Session = Depends(get_db)):
    logger.info(f"REQ_CATEGORIES: lang={lang}")
    try:
        categories = db.query(Category).all()
        result = []
        for c in categories:
            name_val = c.name_ua if lang == "ua" and c.name_ua else (c.name_ru or c.name)
            result.append({
                "id": c.id,
                "parent_id": c.parent_id,
                "image": c.image,
                "name": name_val
            })
        logger.info(f"RESP_CATEGORIES: count={len(result)}")
        return result
    except Exception as e:
        logger.error(f"ERR_CATEGORIES: {e}")
        return []

@router.get("/products")
def get_products(
    request: Request,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    lang: str = "ru",
    offset: int = 0,
    limit: int = 40,
    db: Session = Depends(get_db)
):
    logger.info(f"REQ_PRODUCTS: cat={category_id} search={search} offset={offset} limit={limit}")
    try:
        query = db.query(Product)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if search:
            s_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.title_ru.ilike(s_term),
                    Product.title_ua.ilike(s_term),
                    Product.sku.ilike(s_term)
                )
            )
        
        total = query.count()
        products = query.offset(offset).limit(limit).all()
        
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "sku": p.sku,
                "price": float(p.price) if p.price else 0.0,
                "stock": p.stock,
                "category_id": p.category_id,
                "image": get_proxy_url(request, p.images),
                "name": p.title_ua if lang == "ua" and p.title_ua else (p.title_ru or "Без названия")
            })
        logger.info(f"RESP_PRODUCTS: found={len(result)} total_in_db={total}")
        return result
    except Exception as e:
        logger.error(f"ERR_PRODUCTS: {e}")
        return []

@router.get("/products/{product_id}")
def get_product_detail(
    request: Request, 
    product_id: str, 
    lang: str = "ru", 
    db: Session = Depends(get_db)
):
    logger.info(f"REQ_PROD_DETAIL: id={product_id} lang={lang}")
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"NOT_FOUND_PROD: {product_id}")
            raise HTTPException(status_code=404, detail="Product not found")
        
        res = {
            "id": product.id,
            "sku": product.sku,
            "price": float(product.price) if product.price else 0.0,
            "stock": product.stock,
            "images": [get_proxy_url(request, [img]) for img in product.images] if product.images else [],
            "category_id": product.category_id,
            "name": product.title_ua if lang == "ua" and product.title_ua else (product.title_ru or "Без названия"),
            "description": product.description_ua if lang == "ua" and product.description_ua else (product.description_ru or ""),
            "specs": {}
        }
        logger.info(f"RESP_PROD_DETAIL: {product_id}")
        return res
    except Exception as e:
        logger.error(f"ERR_PROD_DETAIL: {e}")
        raise HTTPException(status_code=500, detail="Server error")