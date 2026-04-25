import logging
import json
import os
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product

logger = logging.getLogger("IMPORTER")
router = APIRouter()

def to_float(val):
    try:
        return float(val) if val else 0.0
    except:
        return 0.0

def to_int(val):
    try:
        return int(val) if val else 0
    except:
        return 0

def generate_uuid(seed: str):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(seed)))

@router.post("/admin/import-xml")
async def run_import(db: Session = Depends(get_db)):
    paths = [
        os.path.join(os.getcwd(), "database_ready.json"),
        os.path.join(os.getcwd(), "server", "database_ready.json"),
        "/opt/render/project/src/database_ready.json"
    ]
    
    file_path = None
    for p in paths:
        if os.path.exists(p):
            file_path = p
            break

    if not file_path:
        logger.error("STATUS:FILE_NOT_FOUND")
        return {"status": "error", "message": "file_not_found"}

    logger.info(f"STATUS:START_IMPORT_FILE:{file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        logger.info(f"STATUS:LOADED_JSON_ITEMS:{len(items)}")

        existing_products = {p.sku: p for p in db.query(Product).all()}
        logger.info(f"STATUS:DB_PRODUCTS_LOADED_TO_MEMORY:{len(existing_products)}")

        count_upd = 0
        count_new = 0

        for item in items:
            sku = str(item.get("sku", ""))
            if not sku:
                logger.warning("SKIP_ITEM:NO_SKU")
                continue

            price = to_float(item.get("price"))
            stock = to_int(item.get("quantity"))
            
            data = {
                "price": price,
                "stock": stock,
                "title_ua": item.get("title_ua"),
                "title_ru": item.get("title_ru"),
                "images": item.get("images", []),
                "category": item.get("category"),
                "is_active": True
            }

            product = existing_products.get(sku)

            if product:
                for key, value in data.items():
                    setattr(product, key, value)
                count_upd += 1
            else:
                new_p = Product(id=generate_uuid(f"prod_{sku}"), sku=sku, **data)
                db.add(new_p)
                count_new += 1

            if (count_upd + count_new) % 100 == 0:
                db.flush()
                logger.info(f"STATUS:PROGRESS:UPDATED:{count_upd}:NEW:{count_new}")

        db.commit()
        logger.info(f"STATUS:FINISHED:UPDATED:{count_upd}:NEW:{count_new}")
        return {"status": "success", "updated": count_upd, "new": count_new}

    except Exception as e:
        db.rollback()
        logger.exception("STATUS:FATAL_ERROR_DURING_IMPORT")
        return {"status": "error", "message": str(e)}