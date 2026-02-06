import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from .models import Product, Category
import requests
import os

def generate_external_xml(db: Session):
    products = db.query(Product).all()
    categories = db.query(Category).all()
    
    root = ET.Element("yml_catalog", date="2024-01-01 00:00")
    shop = ET.SubElement(root, "shop")
    
    currencies = ET.SubElement(shop, "currencies")
    ET.SubElement(currencies, "currency", id="UAH", rate="1")
    
    cats_element = ET.SubElement(shop, "categories")
    for cat in categories:
        cat_item = ET.SubElement(cats_element, "category", id=str(cat.id))
        if cat.parent_id:
            cat_item.set("parentId", str(cat.parent_id))
        cat_item.text = cat.name
        
    offers = ET.SubElement(shop, "offers")
    for prod in products:
        offer = ET.SubElement(offers, "offer", id=str(prod.id), available="true" if prod.stock > 0 else "false")
        ET.SubElement(offer, "name").text = prod.name
        ET.SubElement(offer, "price").text = str(prod.price)
        ET.SubElement(offer, "currencyId").text = "UAH"
        ET.SubElement(offer, "categoryId").text = str(prod.category_id)
        if prod.image:
            ET.SubElement(offer, "picture").text = f"https://твой-домен.com{prod.image}"
        ET.SubElement(offer, "stock_quantity").text = str(prod.stock)
        
    tree = ET.ElementTree(root)
    xml_path = os.path.join(os.path.dirname(__file__), "..", "static", "export_prom.xml")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    return xml_path

def sync_with_prom_api(prod_id, price, stock):
    # Здесь будет метод для мгновенного обновления через API Prom, если понадобится
    pass