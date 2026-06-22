import cv2


def hex_a_bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (b, g, r)


def en_zona(cx, cy, zona):
    return cv2.pointPolygonTest(zona, (float(cx), float(cy)), False) >= 0


def contar_zona(boxes, clases, zona_vehicular, zona_peatonal):
    veh = 0

    for box, cid in zip(boxes, clases):
        cx = int((box[0] + box[2]) / 2)
        cy = int((box[1] + box[3]) / 2)

        if en_zona(cx, cy, zona_vehicular):
            if cid in {1, 2, 3, 4}:
                veh += 1

    peat_cruce = sum(
        1
        for box, cid in zip(boxes, clases)
        if cid == 0
        and en_zona(
            int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2), zona_peatonal
        )
    )

    return veh, peat_cruce
