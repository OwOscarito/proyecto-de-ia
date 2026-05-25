import cv2
import base64
import asyncio
import numpy as np
from pathlib import Path
from collections import defaultdict
from enum import Enum

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ultralytics import YOLO

# ── Configuración ──────────────────────────────────────────────
MODEL_PATH  = "best.pt"
VIDEO_PATH  = "cam1.mp4"
CONF        = 0.25
#DEVICE      = 0 # con GPU
DEVICE = "cpu" #localhost
# TARGET_FPS  = 20 # con GPU
TARGET_FPS = 15 # localhost

CLASES  = ["person", "car", "bus", "truck", "van"]
COLORES = {
    0: (255, 99,  99),
    1: (99,  200, 255),
    2: (99,  255, 150),
    3: (255, 200, 99),
    4: (220, 99,  255),
}

ZONA_VEHICULAR = np.array([
    [0,   200],
    [320, 200],
    [320, 450],
    [0,   450],
], dtype=np.int32)

ZONA_PEATONAL = np.array([
    [0,  160],
    [360, 160],
    [360, 200],
    [0,  200],
], dtype=np.int32)

# ── Semáforo ───────────────────────────────────────────────────
class Fase(Enum):
    VERDE_VEHICULAR = "Verde vehicular"
    AMARILLO        = "Amarillo"
    VERDE_PEATONAL  = "Verde peatonal"
    TODO_ROJO       = "Todo rojo"

class SemaforoAdaptativo:
    def __init__(self, fps):
        self.fps              = fps
        self.T_AMARILLO       = 3
        self.T_TODO_ROJO      = 2
        self.T_VEH_MIN        = 10
        self.T_VEH_MAX        = 60
        self.T_PEAT_MIN       = 8
        self.T_PEAT_MAX       = 40
        self.fase             = Fase.VERDE_VEHICULAR
        self.tiempo_restante  = self.T_VEH_MIN
        self.hist_veh         = []
        self.hist_peat        = []
        self.VENTANA          = 30

    def _avg(self, lst):
        return sum(lst) / max(len(lst), 1)

    def _t_veh(self):
        return max(self.T_VEH_MIN, min(self.T_VEH_MIN + int(self._avg(self.hist_veh) * 4), self.T_VEH_MAX))

    def _t_peat(self):
        return max(self.T_PEAT_MIN, min(self.T_PEAT_MIN + int(self._avg(self.hist_peat) * 3), self.T_PEAT_MAX))

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
            "fase":            self.fase.value,
            "tiempo_restante": round(max(0, self.tiempo_restante), 1),
            "avg_veh":         round(self._avg(self.hist_veh), 1),
            "avg_peat":        round(self._avg(self.hist_peat), 1),
            "t_veh_calc":      self._t_veh(),
            "t_peat_calc":     self._t_peat(),
        }

    def _siguiente(self):
        if self.fase == Fase.VERDE_VEHICULAR:
            self.fase, self.tiempo_restante = Fase.AMARILLO, self.T_AMARILLO
        elif self.fase == Fase.AMARILLO:
            self.fase, self.tiempo_restante = Fase.TODO_ROJO, self.T_TODO_ROJO
        elif self.fase == Fase.TODO_ROJO:
            if self._avg(self.hist_peat) > 1:
                self.fase, self.tiempo_restante = Fase.VERDE_PEATONAL, self._t_peat()
            else:
                self.fase, self.tiempo_restante = Fase.VERDE_VEHICULAR, self._t_veh()
        elif self.fase == Fase.VERDE_PEATONAL:
            self.fase, self.tiempo_restante = Fase.TODO_ROJO, self.T_TODO_ROJO

# ── Helpers ────────────────────────────────────────────────────
def en_zona(cx, cy, zona):
    return cv2.pointPolygonTest(zona, (float(cx), float(cy)), False) >= 0

def contar_zona(boxes, clases):
    veh, peat = 0, 0
    for box, cid in zip(boxes, clases):
        cx, cy = int((box[0]+box[2])/2), int((box[1]+box[3])/2)
        if en_zona(cx, cy, ZONA_VEHICULAR):
            if cid in {1,2,3,4}: veh += 1
            elif cid == 0: peat += 1
    peat_cruce = sum(
        1 for box, cid in zip(boxes, clases)
        if cid == 0 and en_zona(int((box[0]+box[2])/2), int((box[1]+box[3])/2), ZONA_PEATONAL)
    )
    return veh, peat_cruce

# ── FastAPI app ────────────────────────────────────────────────
app   = FastAPI()
model = YOLO(MODEL_PATH)
# model.to(f"cuda:{DEVICE}") # quitar para localhost


@app.get("/")
async def index():
    html = Path("index.html").read_text()
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Cliente conectado ✓")

    cap       = cv2.VideoCapture(VIDEO_PATH)
    fps       = int(cap.get(cv2.CAP_PROP_FPS)) or TARGET_FPS
    semaforo  = SemaforoAdaptativo(fps)
    historial = defaultdict(list)
    delay     = 1.0 / TARGET_FPS

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop del video
                continue

            # Inferencia + tracking
            results = model.track(
                frame, conf=CONF, device=DEVICE,
                tracker="bytetrack.yaml", persist=True, verbose=False
            )
            print(results)
            boxes, tids, clases = [], [], []
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes  = results[0].boxes.xyxy.cpu().numpy()
                tids   = results[0].boxes.id.cpu().numpy().astype(int)
                clases = results[0].boxes.cls.cpu().numpy().astype(int)
                confs  = results[0].boxes.conf.cpu().numpy()

                for box, tid, cid, conf in zip(boxes, tids, clases, confs):
                    x1,y1,x2,y2 = map(int, box)
                    cx,cy = (x1+x2)//2, (y1+y2)//2
                    color = COLORES.get(cid, (200,200,200))
                    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(frame, f"{CLASES[cid]} #{tid} {conf:.2f}",
                                (x1, max(y1-6,10)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
                    historial[tid].append((cx,cy))
                    if len(historial[tid]) > 30: historial[tid].pop(0)
                    for i in range(1, len(historial[tid])):
                        cv2.line(frame, historial[tid][i-1], historial[tid][i], color, 1)

            # Conteo y semáforo
            n_veh, n_peat = contar_zona(boxes, clases)
            estado = semaforo.tick(n_veh, n_peat)

            # Dibujar zonas
            cv2.polylines(frame, [ZONA_VEHICULAR], True, (99,200,255), 2)
            cv2.polylines(frame, [ZONA_PEATONAL],  True, (255,99,99),  2)

            # Codificar frame a JPEG base64
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64 = base64.b64encode(buf).decode()

            # Enviar frame + datos al browser
            await ws.send_json({
                "frame":   b64,
                "n_veh":   n_veh,
                "n_peat":  n_peat,
                **estado
            })

            await asyncio.sleep(delay)

    except WebSocketDisconnect:
        print("Cliente desconectado")
    finally:
        cap.release()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)