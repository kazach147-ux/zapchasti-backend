import requests
import json
import os
import time
import random
import re
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TARGETS_FILE = 'targets.txt'
DATABASE_FILE = 'database_ready.json'

COOKIES = os.getenv('TATA_COOKIES')

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def save_db(db):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def get_data():
    print(f"STARTING_UPDATER | TARGETS: {TARGETS_FILE} | DB: {DATABASE_FILE}")
    
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
        needed_skus = {str(item.get('sku')): item for item in db}
        print(f"LOADED_DB: {len(needed_skus)} records")
    except Exception as e:
        print(f"ERROR_DB_LOAD: {e}")
        return

    try:
        with open(TARGETS_FILE, 'r', encoding='utf-8') as f:
            urls = list(set([line.strip() for line in f if line.strip()]))
        print(f"LOADED_URLS: {len(urls)} links")
    except Exception as e:
        print(f"ERROR_URLS_LOAD: {e}")
        return

    session = get_session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if COOKIES:
        headers['Cookie'] = COOKIES
    
    total = len(urls)
    for i, url in enumerate(urls, 1):
        try:
            time.sleep(random.uniform(0.7, 1.8))
            res = session.get(url, headers=headers, timeout=15)
            
            if res.status_code != 200:
                print(f"[{i}/{total}] SKIP (STATUS {res.status_code}): {url}")
                continue

            html = res.text
            soup = BeautifulSoup(html, 'html.parser')

            sku = None
            sku_tag = soup.find(string=re.compile(r'ID:\s*\d+'))
            if sku_tag:
                sku = re.search(r'\d+', sku_tag).group()
            else:
                sku_match = re.search(r'ID:\s*(\d+)', html)
                if sku_match: sku = sku_match.group(1)

            if not sku or sku not in needed_skus:
                print(f"[{i}/{total}] NOT_IN_DB: SKU {sku} | {url}")
                continue

            price = None
            price_tag = soup.find(class_='price-value') or soup.find(id='price-value')
            if price_tag:
                price_text = price_tag.get_text(strip=True).replace(' ', '')
                digits = ''.join(filter(str.isdigit, price_text))
                price = int(digits) if digits else None

            if price and price > 0:
                needed_skus[sku]['price'] = price
                availability = soup.find(string=re.compile(r"налич", re.I))
                needed_skus[sku]['stock'] = 1 if availability else 0
                print(f"[{i}/{total}] UPDATED: SKU {sku} | PRICE: {price}")

            if i % 50 == 0:
                save_db(db)
                print(f"--- AUTO_SAVE AT STEP {i} ---")

        except Exception as e:
            print(f"[{i}/{total}] ERROR: {url} | {e}")
            continue

    save_db(db)
    print("FINISH: ALL_DATA_SAVED")

if __name__ == "__main__":
    get_data()