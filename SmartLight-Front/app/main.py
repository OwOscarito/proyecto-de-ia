from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_DIR, FRONTEND_SUBPATH
from app.routers import admin, monitor

app = FastAPI(title="SmartLight Frontend", root_path=FRONTEND_SUBPATH)

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

app.include_router(monitor.router)
app.include_router(admin.router)
