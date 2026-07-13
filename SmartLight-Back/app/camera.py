from collections import defaultdict

import cv2
import numpy as np

from app.config import TARGET_FPS, ZONA_PEATONAL, ZONA_VEHICULAR
from app.helpers import hex_a_bgr


class Camera:
    """Encapsula el ciclo de vida de una fuente de video (archivo o índice de
    dispositivo) más sus zonas/colores de detección. Una instancia por
    cámara activa en el sistema (cámara única o miembro de un corredor)."""

    def __init__(self, datos: dict):
        self.cap: cv2.VideoCapture | None = None
        self.fps = TARGET_FPS
        self.historial = defaultdict(list)
        self.actualizar(datos)

    def actualizar(self, datos: dict):
        self.id = datos["id"]
        self.nombre = datos["nombre"]

        nueva_fuente = datos["fuente"]
        fuente_cambio = getattr(self, "fuente", None) != nueva_fuente
        self.fuente = nueva_fuente

        self.zona_vehicular = (
            np.array(datos["zona_vehicular"], dtype=np.int32)
            if datos.get("zona_vehicular")
            else ZONA_VEHICULAR
        )
        self.zona_peatonal = (
            np.array(datos["zona_peatonal"], dtype=np.int32)
            if datos.get("zona_peatonal")
            else ZONA_PEATONAL
        )
        self.color_vehicular = hex_a_bgr(datos.get("color_vehicular", "#63c8ff"))
        self.color_peatonal = hex_a_bgr(datos.get("color_peatonal", "#ff6363"))

        self.grupo_id = datos.get("grupo_id")
        self.offset_segundos = datos.get("offset_segundos", 0)
        self.es_maestro = datos.get("es_maestro", True)

        if fuente_cambio or self.cap is None:
            self.abrir()

    def abrir(self):
        if self.cap is not None:
            self.cap.release()

        origen = int(self.fuente) if str(self.fuente).isdigit() else self.fuente
        self.cap = cv2.VideoCapture(origen)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or TARGET_FPS
        self.historial = defaultdict(list)

    def leer_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return None
        return frame

    def liberar(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def dibujar_zonas(self, frame):
        cv2.polylines(frame, [self.zona_vehicular], True, self.color_vehicular, 2)
        cv2.polylines(frame, [self.zona_peatonal], True, self.color_peatonal, 2)

    def registrar_trayectoria(self, tid, cx, cy):
        self.historial[tid].append((cx, cy))
        if len(self.historial[tid]) > 30:
            self.historial[tid].pop(0)
        return self.historial[tid]
