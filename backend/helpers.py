import cv2

from backend.config import ZONA_PEATONAL, ZONA_VEHICULAR


def en_zona(cx, cy, zona):
    return cv2.pointPolygonTest(zona, (float(cx), float(cy)), False) >= 0


def contar_zona(boxes, clases):
    veh = 0

    for box, cid in zip(boxes, clases):
        cx = int((box[0] + box[2]) / 2)
        cy = int((box[1] + box[3]) / 2)

        if en_zona(cx, cy, ZONA_VEHICULAR):
            if cid in {1, 2, 3, 4}:
                veh += 1

    peat_cruce = sum(
        1
        for box, cid in zip(boxes, clases)
        if cid == 0
        and en_zona(
            int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2), ZONA_PEATONAL
        )
    )

    return veh, peat_cruce
