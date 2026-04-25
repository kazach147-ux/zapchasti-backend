import logging
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime
from app.config import IMAGEKIT_URL
from decimal import Decimal

logger = logging.getLogger("SCHEMAS")

class CategoryOut(BaseModel):
    id: str
    parent_id: Optional[str] = None
    name: str

    class Config:
        orm_mode = True

class CategoryTree(BaseModel):
    id: str
    name: str
    children: List["CategoryTree"] = Field(default_factory=list)

    class Config:
        orm_mode = True

class ProductOut(BaseModel):
    id: str
    name: str
    price: Decimal
    stock: int
    category_id: str
    image: Optional[str] = None

    class Config:
        orm_mode = True

    @validator("image", pre=False, always=True)
    def assemble_image_url(cls, v):
        try:
            if v and not v.startswith("http"):
                res = f"{IMAGEKIT_URL.rstrip('/')}/{v.lstrip('/')}"
                return res
            return v
        except Exception as e:
            logger.error(f"IMAGE_URL_VALIDATION_ERROR: {e}")
            return v

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    ttn: Optional[str] = None
    admin_comment: Optional[str] = None
    delivery_type: Optional[str] = None
    pickup_address: Optional[str] = None
    payment_method: Optional[str] = None

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    client_phone: str
    fio: Optional[str] = "Клієнт"
    viber: Optional[str] = None
    tg_username: Optional[str] = None
    items_json: Any
    total_price: Decimal
    status: str
    payment_status: Optional[str] = "WAITING"
    comment: Optional[str] = None
    admin_comment: Optional[str] = None
    created_at: datetime
    np_city_name: Optional[str] = None
    np_warehouse_desc: Optional[str] = None
    ttn: Optional[str] = None
    payment_method: Optional[str] = "cod"
    delivery_type: Optional[str] = "NP"
    pickup_address: Optional[str] = None
    source: Optional[str] = "WEB"

    class Config:
        orm_mode = True