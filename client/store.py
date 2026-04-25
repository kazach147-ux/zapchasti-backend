import json
import os
import sqlite3
import time
import requests

class Store:
    _cart = []
    _lang_data = {}
    SERVER_URL = ""
    IMAGE_BASE_URL = ""
    GIST_URL = "https://raw.githubusercontent.com/kazach147-ux/zapchasti-backend/main/server_url.txt"
    _lang = "ru"
    _observers = []
    
    COLOR_BG = (0.08, 0.08, 0.1, 1)
    COLOR_HEADER = (0.12, 0.12, 0.15, 1)
    COLOR_CARD = (0.15, 0.15, 0.18, 1)
    COLOR_ACCENT = (1, 0.5, 0, 1)
    COLOR_TEXT_LIGHT = (1, 1, 1, 1)

    DB_PATH = "cache.db"
    CONFIG_PATH = "config.json"
    PROFILE_PATH = "profile.json"
    IMG_CACHE_DIR = "cache_images"
    CACHE_TTL = 3600 * 24

    @staticmethod
    def get_text(key, default=""):
        k = str(key).lower()
        val = Store._lang_data.get(k)
        if val: return val
        return default if default else key

    @staticmethod
    def init():
        if not os.path.exists(Store.IMG_CACHE_DIR):
            os.makedirs(Store.IMG_CACHE_DIR)
        conn = sqlite3.connect(Store.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cart (id TEXT PRIMARY KEY, qty INTEGER, data TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS search_cache (query TEXT PRIMARY KEY, data TEXT, timestamp REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS products_cache (id TEXT PRIMARY KEY, category_id TEXT, data TEXT, timestamp REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories_cache (id TEXT PRIMARY KEY, data TEXT, timestamp REAL)''')
        conn.commit()
        conn.close()
        
        Store.load_config()
        Store.fetch_server_url()
        Store.fetch_remote_config()
        Store.load_lang()
        Store._load_cart_from_db()

    @staticmethod
    def fetch_server_url():
        try:
            r = requests.get(Store.GIST_URL, timeout=5)
            if r.status_code == 200:
                new_url = r.text.strip()
                if new_url.startswith("http"):
                    Store.SERVER_URL = new_url
                    Store.save_config()
        except: pass

    @staticmethod
    def fetch_remote_config():
        if not Store.SERVER_URL: return
        try:
            response = requests.get(f"{Store.SERVER_URL}/api/config", timeout=10)
            if response.status_code == 200:
                data = response.json()
                Store.SERVER_URL = data.get("api_url", Store.SERVER_URL)
                Store.IMAGE_BASE_URL = data.get("image_base_url", "")
                Store.save_config()
        except: pass

    @staticmethod
    def load_config():
        if os.path.exists(Store.CONFIG_PATH):
            try:
                with open(Store.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    Store._lang = config.get("language", "ru")
                    Store.SERVER_URL = config.get("server_url", "")
                    Store.IMAGE_BASE_URL = config.get("image_base_url", "")
            except: pass

    @staticmethod
    def save_config():
        try:
            with open(Store.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    "language": Store._lang, 
                    "server_url": Store.SERVER_URL,
                    "image_base_url": Store.IMAGE_BASE_URL
                }, f)
        except: pass

    @staticmethod
    def get_image_url(image_path):
        if not image_path: return ""
        filename = os.path.basename(image_path)
        local_path = os.path.join(Store.IMG_CACHE_DIR, filename)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return os.path.abspath(local_path)
        if image_path.startswith('http'): return image_path
        if not Store.IMAGE_BASE_URL: return ""
        return f"{Store.IMAGE_BASE_URL}{filename}"

    @staticmethod
    def load_lang():
        lang_file = f"translations_{Store._lang}.json"
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    Store._lang_data = {str(k).lower(): v for k, v in data.items()}
            except: 
                Store._lang_data = {}
        else:
            Store._lang_data = {}

    @staticmethod
    def set_lang(lang):
        if Store._lang != lang:
            Store._lang = lang
            Store.load_lang()
            Store.save_config()
            Store.notify_observers()

    @staticmethod
    def add_observer(callback):
        if callback not in Store._observers:
            Store._observers.append(callback)

    @staticmethod
    def notify_observers():
        for callback in Store._observers:
            try: callback()
            except: pass

    @staticmethod
    def get_user_data():
        if os.path.exists(Store.PROFILE_PATH):
            try:
                with open(Store.PROFILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"fio": "", "phone": "", "viber": "", "city": "", "warehouse": ""}

    @staticmethod
    def save_user_data(data):
        try:
            with open(Store.PROFILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except: pass

    @staticmethod
    def _load_cart_from_db():
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM cart")
            Store._cart = [json.loads(row[0]) for row in cursor.fetchall()]
            conn.close()
        except: Store._cart = []

    @staticmethod
    def get_cart():
        return Store._cart.copy()

    @staticmethod
    def add_to_cart(product):
        p_id = str(product.get('id'))
        found = False
        for item in Store._cart:
            if str(item.get('id')) == p_id:
                item['qty'] = item.get('qty', 1) + 1
                found = True
                Store._sync_cart_db(item)
                break
        if not found:
            product['qty'] = 1
            Store._cart.append(product)
            Store._sync_cart_db(product)
        Store.notify_observers()

    @staticmethod
    def update_cart_qty(p_id, new_qty):
        p_id = str(p_id)
        for item in Store._cart:
            if str(item.get('id')) == p_id:
                item['qty'] = max(1, new_qty)
                Store._sync_cart_db(item)
                break
        Store.notify_observers()

    @staticmethod
    def remove_from_cart(p_id):
        p_id = str(p_id)
        Store._cart = [item for item in Store._cart if str(item.get('id')) != p_id]
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cart WHERE id=?", (p_id,))
            conn.commit()
            conn.close()
        except: pass
        Store.notify_observers()

    @staticmethod
    def clear_cart():
        Store._cart = []
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cart")
            conn.commit()
            conn.close()
        except: pass
        Store.notify_observers()

    @staticmethod
    def _sync_cart_db(item):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO cart (id, qty, data) VALUES (?, ?, ?)",
                           (str(item['id']), item['qty'], json.dumps(item, ensure_ascii=False)))
            conn.commit()
            conn.close()
        except: pass

    @staticmethod
    def cache_products(products, category_id=None):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            ts = time.time()
            for p in products:
                cursor.execute("INSERT OR REPLACE INTO products_cache (id, category_id, data, timestamp) VALUES (?, ?, ?, ?)",
                               (str(p['id']), str(category_id) if category_id else "", json.dumps(p, ensure_ascii=False), ts))
            conn.commit()
            conn.close()
        except: pass

    @staticmethod
    def get_cached_products(offset=0, limit=50, category_id=None, search=None):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            query = "SELECT data FROM products_cache"
            params = []
            conditions = []
            if category_id:
                conditions.append("category_id = ?")
                params.append(str(category_id))
            if search:
                conditions.append("data LIKE ?")
                params.append(f"%{search}%")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            res = [json.loads(row[0]) for row in cursor.fetchall()]
            conn.close()
            return res
        except: return []

    @staticmethod
    def cache_categories(categories):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            ts = time.time()
            for c in categories:
                cursor.execute("INSERT OR REPLACE INTO categories_cache (id, data, timestamp) VALUES (?, ?, ?)",
                               (str(c['id']), json.dumps(c, ensure_ascii=False), ts))
            conn.commit()
            conn.close()
        except: pass

    @staticmethod
    def get_cached_categories():
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM categories_cache")
            res = [json.loads(row[0]) for row in cursor.fetchall()]
            conn.close()
            return res
        except: return []

    @staticmethod
    def _get_from_cache(key):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT data, timestamp FROM search_cache WHERE query = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                data_str, ts = row
                if time.time() - ts < Store.CACHE_TTL:
                    return json.loads(data_str)
        except: pass
        return None

    @staticmethod
    def _save_to_cache(key, value):
        try:
            conn = sqlite3.connect(Store.DB_PATH)
            cursor = conn.cursor()
            ts = time.time()
            cursor.execute("INSERT OR REPLACE INTO search_cache (query, data, timestamp) VALUES (?, ?, ?)",
                           (key, json.dumps(value, ensure_ascii=False), ts))
            conn.commit()
            conn.close()
        except: pass

    @staticmethod
    def get_cities_from_server(search_query):
        if not search_query or not Store.SERVER_URL: return []
        q = search_query.lower().strip()
        cache_key = f"cities:{q}"
        cached = Store._get_from_cache(cache_key)
        if cached is not None: return cached
        
        print(f"[CITY] REQUEST START: {q}")
        try:
            r = requests.get(f"{Store.SERVER_URL}/api/shipping/cities", params={"search": q}, timeout=10)
            print(f"[CITY] STATUS: {r.status_code}")
            if r.status_code == 200:
                items = r.json()
                print(f"[CITY] JSON LEN: {len(items)}")
                result = [{"name": item.get("name", ""), "ref": item.get("ref", "")} for item in items if item.get("name") and item.get("ref")]
                Store._save_to_cache(cache_key, result)
                return result
            else:
                print(f"[CITY] ERROR RAW: {r.text}")
                return []
        except Exception as e:
            print(f"[CITY] EXCEPTION: {e}")
            return []

    @staticmethod
    def get_warehouses_from_server(city_ref, search_text=""):
        if not city_ref or not Store.SERVER_URL: return []
        cache_key = f"warehouses:{city_ref}:{search_text.lower().strip()}"
        cached = Store._get_from_cache(cache_key)
        if cached is not None: return cached
        
        print(f"[WH] REQUEST START FOR CITY: {city_ref}")
        try:
            params = {"city_ref": city_ref}
            if search_text: params["search"] = search_text.strip()
            r = requests.get(f"{Store.SERVER_URL}/api/shipping/warehouses", params=params, timeout=10)
            print(f"[WH] STATUS: {r.status_code}")
            if r.status_code == 200:
                items = r.json()
                print(f"[WH] JSON LEN: {len(items)}")
                result = [{"name": w.get("name", ""), "ref": w.get("ref", "")} for w in items if w.get("name") and w.get("ref")]
                Store._save_to_cache(cache_key, result)
                return result
            else:
                print(f"[WH] ERROR RAW: {r.text}")
                return []
        except Exception as e:
            print(f"[WH] EXCEPTION: {e}")
            return []

    @staticmethod
    def create_order(order_data):
        if not Store.SERVER_URL: return None
        try:
            r = requests.post(f"{Store.SERVER_URL}/api/orders/create", json=order_data, timeout=15)
            return r.json() if r.status_code == 200 else None
        except:
            return None

Store.init()