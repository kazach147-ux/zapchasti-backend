import base64
import hashlib
import json
import os
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order

logger = logging.getLogger("PAYMENTS")
router = APIRouter(prefix="/payments", tags=["Payments"])

LIQ_PUB_KEY = os.getenv("LIQ_PUB_KEY")
LIQ_PRIV_KEY = os.getenv("LIQ_PRIV_KEY")

def generate_signature(data):
    if not LIQ_PRIV_KEY:
        logger.error("LIQPAY_SIGN_ERR: PRIV_KEY_MISSING")
        return ""
    sign_str = LIQ_PRIV_KEY + data + LIQ_PRIV_KEY
    return base64.b64encode(hashlib.sha1(sign_str.encode()).digest()).decode()

@router.get("/get_form/{order_id}")
def get_payment_form(order_id: int, db: Session = Depends(get_db)):
    logger.info(f"PAY_FORM_REQ: ORDER_{order_id}")
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.warning(f"PAY_FORM_FAIL: NOT_FOUND_{order_id}")
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not LIQ_PUB_KEY or not LIQ_PRIV_KEY:
            logger.error("PAY_FORM_ERR: KEYS_MISSING")
            raise HTTPException(status_code=500, detail="Payment config missing")
        
        params = {
            "public_key": LIQ_PUB_KEY,
            "version": "3",
            "action": "pay",
            "amount": float(order.total_price or 0),
            "currency": "UAH",
            "description": f"Замовлення №{order.id}",
            "order_id": str(order.id),
            "language": "uk",
            "server_url": "https://zapchasti-backend-2.onrender.com/api/payments/callback"
        }
        
        json_data = json.dumps(params, separators=(',', ':'))
        data = base64.b64encode(json_data.encode()).decode()
        signature = generate_signature(data)
        
        logger.info(f"PAY_FORM_OK: ORDER_{order_id}")
        return {"data": data, "signature": signature}
    except Exception as e:
        logger.error(f"PAY_FORM_FATAL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/callback")
async def payment_callback(request: Request, db: Session = Depends(get_db)):
    logger.info("LIQPAY_CB_START")
    try:
        form_data = await request.form()
        data = form_data.get("data")
        signature = form_data.get("signature")
        
        if not data or not signature:
            logger.warning("LIQPAY_CB_EMPTY")
            raise HTTPException(status_code=400, detail="Missing data")
        
        if generate_signature(data) != signature:
            logger.error("LIQPAY_CB_SIGN_INVALID")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        decoded_data = json.loads(base64.b64decode(data).decode())
        status = decoded_data.get("status")
        order_id = decoded_data.get("order_id")
        
        logger.info(f"LIQPAY_CB_PROC: ORDER_{order_id} STAT_{status}")
        
        if status in ["success", "wait_accept"]:
            order = db.query(Order).filter(Order.id == int(order_id)).first()
            if order:
                old_status = order.status
                order.status = "PAID"
                order.payment_status = "SUCCESS"
                if hasattr(order, 'add_status_log'):
                    order.add_status_log(old_status, "PAID", "liqpay_callback")
                db.commit()
                logger.info(f"LIQPAY_CB_SUCCESS: ORDER_{order_id}")
            else:
                logger.warning(f"LIQPAY_CB_ORDER_MISSING: {order_id}")
        else:
            logger.warning(f"LIQPAY_CB_NOT_PAID: ORDER_{order_id} STAT_{status}")
                
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"LIQPAY_CB_FATAL: {e}")
        return {"status": "error", "message": str(e)}