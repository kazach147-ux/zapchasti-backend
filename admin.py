from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.database import SessionLocal
from app.models import Order
import os
import requests

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBasic()

def load_admin_password():
    return os.getenv("ADMIN_PASSWORD", "admin")

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    admin_pass = load_admin_password()
    if credentials.username != "admin" or credentials.password != admin_pass:
        raise HTTPException(status_code=401)
    return credentials.username

@router.get("/test")
def test_admin(user: str = Depends(get_current_admin)):
    return {"ok": True}

@router.get("/orders/all")
def get_all_orders(user: str = Depends(get_current_admin)):
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        result = []
        for o in orders:
            result.append({
                "id": o.id,
                "fio": getattr(o, "fio", ""),
                "phone": getattr(o, "phone", ""),
                "total_price": getattr(o, "total_price", 0),
                "status": getattr(o, "status", ""),
                "ttn": getattr(o, "ttn", "")
            })
        return result
    finally:
        db.close()
