import base64
from collections import defaultdict

import cv2
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
from backend.helpers import contar_zona
from backend.semaforo import SemaforoAdaptativo
from ultralytics import YOLO


def init_model():
    model = YOLO(MODEL_PATH)
    return model


async def process_video(socketio, model):
    print("Cliente conectado")

    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or TARGET_FPS

    semaforo = SemaforoAdaptativo(fps)
    historial = defaultdict(list)

    delay = 1.0 / TARGET_FPS

    while True:
        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

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

                historial[tid].append((cx, cy))

                if len(historial[tid]) > 30:
                    historial[tid].pop(0)

                for i in range(1, len(historial[tid])):
                    cv2.line(frame, historial[tid][i - 1], historial[tid][i], color, 1)

        n_veh, n_peat = contar_zona(boxes, clases)
        estado = semaforo.tick(n_veh, n_peat)

        cv2.polylines(frame, [ZONA_VEHICULAR], True, (99, 200, 255), 2)
        cv2.polylines(frame, [ZONA_PEATONAL], True, (255, 99, 99), 2)

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

        if not ok:
            continue

        b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

        socketio.emit(
            "video_frame", {"frame": b64, "n_veh": n_veh, "n_peat": n_peat, **estado}
        )

        socketio.sleep(delay)
