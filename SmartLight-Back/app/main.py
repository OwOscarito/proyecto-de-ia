import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import APP_DIR
from app.database import init_db
from app.routers import camaras, grupos
from app.semaphore import Semaphore

app = FastAPI(
    title="SmartLight Backend",
    description="AI-powered traffic light prediction API",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

app.include_router(camaras.router)
app.include_router(grupos.router)

# Se usa python-socketio directo (no el wrapper fastapi-socketio): la versión
# de Starlette instalada cambió cómo un Mount recorta el path de la request
# (ya no muta scope["path"], hay que leerlo vía get_route_path), y el wrapper
# fastapi-socketio sigue asumiendo el comportamiento viejo — con él, cualquier
# conexión de socket.io devolvía 404 sin importar el path configurado. Con
# `other_asgi_app`, socket.io queda como la app ASGI de más afuera y reenvía
# lo que no es suyo a FastAPI tal cual, sin pasar por el mecanismo de Mount.
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

semaforo = Semaphore(sio)


@app.on_event("startup")
def on_startup():
    init_db()


@sio.event
async def connect(sid, environ):
    print(f"Cliente conectado: {sid}")
    await semaforo.asegurar_task(None)


@sio.event
async def ver_camara(sid, data):
    camara_id = data.get("camara_id")
    if camara_id is not None:
        await semaforo.asegurar_task(camara_id)


@sio.event
async def disconnect(sid):
    print(f"Cliente desconectado: {sid}")
