from sqlalchemy import Column, String, Float, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"extend_existing": True}
    id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, nullable=True, index=True)
    name_ru = Column(String, nullable=True)
    name_ua = Column(String, nullable=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    children = relationship("Category", primaryjoin="Category.id==foreign(Category.parent_id)", viewonly=True)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}
    id = Column(String, primary_key=True, index=True)
    name_ru = Column(String, nullable=True)
    name_ua = Column(String, nullable=True)
    name = Column(String, nullable=False)
    price = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    image = Column(String, nullable=True)
    category_id = Column(String, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")

class Client(Base):
    __tablename__ = "clients"
    phone = Column(String, primary_key=True, index=True)
    fio = Column(String, nullable=False)
    viber = Column(String, nullable=True)
    city = Column(String, nullable=True)
    discount_percent = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    orders = relationship("Order", back_populates="client")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_phone = Column(String, ForeignKey("clients.phone"))
    items_json = Column(Text, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="Новий")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    np_city_ref = Column(String, nullable=True)
    np_warehouse_ref = Column(String, nullable=True)
    np_warehouse_desc = Column(Text, nullable=True)
    client = relationship("Client", back_populates="orders")