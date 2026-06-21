from fastapi import FastAPI
from fastapi_socketio import SocketManager
from semaphore import Semaphore
from video import process_video

app = FastAPI(
    title="",
    description="AI-powered prediction API",
    docs_url="/docs",
    redoc_url="/redoc",
)
sm = SocketManager(app=app, cors_allowed_origins="*")


semaphore = Semaphore(sm)


@sm.on("connect")
async def handle_connect(sid):
    print(f" Client connected: {sid}")
    sm.start_background_task(semaphore.get_frame_info())


@sm.on("disconnect")
async def handle_disconnect(sid):
    print(f" Client disconnected: {sid}")
