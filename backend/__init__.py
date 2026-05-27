from threading import Lock

from flask import Flask
from flask_socketio import SocketIO

from .video_procesor import procesar_video

video_task = None
video_task_lock = Lock()


def create_app(base_path, secret_key="dev"):
    static_path = base_path / "static"
    print(static_path)
    app = Flask(
        __name__,
        static_folder=static_path,
    )
    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    @socketio.on("connect")
    def handle_connect():
        print("Cliente conectado")
        global video_task
        with video_task_lock:
            if video_task is None:
                video_task = socketio.start_background_task(procesar_video, socketio)

    @socketio.on("disconnect")
    def handle_disconnect():
        print("Cliente desconectado")

    return app, socketio
