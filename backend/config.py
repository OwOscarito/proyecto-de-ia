import numpy as np

MODEL_PATH = "backend/static/model/best.pt"
VIDEO_PATH = "backend/static/video/cam1.mp4"

CONF = 0.25
DEVICE = "cpu"
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
