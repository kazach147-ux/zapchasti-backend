import os
import logging
import sys
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CONFIG")

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "app", "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"DIR_CREATED: {DATA_DIR}")

IMAGEKIT_URL = os.getenv("IMAGEKIT_URL_ENDPOINT")
FEED_URL = os.getenv("FEED_URL")

SUPABASE_URL = "https://lapnypjlgxydmafclfph.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "6543")
DB_NAME = "postgres"

if not all([DB_USER, DB_PASSWORD, DB_HOST]):
    logger.critical("DB_ENV_MISSING")
    sys.exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

APP_NAME = "zapchasti_app"
ADMIN_PASSWORD = os.getenv("ADMIN_PASS")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logger.info(f"CONFIG_READY: {APP_NAME}")