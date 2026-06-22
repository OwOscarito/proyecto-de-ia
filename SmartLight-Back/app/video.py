import cv2
from ultralytics import YOLO

from app.camera import Camera
from app.config import CLASES, COLORES, CONF, DEVICE, MODEL_PATH
from app.helpers import contar_zona


def init_model() -> YOLO:
    return YOLO(MODEL_PATH)


def procesar_frame_sync(model: YOLO, model_lock, frame, camera: Camera):
    """Corre la inferencia YOLO + dibuja detecciones/zonas sobre un frame.

    Es síncrono y bloqueante a propósito: el caller (Semaphore) lo ejecuta
    dentro de `asyncio.to_thread(...)` para no congelar el event loop de
    FastAPI. `model_lock` serializa las llamadas a `model.track()` porque el
    modelo no es thread-safe (el "fusing" interno de capas Conv+BN se
    corrompe si se llama concurrentemente desde varias cámaras a la vez).
    """
    with model_lock:
        results = model.track(
            frame,
            conf=CONF,
            device=DEVICE,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
        )

    boxes = []
    clases = []

    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        tids = results[0].boxes.id.cpu().numpy().astype(int)
        clases = results[0].boxes.cls.cpu().numpy().astype(int)
        confs = results[0].boxes.conf.cpu().numpy()

        for box, tid, cid, conf in zip(boxes, tids, clases, confs):
            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            color = COLORES.get(cid, (200, 200, 200))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{CLASES[cid]} #{tid} {conf:.2f}",
                (x1, max(y1 - 6, 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
            )

            trayectoria = camera.registrar_trayectoria(tid, cx, cy)
            for i in range(1, len(trayectoria)):
                cv2.line(frame, trayectoria[i - 1], trayectoria[i], color, 1)

    n_veh, n_peat = contar_zona(boxes, clases, camera.zona_vehicular, camera.zona_peatonal)
    camera.dibujar_zonas(frame)

    return frame, n_veh, n_peat
