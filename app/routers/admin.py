import logging
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, String, func
from app.database import get_db
from app.models import Order, Product, Client
from app.auth import check_auth

logger = logging.getLogger("ADMIN")
router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(check_auth)])

def serialize_order(o):
    logger.info(f"ORDER_SERIALIZE_START: ID_{o.id}")
    try:
        items = []
        if isinstance(o.items_json, str):
            try:
                items = json.loads(o.items_json)
            except Exception as e:
                logger.error(f"ORDER_JSON_ERR: ID_{o.id} ERROR_{e}")
        else:
            items = o.items_json or []

        res = {
            "id": o.id,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "status": str(o.status).lower() if o.status else "new",
            "fio": o.fio,
            "phone": o.client_phone,
            "city_name": o.np_city_name or "—",
            "warehouse": o.np_warehouse_desc or "",
            "delivery_type": str(o.delivery_type).lower() if o.delivery_type else "nova_poshta",
            "payment_type": str(o.payment_method).lower() if o.payment_method else "cod",
            "items": items,
            "total_price": float(o.total_price or 0),
            "admin_comment": o.admin_comment or "",
            "client_comment": o.comment or "",
            "ttn": o.ttn or ""
        }
        return res
    except Exception as e:
        logger.error(f"ORDER_SERIALIZE_FATAL: ID_{o.id} ERROR_{e}")
        return {"id": getattr(o, 'id', 'unknown'), "error": "serialization_fail"}

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    logger.info("ADMIN_STATS_FETCH_START")
    try:
        total_orders = db.query(Order).count()
        total_revenue = db.query(func.sum(Order.total_price)).scalar() or 0
        total_products = db.query(Product).count()
        total_clients = db.query(Client).count()
        low_stock = db.query(Product).filter(Product.stock <= 5).count()
        
        res = {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "total_products": total_products,
            "total_clients": total_clients,
            "low_stock_count": low_stock
        }
        logger.info(f"ADMIN_STATS_SUCCESS: {res}")
        return res
    except Exception as e:
        logger.error(f"ADMIN_STATS_FATAL: {e}")
        raise HTTPException(status_code=500)

@router.get("/orders")
def get_admin_orders(limit: int = 100, offset: int = 0, search: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"ADMIN_GET_ORDERS_REQ: LIMIT_{limit} OFFSET_{offset} SEARCH_{search}")
    try:
        query = db.query(Order)
        if search:
            query = query.filter(or_(
                Order.fio.ilike(f"%{search}%"),
                Order.client_phone.ilike(f"%{search}%"),
                Order.ttn.ilike(f"%{search}%")
            ))
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        res = [serialize_order(o) for o in orders]
        logger.info(f"ADMIN_GET_ORDERS_SUCCESS: DELIVERED_{len(res)}")
        return res
    except Exception as e:
        logger.error(f"ADMIN_GET_ORDERS_FATAL: {e}")
        raise HTTPException(status_code=500)

@router.get("/products")
def get_admin_products(search: str = "", limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    logger.info(f"ADMIN_GET_PRODUCTS_REQ: SEARCH_{search} LIMIT_{limit}")
    try:
        query = db.query(Product)
        if search:
            query = query.filter(or_(
                Product.title_ru.ilike(f"%{search}%"),
                Product.title_ua.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            ))
        products = query.offset(offset).limit(limit).all()
        res = []
        for p in products:
            img = p.images[0] if p.images and len(p.images) > 0 else None
            res.append({
                "id": p.id,
                "sku": p.sku or str(p.id),
                "name": p.title_ua or p.title_ru or "No name",
                "price": float(p.price or 0),
                "stock": p.stock or 0,
                "image": img,
                "is_active": True
            })
        logger.info(f"ADMIN_GET_PRODUCTS_SUCCESS: DELIVERED_{len(res)}")
        return res
    except Exception as e:
        logger.error(f"ADMIN_GET_PRODUCTS_FATAL: {e}")
        return []

@router.patch("/update-product-field")
def update_product_field(data: dict, db: Session = Depends(get_db)):
    logger.info(f"ADMIN_PROD_UPDATE_START: DATA_{data}")
    try:
        pid = data.get("id")
        product = db.query(Product).filter(Product.id == pid).first()
        if not product: 
            raise HTTPException(status_code=404)
        for key, value in data.items():
            if key != "id" and hasattr(product, key):
                setattr(product, key, value)
        db.commit()
        logger.info(f"ADMIN_PROD_UPDATE_SUCCESS: ID_{pid}")
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.error(f"ADMIN_PROD_UPDATE_ROLLBACK: {e}")
        raise HTTPException(status_code=500)

@router.delete("/product/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    logger.info(f"ADMIN_PROD_DEL_REQ: ID_{product_id}")
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            logger.info(f"ADMIN_PROD_DEL_SUCCESS")
            return {"success": True}
        return {"success": False}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500)

@router.patch("/order/{order_id}/update-field")
def update_order_field(order_id: int, data: dict, db: Session = Depends(get_db)):
    logger.info(f"ADMIN_ORDER_UPDATE: ID_{order_id} DATA_{data}")
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order: raise HTTPException(status_code=404)
        mapping = {"phone": "client_phone", "status": "status", "ttn": "ttn"}
        for key, value in data.items():
            field = mapping.get(key, key)
            if hasattr(order, field):
                setattr(order, field, value)
        db.commit()
        logger.info(f"ADMIN_ORDER_UPDATE_SUCCESS: ID_{order_id}")
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.error(f"ADMIN_ORDER_UPDATE_ERR: {e}")
        raise HTTPException(status_code=500)