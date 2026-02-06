from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Optional, List
from app.database import get_db
from app.models import Category, Product
from deep_translator import GoogleTranslator

router = APIRouter()

def translate_text(text_to_translate: str, target_lang: str) -> str:
    if not text_to_translate or len(str(text_to_translate)) < 2:
        return text_to_translate
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text_to_translate)
    except:
        return text_to_translate

@router.get("/categories/tree")
def categories_tree(
    db: Session = Depends(get_db),
    accept_language: Optional[str] = Header("ru")
):
    lang = "ua" if "ua" in accept_language.lower() else "ru"
    categories = db.query(Category).all()
    
    query_sql = text("SELECT category_id, COUNT(id) FROM products GROUP BY category_id")
    products_raw = db.execute(query_sql).fetchall()
    products_count = {str(r[0]) if r[0] is not None else "None": r[1] for r in products_raw}
    
    by_parent: Dict[Optional[str], List[Category]] = {}
    for c in categories:
        by_parent.setdefault(c.parent_id, []).append(c)

    def build(parent_id: Optional[str]):
        result = []
        for cat in by_parent.get(parent_id, []):
            name_display = cat.name_ua if lang == "ua" else cat.name_ru
            
            if lang == "ua" and (not name_display or name_display == cat.name_ru):
                name_display = translate_text(cat.name, "uk")
                cat.name_ua = name_display
                db.add(cat)
            
            result.append({
                "id": cat.id,
                "name": name_display or cat.name,
                "image": cat.image or "",
                "children": build(cat.id)
            })
        return result

    res = build(None)
    db.commit()
    return res

@router.get("/products")
def list_products(
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50, 
    offset: int = 0, 
    db: Session = Depends(get_db),
    accept_language: Optional[str] = Header("ru")
):
    lang = "ua" if "ua" in accept_language.lower() else "ru"
    search_term = search or query
    db_query = db.query(Product)
    
    if search_term:
        db_query = db_query.filter(
            (Product.name_ru.ilike(f"%{search_term}%")) | 
            (Product.name_ua.ilike(f"%{search_term}%")) |
            (Product.name.ilike(f"%{search_term}%"))
        )
    
    if category_id:
        db_query = db_query.filter(Product.category_id == category_id)
    
    products = db_query.order_by(Product.id.desc()).offset(offset).limit(limit).all()
    total = db_query.count()
    
    items = []
    for p in products:
        name_display = p.name_ua if lang == "ua" else p.name_ru
        
        if lang == "ua" and (not name_display or name_display == p.name_ru):
            name_display = translate_text(p.name, "uk")
            p.name_ua = name_display
            db.add(p)

        items.append({
            "id": p.id,
            "name": name_display or p.name,
            "price": p.price,
            "stock": p.stock,
            "image": p.image or "",
            "category_id": p.category_id
        })
    db.commit()
    return {"total": total, "items": items, "limit": limit, "offset": offset}

@router.get("/search")
def search_products(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    accept_language: Optional[str] = Header("ru")
):
    return list_products(search=query, limit=limit, offset=offset, db=db, accept_language=accept_language)