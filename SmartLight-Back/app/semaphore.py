import asyncio
import base64
import time
from enum import Enum
from threading import Lock

import cv2

from app.camera import Camera
from app.config import INTERVALO_RECARGA, TARGET_FPS
from app.database import get_camara_activa, obtener_camara, obtener_grupo
from app.video import init_model, procesar_frame_sync


class Fase(Enum):
    VERDE_VEHICULAR = "Verde vehicular"
    AMARILLO = "Amarillo"
    VERDE_PEATONAL = "Verde peatonal"
    TODO_ROJO = "Todo rojo"


class SemaforoAdaptativo:
    """Máquina de estados del ciclo del semáforo. Calcula la duración del
    verde según el promedio de detecciones de una ventana de 30 frames.

    Soporta sincronización tipo "ola verde": si `es_maestro=False`, retrasa
    su propio verde vehicular hasta `offset_segundos` después de que el
    maestro del grupo arrancó el suyo (consultado vía `obtener_estado_maestro`,
    inyectado por `Semaphore`). Si el maestro no tiene estado registrado
    (caído/no corriendo), no bloquea — sigue su ciclo normal."""

    def __init__(self, fps, es_maestro=True, offset_segundos=0, obtener_estado_maestro=None):
        self.fps = fps
        self.T_AMARILLO = 3
        self.T_TODO_ROJO = 2
        self.T_VEH_MIN = 10
        self.T_VEH_MAX = 60
        self.T_PEAT_MIN = 8
        self.T_PEAT_MAX = 40
        self.fase = Fase.VERDE_VEHICULAR
        self.tiempo_restante = self.T_VEH_MIN
        self.hist_veh = []
        self.hist_peat = []
        self.VENTANA = 30
        self.ultimo_inicio_verde = time.monotonic()

        self.es_maestro = es_maestro
        self.offset_segundos = offset_segundos
        self.obtener_estado_maestro = obtener_estado_maestro

    def _avg(self, lst):
        return sum(lst) / max(len(lst), 1)

    def _t_veh(self):
        return max(
            self.T_VEH_MIN,
            min(self.T_VEH_MIN + int(self._avg(self.hist_veh) * 4), self.T_VEH_MAX),
        )

    def _t_peat(self):
        return max(
            self.T_PEAT_MIN,
            min(self.T_PEAT_MIN + int(self._avg(self.hist_peat) * 3), self.T_PEAT_MAX),
        )

    def tick(self, n_veh, n_peat):
        self.hist_veh.append(n_veh)
        self.hist_peat.append(n_peat)

        if len(self.hist_veh) > self.VENTANA:
            self.hist_veh.pop(0)
            self.hist_peat.pop(0)

        self.tiempo_restante -= 1 / self.fps

        if self.tiempo_restante <= 0:
            self._siguiente()

        return {
            "fase": self.fase.value,
            "tiempo_restante": round(max(0, self.tiempo_restante), 1),
            "avg_veh": round(self._avg(self.hist_veh), 1),
            "avg_peat": round(self._avg(self.hist_peat), 1),
            "t_veh_calc": self._t_veh(),
            "t_peat_calc": self._t_peat(),
        }

    def _esperando_sincronizacion(self):
        if self.es_maestro or self.obtener_estado_maestro is None:
            return False

        estado_maestro = self.obtener_estado_maestro()
        if not estado_maestro:
            return False

        objetivo = estado_maestro["ultimo_inicio_verde"] + self.offset_segundos
        ahora = time.monotonic()

        if ahora < objetivo:
            self.tiempo_restante = objetivo - ahora
            return True

        return False

    def _siguiente(self):
        if self.fase == Fase.VERDE_VEHICULAR:
            self.fase = Fase.AMARILLO
            self.tiempo_restante = self.T_AMARILLO

        elif self.fase == Fase.AMARILLO:
            self.fase = Fase.TODO_ROJO
            self.tiempo_restante = self.T_TODO_ROJO

        elif self.fase == Fase.TODO_ROJO:
            if self._avg(self.hist_peat) > 1:
                self.fase = Fase.VERDE_PEATONAL
                self.tiempo_restante = self._t_peat()
            elif self._esperando_sincronizacion():
                return
            else:
                self.fase = Fase.VERDE_VEHICULAR
                self.tiempo_restante = self._t_veh()
                self.ultimo_inicio_verde = time.monotonic()

        elif self.fase == Fase.VERDE_PEATONAL:
            self.fase = Fase.TODO_ROJO
            self.tiempo_restante = self.T_TODO_ROJO


