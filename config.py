from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "app", "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

FEED_URL = os.getenv("FEED_URL", "http://sr.agro-moto-tata.com:85/Prom_VO.xml")
FEED_LOCAL_PATH = os.path.join(DATA_DIR, "test_products.xml")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

DB_URL = DATABASE_URL or f"sqlite:///{os.path.join(DATA_DIR, 'zapchasti.db')}"
APP_NAME = "zapchasti_app"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "3182231822")