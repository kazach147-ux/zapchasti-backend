from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import Base, engine, SessionLocal
from app.routers.importer import router as importer_router, run_import
from app.routers.catalog import router as catalog_router
from app.routers.orders import router as orders_router
from app.routers.admin import router as admin_router, get_current_admin


Base.metadata.create_all(bind=engine)

app = FastAPI(title="zapchasti_app API")

ADMIN_CONFIG_FILE = "admin_settings.json"


def nightly_job():
    db = SessionLocal()
    try:
        run_import(db)
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(nightly_job, 'cron', hour=3, minute=0)
scheduler.start()


def save_admin_config(password):
    with open(ADMIN_CONFIG_FILE, "w") as f:
        json.dump({"admin_password": password}, f)


def load_admin_password():
    if os.path.exists(ADMIN_CONFIG_FILE):
        with open(ADMIN_CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("admin_password", "admin")
    return "admin"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PasswordChange(BaseModel):
    new_password: str


ADMIN_WEB_PATH = os.path.join(os.path.dirname(__file__), "static", "admin_web")


@app.get("/admin_web/{file_name:path}")
def get_admin_web(file_name: str, user: str = Depends(get_current_admin)):
    path = os.path.join(ADMIN_WEB_PATH, file_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    return FileResponse(path)


app.include_router(importer_router)
app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(admin_router)


@app.post("/admin/change_password")
async def change_password(data: PasswordChange):
    save_admin_config(data.new_password)
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"status": "online"}
