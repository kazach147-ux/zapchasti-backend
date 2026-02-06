from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import Order, Client
import json

router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    qty: int


class OrderCreate(BaseModel):
    fio: str
    phone: str
    viber: Optional[str] = None
    city: str
    city_ref: Optional[str] = None
    warehouse_ref: Optional[str] = None
    warehouse_desc: Optional[str] = None
    comment: Optional[str] = None
    items: List[OrderItem]
    total_price: float


@router.post("/create")
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        client = db.query(Client).filter(Client.phone == order_data.phone).first()

        if not client:
            client = Client(
                phone=order_data.phone,
                fio=order_data.fio,
                viber=order_data.viber,
                city=order_data.city,
                total_spent=0.0,
                discount_percent=0.0
            )
            db.add(client)
        else:
            client.fio = order_data.fio
            client.viber = order_data.viber
            client.city = order_data.city

        discount = getattr(client, "discount_percent", 0.0) or 0.0
        final_price = order_data.total_price * (1 - discount / 100) if discount > 0 else order_data.total_price

        items_list = []
        for item in order_data.items:
            items_list.append({
                "id": str(item.id),
                "name": str(item.name),
                "price": float(item.price),
                "qty": int(item.qty)
            })

        new_order = Order(
            client_phone=order_data.phone,
            items_json=json.dumps(items_list, ensure_ascii=False),
            total_price=float(final_price),
            comment=order_data.comment,
            np_city_ref=order_data.city_ref,
            np_warehouse_ref=order_data.warehouse_ref,
            np_warehouse_desc=order_data.warehouse_desc,
            status="Новий"
        )

        client.total_spent = (getattr(client, "total_spent", 0.0) or 0.0) + float(final_price)

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {
            "status": "ok",
            "order_id": new_order.id,
            "applied_discount": discount
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
def list_orders(db: Session = Depends(get_db)):
    try:
        orders = db.query(Order).order_by(Order.id.desc()).all()

        result = []
        for o in orders:
            result.append({
                "id": o.id,
                "phone": o.client_phone,
                "fio": o.client.fio if o.client else "Невідомо",
                "items": json.loads(o.items_json) if o.items_json else [],
                "total_price": o.total_price,
                "status": o.status,
                "city": o.client.city if o.client else "",
                "warehouse_desc": o.np_warehouse_desc or "",
                "city_ref": o.np_city_ref or "",
                "warehouse_ref": o.np_warehouse_ref or ""
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear_all")
def clear_all_orders(db: Session = Depends(get_db)):
    try:
        db.query(Order).delete()
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        db.delete(order)
        db.commit()

        return {"status": "ok"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients")
def list_clients(db: Session = Depends(get_db)):
    try:
        clients = db.query(Client).all()

        return [
            {
                "phone": c.phone,
                "name": c.fio,
                "discount": c.discount_percent,
                "total_spent": c.total_spent,
                "city": c.city
            }
            for c in clients
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
