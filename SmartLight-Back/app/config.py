import os
from pathlib import Path

import numpy as np
import torch

APP_DIR = Path(__file__).resolve().parent

MODEL_PATH = str(APP_DIR / "static" / "model" / "v100.pt")
VIDEO_PATH = str(APP_DIR / "static" / "video" / "example_video.mp4")

# Rutas configurables por variable de entorno: en Docker el filesystem del
# contenedor es efímero, así que en producción estas deben apuntar a un
# volumen montado (ver SmartLight-Back.Dockerfile / docker-compose).
DB_PATH = Path(os.getenv("DB_PATH", str(APP_DIR.parent / "smartlight.db")))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", str(APP_DIR.parent / "uploads")))

CONF = 0.25
# Usa GPU automáticamente si torch detecta CUDA disponible (driver NVIDIA +
# build de torch con soporte CUDA); si no, cae a CPU sin tocar este archivo.
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TARGET_FPS = 15

CLASES = ["person", "car", "bus", "truck", "van"]

COLORES = {
    0: (255, 99, 99),
    1: (99, 200, 255),
    2: (99, 255, 150),
    3: (255, 200, 99),
    4: (220, 99, 255),
}

ZONA_VEHICULAR = np.array(
    [
        [0, 200],
        [320, 200],
        [320, 450],
        [0, 450],
    ],
    dtype=np.int32,
)

ZONA_PEATONAL = np.array(
    [
        [0, 160],
        [360, 160],
        [360, 200],
        [0, 200],
    ],
    dtype=np.int32,
)

# Cada cuántos segundos se vuelve a consultar la cámara/zonas activas en la
# base de datos, para aplicar cambios del panel admin sin reiniciar el backend.
INTERVALO_RECARGA = 3

MAX_CAMARAS_POR_GRUPO = 4
