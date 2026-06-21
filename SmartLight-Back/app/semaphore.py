from fastapi_socketio import socket_manager

from backend.config import (
    CLASES,
    COLORES,
    CONF,
    DEVICE,
    MODEL_PATH,
    TARGET_FPS,
    VIDEO_PATH,
    ZONA_PEATONAL,
    ZONA_VEHICULAR,
)
from ultralytics import YOLO

class Camera:
  def __init__(self) -> None:
      self.model = YOLO
      self.zones =

  def add_zone(self) -> None:
      pass

class Semaphore:
    def __init__(self, sm) -> None:
        self.socket = sm
        self.task =

        self.model = YOLO
        self.cameras = []

        self.status = []

    async def process_frame() -> None:
      #
      pass

    async def get_process_frame() -> None:
      pass
