import json
import logging
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Text, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship, backref
from app.database import Base

logger = logging.getLogger("MODELS")

class AdminConfig(Base):
    __tablename__ = "admin_config"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    xml_url = Column(String, nullable=False)
    language = Column(String, default="uk")

class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    name_ru = Column(String, nullable=True)
    name_ua = Column(String, nullable=True)
    image = Column(String, nullable=True)
    
    children = relationship("Category", backref=backref("parent", remote_side=[id]))
    products = relationship("Product", back_populates="category_rel")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    sku = Column(String, unique=True, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String, nullable=True)
    title_ua = Column(String, nullable=True)
    title_ru = Column(String, nullable=True)
    description_ua = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    images = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    category_id = Column(String, ForeignKey("categories.id"), index=True, nullable=True)
    category_rel = relationship("Category", back_populates="products")

class Client(Base):
    __tablename__ = "clients"
    phone = Column(String, primary_key=True, index=True)
    fio = Column(String, nullable=True, index=True)
    viber = Column(String, nullable=True)
    tg_username = Column(String, nullable=True)
    city = Column(String, nullable=True)
    discount_percent = Column(Numeric(5, 2), default=0.0)
    total_spent = Column(Numeric(14, 2), default=0.0)
    last_order_date = Column(DateTime, default=datetime.utcnow)
    orders = relationship("Order", back_populates="client", cascade="all, delete")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_phone = Column(String, ForeignKey("clients.phone"), index=True)
    fio = Column(String, nullable=True, index=True)
    viber = Column(String, nullable=True)
    tg_username = Column(String, nullable=True)
    items_json = Column(Text, nullable=False)
    total_price = Column(Numeric(14, 2), nullable=False)
    status = Column(String, default="NEW", index=True)
    payment_status = Column(String, default="WAITING")
    comment = Column(Text, nullable=True)
    admin_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    np_city_ref = Column(String, nullable=True)
    np_city_name = Column(String, nullable=True)
    np_warehouse_ref = Column(String, nullable=True)
    np_warehouse_desc = Column(Text, nullable=True)
    ttn = Column(String, nullable=True)
    payment_method = Column(String, default="cod")
    delivery_type = Column(String, default="NP")
    pickup_address = Column(String, nullable=True)
    pickup_date = Column(DateTime, nullable=True)
    status_history = Column(Text, default="[]")
    processed_by = Column(String, nullable=True)
    source = Column(String, default="WEB")
    client = relationship("Client", back_populates="orders")

    def add_status_log(self, old_status, new_status, user="admin"):
        try:
            current_history = self.status_history if self.status_history else "[]"
            history = json.loads(current_history)
            history.append({
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": user,
                "changed_at": datetime.utcnow().isoformat()
            })
            self.status_history = json.dumps(history, ensure_ascii=False)
        except Exception as e:
            logger.error(f"LOG_STATUS_FAIL: ORDER_{self.id} ERR_{str(e)}")