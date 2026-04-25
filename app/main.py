import os
import uvicorn
import httpx
import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from aiogram import Bot, Dispatcher, types
from app.database import Base, engine
from app.routers.importer import router as importer_router
from app.routers.catalog import router as catalog_router
from app.routers.orders import router as orders_router
from app.routers.shipping import router as shipping_router
from app.routers.payments import router as payments_router
from app.routers.admin import router as admin_router
from app.auth import check_auth
from app.config import IMAGEKIT_URL, BOT_TOKEN, WEBHOOK_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SERVER")

http_client = httpx.AsyncClient(timeout=30.0)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def setup_webhook():
    logger.info("TG_WEBHOOK_INIT_START")
    await asyncio.sleep(5)
    try:
        webhook_info = await bot.get_webhook_info()
        logger.info(f"TG_CURRENT_WEBHOOK: {webhook_info.url}")
        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
            logger.info(f"TG_WEBHOOK_UPDATED: {WEBHOOK_URL}")
        else:
            logger.info("TG_WEBHOOK_ALREADY_SET")
    except Exception as e:
        logger.error(f"TG_WEBHOOK_FATAL_ERROR: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LIFESPAN_BOOT_SEQUENCE_STARTED")
    asyncio.create_task(setup_webhook())
    yield
    await http_client.aclose()
    logger.info("LIFESPAN_SHUTDOWN_CLEANUP")

app = FastAPI(title="zapchasti_app", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    logger.info("DB_CONNECTION_ATTEMPT")
    Base.metadata.create_all(bind=engine)
    logger.info("DB_CONNECTION_SUCCESS_READY")
except Exception as e:
    logger.critical(f"DB_CONNECTION_CRITICAL_FAILURE: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_WEB_DIR = os.path.join(BASE_DIR, "static", "admin_web")
logger.info(f"ADMIN_PATH_RESOLVED: {ADMIN_WEB_DIR}")

@app.get("/")
@app.head("/")
async def root_stub():
    logger.info("SERVER_HEALTH_CHECK_REQUEST")
    return PlainTextResponse("SERVER_OK", status_code=200)

@app.post("/webhook", include_in_schema=False)
async def telegram_webhook(request: Request):
    logger.info("TG_WEBHOOK_INCOMING_UPDATE")
    try:
        update_data = await request.json()
        logger.info(f"TG_RAW_DATA: {update_data}")
        update = types.Update(**update_data)
        Bot.set_current(bot)
        Dispatcher.set_current(dp)
        await dp.process_update(update)
        logger.info("TG_UPDATE_PROCESSED_SUCCESSFULLY")
        return {"ok": True}
    except Exception as e:
        logger.error(f"TG_WEBHOOK_PROCESSING_ERROR: {e}")
        return {"ok": False}

@app.get("/admin_web/{file_path:path}")
async def protected_admin(file_path: str = "", user: str = Depends(check_auth)):
    logger.info(f"ADMIN_ACCESS_REQUEST: user={user}, path={file_path}")
    if not file_path or file_path == "/":
        file_path = "index.html"
    full_path = os.path.join(ADMIN_WEB_DIR, file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        logger.info(f"ADMIN_FILE_SERVED: {full_path}")
        return FileResponse(full_path)
    logger.warning(f"ADMIN_FILE_NOT_FOUND_404: {full_path}")
    raise HTTPException(status_code=404)

logger.info("ROUTERS_REGISTRATION_START")
app.include_router(importer_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(shipping_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
logger.info("ROUTERS_REGISTRATION_COMPLETED_WITH_API_PREFIX")

@app.get("/api/config")
async def get_server_config(request: Request):
    host_url = f"{request.url.scheme}://{request.url.netloc}"
    logger.info(f"CONFIG_DATA_REQUESTED_FROM: {host_url}")
    return {
        "api_url": host_url,
        "image_base_url": f"{host_url}/api/proxy-image?url=",
        "imagekit_endpoint": IMAGEKIT_URL,
        "status": "online"
    }

@app.get("/api/proxy-image")
async def proxy_image(url: str = Query(...)):
    target_url = url if url.startswith("http") else f"{IMAGEKIT_URL.rstrip('/')}/{url.lstrip('/')}"
    logger.info(f"IMAGE_PROXY_REQUEST: {target_url}")
    try:
        resp = await http_client.get(target_url, follow_redirects=True)
        if resp.status_code == 200:
            logger.info(f"IMAGE_PROXY_SUCCESS: {target_url}")
            return StreamingResponse(resp.aiter_bytes(), media_type=resp.headers.get("Content-Type", "image/jpeg"))
        logger.warning(f"IMAGE_PROXY_REMOTE_ERROR: {resp.status_code} for {target_url}")
    except Exception as e:
        logger.error(f"IMAGE_PROXY_FATAL_ERROR: {url} - {e}")
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"SERVER_STARTING_ON_PORT_{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)