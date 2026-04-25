import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from .models import Product, Category
import os
import csv
import logging
from datetime import datetime

logger = logging.getLogger("UTILS")

def generate_external_xml(db: Session, base_url: str = "https://zapchasti-backend-2.onrender.com"):
    logger.info("XML_GEN_START")
    try:
        products = db.query(Product).all()
        categories = db.query(Category).all()
        
        root = ET.Element("yml_catalog", date=datetime.now().strftime("%Y-%m-%d %H:%M"))
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
            # Используем title_ua, так как поля name в модели нет
            ET.SubElement(offer, "name").text = prod.title_ua or prod.sku
            ET.SubElement(offer, "price").text = str(prod.price)
            ET.SubElement(offer, "currencyId").text = "UAH"
            ET.SubElement(offer, "categoryId").text = str(prod.category_id)
            if prod.images and isinstance(prod.images, list) and len(prod.images) > 0:
                ET.SubElement(offer, "picture").text = prod.images[0]
            ET.SubElement(offer, "stock_quantity").text = str(prod.stock)
            
        tree = ET.ElementTree(root)
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            logger.info(f"STATIC_DIR_CREATED: {static_dir}")
            
        file_path = os.path.join(static_dir, "external_feed.xml")
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"XML_GEN_SUCCESS: {file_path}")
    except Exception as e:
        logger.error(f"XML_GEN_CRITICAL_ERROR: {e}")

def update_prices_from_feeds(db: Session):
    logger.info("FEED_SYNC_START")
    
    xml_path = "clean_prom_ready_filter.xml"
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            count = 0
            for offer in root.findall(".//offer"):
                o_id = offer.get("id")
                price = offer.findtext("price")
                if o_id and price:
                    product = db.query(Product).filter(Product.id == o_id).first()
                    if product:
                        product.price = float(price)
                        count += 1
            db.commit()
            logger.info(f"SYNC_XML_DONE: {count} PRODUCTS")
        except Exception as e:
            logger.error(f"SYNC_XML_ERROR: {e}")

    csv_path = "clean_opencart_ready_filter.csv"
    if os.path.exists(csv_path):
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    model = row.get("model")
                    price = row.get("price")
                    if model and price:
                        product = db.query(Product).filter(Product.id == model).first()
                        if product:
                            product.price = float(price)
                            count += 1
                db.commit()
                logger.info(f"SYNC_CSV_DONE: {count} PRODUCTS")
        except Exception as e:
            logger.error(f"SYNC_CSV_ERROR: {e}")