from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import xml.etree.ElementTree as ET
import requests
import os
from app.database import get_db
from app.models import Category, Product
from app.config import FEED_URL
from app.sync_services import generate_external_xml

router = APIRouter(tags=["Import"])

def download_image(url: str, obj_id: str, prefix=""):
    if not url or not url.startswith("http"):
        return ""
    try:
        img_name = f"{prefix}{obj_id}.jpg"
        current_dir = os.path.dirname(os.path.dirname(__file__))
        static_dir = os.path.join(current_dir, "static", "images")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        save_path = os.path.join(static_dir, img_name)
        if os.path.exists(save_path):
            return img_name
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return img_name
    except:
        pass
    return ""

@router.post("/run")
def run_import(db: Session = Depends(get_db)):
    try:
        response = requests.get(FEED_URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        shop = root.find("shop")
        if shop is None: 
            return {"status": "error", "message": "Invalid XML"}

        added, updated = 0, 0
        cats = shop.find("categories")
        if cats is not None:
            for c in cats.findall("category"):
                c_id = c.get("id")
                p_id = c.get("parentId")
                name = c.text or ""
                cat = db.query(Category).filter(Category.id == str(c_id)).first()
                if cat:
                    cat.name = name
                    cat.name_ru, cat.name_ua = name, name
                    cat.parent_id = str(p_id) if p_id else None
                else:
                    db.add(Category(id=str(c_id), parent_id=str(p_id) if p_id else None, 
                                    name=name, name_ru=name, name_ua=name))
            db.commit()

        offers = shop.find("offers")
        if offers is not None:
            for offer in offers.findall("offer"):
                o_id = offer.get("id")
                cat_id = offer.findtext("categoryId")
                name = offer.findtext("name") or ""
                price_str = offer.findtext("price")
                try: 
                    price = float(price_str.replace(',', '.') if price_str else 0)
                except: 
                    price = 0.0
                try: 
                    stock = int(offer.findtext("quantity") or offer.findtext("stock") or "0")
                except: 
                    stock = 0
                
                remote_image = offer.findtext("picture") or offer.findtext("image") or ""
                local_image_name = download_image(remote_image, str(o_id))
                
                prod = db.query(Product).filter(Product.id == str(o_id)).first()
                if prod:
                    prod.name, prod.name_ru, prod.name_ua = name, name, name
                    prod.price, prod.stock = price, stock
                    prod.category_id = str(cat_id) if cat_id else None
                    if local_image_name: 
                        prod.image = local_image_name
                    updated += 1
                else:
                    db.add(Product(id=str(o_id), name=name, name_ru=name, name_ua=name,
                                   price=price, stock=stock, category_id=str(cat_id), image=local_image_name))
                    added += 1
            db.commit()
        
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
            
        try:
            generate_external_xml(db)
        except:
            pass
            
        return {"status": "ok", "added": added, "updated": updated}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))