class Semaphore:
    """Orquesta el procesamiento de todas las cámaras activas: posee el
    modelo YOLO (una sola instancia compartida), las instancias `Camera` y
    `SemaforoAdaptativo` por cámara, el estado de sincronización entre
    cámaras de un mismo grupo (lo que antes era `coordinador.py`) y las
    tareas async en background, una por cámara."""

    def __init__(self, sm):
        self.socket = sm
        self.model = init_model()
        self._model_lock = Lock()

        self.cameras: dict[int, Camera] = {}
        self.relojes: dict[int, SemaforoAdaptativo] = {}
        self.tasks: dict[int, asyncio.Task] = {}

        self.status: dict[int, dict] = {}
        self._status_lock = Lock()

    # --- estado compartido para la sincronización "ola verde" ---

    def actualizar_estado(self, camara_id, fase, tiempo_restante, ultimo_inicio_verde):
        with self._status_lock:
            self.status[camara_id] = {
                "fase": fase,
                "tiempo_restante": tiempo_restante,
                "ultimo_inicio_verde": ultimo_inicio_verde,
            }

    def obtener_estado(self, camara_id):
        with self._status_lock:
            return self.status.get(camara_id)

    def _maestro_del_grupo(self, grupo_id, camara_id_propia):
        grupo = obtener_grupo(grupo_id)
        if not grupo:
            return None
        for c in grupo["camaras"]:
            if c["es_maestro"] and c["id"] != camara_id_propia:
                return c["id"]
        return None

    def _crear_reloj(self, fps, datos: dict):
        if datos.get("grupo_id") is None or datos.get("es_maestro", True):
            return SemaforoAdaptativo(fps, es_maestro=True)

        maestro_id = self._maestro_del_grupo(datos["grupo_id"], datos["id"])
        if maestro_id is None:
            return SemaforoAdaptativo(fps, es_maestro=True)

        return SemaforoAdaptativo(
            fps,
            es_maestro=False,
            offset_segundos=datos["offset_segundos"],
            obtener_estado_maestro=lambda: self.obtener_estado(maestro_id),
        )

    @staticmethod
    def _cargar_datos_camara(camara_id=None):
        return obtener_camara(camara_id) if camara_id is not None else get_camara_activa()

    # --- ciclo de vida de las tareas de procesamiento ---

    async def asegurar_task(self, camara_id=None):
        if camara_id in self.tasks and not self.tasks[camara_id].done():
            return
        self.tasks[camara_id] = asyncio.create_task(self._loop(camara_id))

    async def _loop(self, camara_id):
        datos = self._cargar_datos_camara(camara_id)
        if datos is None:
            return

        camara_id_real = datos["id"]

        camera = Camera(datos)
        self.cameras[camara_id_real] = camera
        self.relojes[camara_id_real] = self._crear_reloj(camera.fps, datos)

        delay = 1.0 / TARGET_FPS
        ultima_recarga = time.monotonic()

        try:
            while True:
                ahora = time.monotonic()

                if ahora - ultima_recarga >= INTERVALO_RECARGA:
                    ultima_recarga = ahora
                    nuevos_datos = self._cargar_datos_camara(camara_id)
                    if nuevos_datos:
                        fuente_cambio = nuevos_datos["fuente"] != camera.fuente
                        camera.actualizar(nuevos_datos)
                        if fuente_cambio:
                            self.relojes[camara_id_real] = self._crear_reloj(
                                camera.fps, nuevos_datos
                            )

                frame = await asyncio.to_thread(camera.leer_frame)
                if frame is None:
                    continue

                frame, n_veh, n_peat = await asyncio.to_thread(
                    procesar_frame_sync, self.model, self._model_lock, frame, camera
                )

                reloj = self.relojes[camara_id_real]
                estado = reloj.tick(n_veh, n_peat)

                self.actualizar_estado(
                    camara_id_real, estado["fase"], estado["tiempo_restante"], reloj.ultimo_inicio_verde
                )

                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ok:
                    continue

                b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

                await self.socket.emit(
                    "video_frame",
                    {
                        "frame": b64,
                        "n_veh": n_veh,
                        "n_peat": n_peat,
                        "camara_id": camara_id_real,
                        **estado,
                    },
                )

                await asyncio.sleep(delay)
        finally:
            camera.liberar()
