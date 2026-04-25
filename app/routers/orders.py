import os
import json
import logging
import httpx
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Order, Client, Product
from app.schemas import OrderUpdate
from app.config import BOT_TOKEN

router = APIRouter(tags=["Orders"])
logger = logging.getLogger("ORDERS")

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

async def send_telegram_notification(order_id: int, is_new: bool = True):
    logger.info(f"TG_NOTIF_START: ID_{order_id} IS_NEW_{is_new}")
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"TG_NOTIF_FAIL: ORDER_NOT_FOUND_ID_{order_id}")
            return
        if not BOT_TOKEN or not ADMIN_CHAT_ID:
            logger.error(f"TG_NOTIF_FAIL: MISSING_CONFIG_TOKEN_OR_CHATID")
            return

        try:
            items = json.loads(order.items_json) if isinstance(order.items_json, str) else (order.items_json or [])
        except Exception as e:
            logger.error(f"TG_NOTIF_JSON_ERR: ID_{order_id} ERROR_{e}")
            items = []

        items_list = ""
        for i in items:
            name = str(i.get('name', '?')).replace('<', '&lt;').replace('>', '&gt;')[:30]
            items_list += f"▪️ {name} x{i.get('qty', 1)} — {i.get('price', 0)} UAH\n"

        status_icons = {"NEW": "🆕", "PROCESSING": "⚙️", "SHIPPED": "🚚", "COMPLETED": "✅", "CANCELLED": "❌"}
        s_icon = status_icons.get(str(order.status).upper(), "❓")
        
        d_type = str(order.delivery_type or "").upper()
        is_np = any(x in d_type for x in ["NP", "NOVA", "ПОШТА", "НОВА"])
        delivery_info = f"🚀 Нова Пошта\n📍 {order.np_city_name or '---'}\n🏢 {order.np_warehouse_desc or '---'}" if is_np else f"🏃 Доставка: {order.delivery_type or 'Самовивіз'}"
        
        header = "🔔 <b>НОВЕ ЗАМОВЛЕННЯ</b>" if is_new else "🔄 <b>ОНОВЛЕНО</b>"
        text = (
            f"{header} <b>#{order.id}</b>\n"
            f"📅 {order.created_at.strftime('%d.%m %H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Клієнт:</b> {str(order.fio).replace('<', '&lt;')}\n"
            f"📞 <b>Тел:</b> <code>{order.client_phone}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{delivery_info}\n"
            f"💰 <b>Сума:</b> <code>{order.total_price}</code> <b>UAH</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🛒 <b>Товари:</b>\n{items_list}"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{s_icon} <b>Статус:</b> {order.status}\n"
            f"💬 <b>Коментар:</b> {str(order.comment or '---').replace('<', '&lt;')}"
        )

        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "⚙️ В роботу", "callback_data": f"status_processing_{order.id}"},
                     {"text": "🚚 Відправлено", "callback_data": f"status_shipped_{order.id}"}],
                    [{"text": "📱 Viber", "url": f"viber://chat?number={str(order.client_phone).replace('+', '')}"}]
                ]
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
            logger.info(f"TG_SEND_RESPONSE: ID_{order_id} CODE_{resp.status_code}")
    except Exception as e:
        logger.error(f"TG_FATAL_ERR: ID_{order_id} ERROR_{e}")
    finally:
        db.close()
        logger.info(f"TG_NOTIF_DB_CLOSED: ID_{order_id}")

@router.post("/orders/create")
def create_order(order_data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"ORDER_CREATE_REQ: DATA_{order_data}")
    try:
        phone = str(order_data.get("phone", ""))
        price_val = Decimal(str(order_data.get("total_price", 0)))
        fio_val = order_data.get("fio") or "Клієнт"
        items = order_data.get("items") or []
        
        for item in items:
            product = db.query(Product).filter(Product.id == item.get("id")).first()
            if product:
                old_stock = product.stock or 0
                product.stock = max(0, old_stock - item.get("qty", 1))
                logger.info(f"STOCK_UPDATE: PROD_{product.id} OLD_{old_stock} NEW_{product.stock}")

        client = db.query(Client).filter(Client.phone == phone).first()
        if not client:
            logger.info(f"CLIENT_NEW: PHONE_{phone}")
            client = Client(phone=phone, fio=fio_val, total_spent=price_val, last_order_date=datetime.utcnow())
            db.add(client)
        else:
            logger.info(f"CLIENT_EXISTS: PHONE_{phone}")
            client.total_spent = (client.total_spent or Decimal("0")) + price_val
            client.last_order_date = datetime.utcnow()
            if order_data.get("fio"): client.fio = order_data.get("fio")

        db.flush()
        new_order = Order(
            client_phone=phone, fio=fio_val,
            items_json=json.dumps(items, ensure_ascii=False),
            total_price=price_val, comment=order_data.get("comment"),
            np_city_name=order_data.get("city_name"), 
            np_warehouse_desc=order_data.get("warehouse_desc"),
            delivery_type=order_data.get("delivery_type", "NP"), 
            payment_method=order_data.get("payment_method", "cod"),
            source=order_data.get("source", "APP"), status="NEW"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        logger.info(f"ORDER_CREATED_SUCCESS: ID_{new_order.id}")
        
        background_tasks.add_task(send_telegram_notification, new_order.id, True)
        return {"status": "success", "order_id": new_order.id}
    except Exception as e:
        db.rollback()
        logger.error(f"ORDER_CREATE_FATAL: ERROR_{e}")
        raise HTTPException(status_code=500)

@router.patch("/orders/{order_id}")
def update_order(order_id: int, update_data: OrderUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    logger.info(f"ORDER_UPDATE_REQ: ID_{order_id} DATA_{update_data}")
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(f"ORDER_UPDATE_FAIL: NOT_FOUND_ID_{order_id}")
        raise HTTPException(status_code=404)
    
    data = update_data.dict(exclude_unset=True)
    if "status" in data and data["status"] == "SHIPPED":
        order.sent_at = datetime.utcnow()
        logger.info(f"ORDER_STATUS_SHIPPED: ID_{order_id}")
    
    for key, value in data.items():
        if hasattr(order, key):
            setattr(order, key, value)
    
    try:
        db.commit()
        logger.info(f"ORDER_UPDATE_SUCCESS: ID_{order_id}")
        background_tasks.add_task(send_telegram_notification, order.id, False)
        return {"status": "success", "order_id": order_id}
    except Exception as e:
        db.rollback()
        logger.error(f"ORDER_UPDATE_FATAL: ID_{order_id} ERROR_{e}")
        raise HTTPException(status_code=500)

@router.get("/orders/all")
def get_all_orders(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    logger.info(f"ORDERS_FETCH_ALL: LIMIT_{limit} OFFSET_{offset}")
    return db.query(Order).order_by(Order.id.desc()).offset(offset).limit(limit).all()