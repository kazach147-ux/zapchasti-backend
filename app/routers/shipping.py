import os
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order
from app.config import BOT_TOKEN

router = APIRouter(prefix="/shipping", tags=["Shipping"])
logger = logging.getLogger("SHIPPING")

NP_URL = "https://api.novaposhta.ua/v2.0/json/"
NP_API_KEY = os.getenv("NP_API_KEY")

@router.get("/cities")
async def get_cities(search: str = Query(..., min_length=2)):
    logger.info(f"NP_CITY_SEARCH: {search}")
    if not NP_API_KEY:
        logger.error("NP_KEY_MISSING")
        return []

    payload = {
        "apiKey": NP_API_KEY,
        "modelName": "Address",
        "calledMethod": "getCities",
        "methodProperties": {"FindByString": search, "Limit": "50"}
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(NP_URL, json=payload)
            r = resp.json()
            if r.get("success"):
                data = [{"name": c["Description"], "ref": c["Ref"]} for c in r.get("data", [])]
                logger.info(f"NP_CITY_OK: {len(data)}")
                return data
            logger.warning(f"NP_CITY_API_ERR: {r.get('errors')}")
            return []
        except Exception as e:
            logger.error(f"NP_CITY_FATAL: {e}")
            return []

@router.get("/warehouses")
async def get_warehouses(city_ref: str = Query(...)):
    logger.info(f"NP_WH_REQ: {city_ref}")
    if not NP_API_KEY:
        logger.error("NP_KEY_MISSING")
        return []

    payload = {
        "apiKey": NP_API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {"CityRef": city_ref}
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(NP_URL, json=payload)
            r = resp.json()
            if r.get("success"):
                data = [{"name": w["Description"], "ref": w["Ref"]} for w in r.get("data", [])]
                logger.info(f"NP_WH_OK: {len(data)}")
                return data
            logger.warning(f"NP_WH_API_ERR: {r.get('errors')}")
            return []
        except Exception as e:
            logger.error(f"NP_WH_FATAL: {e}")
            return []

@router.post("/create_ttn")
async def create_ttn(order_id: int, db: Session = Depends(get_db)):
    logger.info(f"TTN_START: {order_id}")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(f"TTN_ERR: {order_id}_NOT_FOUND")
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.status
    order.status = "SHIPPED"
    try:
        if hasattr(order, 'add_status_log'):
            order.add_status_log(old_status, "SHIPPED", "system_np")
        
        db.commit()
        logger.info(f"TTN_OK: ORDER_{order_id}")
        return {"status": "success", "message": "Status updated"}
    except Exception as e:
        db.rollback()
        logger.error(f"TTN_DB_ERR: {e}")
        raise HTTPException(status_code=500, detail="Database error")