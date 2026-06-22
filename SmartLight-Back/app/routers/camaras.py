import re
import uuid

import cv2
from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import MAX_CAMARAS_POR_GRUPO, UPLOADS_DIR
from app.database import (
    activar_camara,
    asignar_grupo,
    contar_camaras_en_grupo,
    crear_camara,
    editar_camara,
    eliminar_camara,
    guardar_zona,
    listar_camaras,
    obtener_camara,
    quitar_de_grupo,
)
from app.schemas import CamaraDetalleOut, CamaraOut, OkOut, ZonaIn

router = APIRouter(prefix="/camaras", tags=["camaras"])


def _nombre_seguro(nombre: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", nombre)


async def _resolver_fuente(fuente_tipo: str, video: UploadFile | None, device_index: str | None):
    if fuente_tipo == "webcam":
        return (device_index or "0").strip() or "0", "webcam"

    if video is not None and video.filename:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        nombre_unico = f"{uuid.uuid4().hex}_{_nombre_seguro(video.filename)}"
        ruta = UPLOADS_DIR / nombre_unico
        contenido = await video.read()
        ruta.write_bytes(contenido)
        return str(ruta), "archivo"

    return None, "archivo"


def _aplicar_grupo(camara_id, grupo_id, offset_segundos, es_maestro):
    if grupo_id is None:
        quitar_de_grupo(camara_id)
        return

    camara_actual = obtener_camara(camara_id)
    ya_en_grupo = camara_actual and camara_actual["grupo_id"] == grupo_id

    if not ya_en_grupo and contar_camaras_en_grupo(grupo_id) >= MAX_CAMARAS_POR_GRUPO:
        raise HTTPException(
            status_code=409,
            detail=f"Ese grupo ya tiene el máximo de {MAX_CAMARAS_POR_GRUPO} cámaras.",
        )

    asignar_grupo(camara_id, grupo_id, offset_segundos, es_maestro)


@router.get("", response_model=list[CamaraOut])
def get_camaras():
    return listar_camaras()


@router.post("", response_model=CamaraDetalleOut)
async def post_camara(
    nombre: str = Form(...),
    fuente_tipo: str = Form("archivo"),
    video: UploadFile | None = None,
    device_index: str | None = Form(None),
    latitud: float | None = Form(None),
    longitud: float | None = Form(None),
    grupo_id: int | None = Form(None),
    offset_segundos: int = Form(0),
    es_maestro: bool = Form(False),
):
    fuente, fuente_tipo_real = await _resolver_fuente(fuente_tipo, video, device_index)
    if fuente is None:
        raise HTTPException(status_code=400, detail="Falta el video o el índice de cámara.")

    camara_id = crear_camara(nombre, fuente, fuente_tipo_real, latitud, longitud)
    _aplicar_grupo(camara_id, grupo_id, offset_segundos, es_maestro)

    camara = obtener_camara(camara_id)
    return camara


@router.get("/{camara_id}", response_model=CamaraDetalleOut)
def get_camara(camara_id: int):
    camara = obtener_camara(camara_id)
    if camara is None:
        raise HTTPException(status_code=404, detail="Cámara no encontrada.")
    return camara


@router.put("/{camara_id}", response_model=CamaraDetalleOut)
async def put_camara(
    camara_id: int,
    nombre: str = Form(...),
    fuente_tipo: str = Form("archivo"),
    video: UploadFile | None = None,
    device_index: str | None = Form(None),
    latitud: float | None = Form(None),
    longitud: float | None = Form(None),
    grupo_id: int | None = Form(None),
    offset_segundos: int = Form(0),
    es_maestro: bool = Form(False),
):
    existente = obtener_camara(camara_id)
    if existente is None:
        raise HTTPException(status_code=404, detail="Cámara no encontrada.")

    fuente, fuente_tipo_real = await _resolver_fuente(fuente_tipo, video, device_index)
    if fuente is None:
        fuente, fuente_tipo_real = existente["fuente"], existente["fuente_tipo"]

    editar_camara(camara_id, nombre, fuente, fuente_tipo_real, latitud, longitud)
    _aplicar_grupo(camara_id, grupo_id, offset_segundos, es_maestro)

    return obtener_camara(camara_id)


@router.delete("/{camara_id}", response_model=OkOut)
def delete_camara(camara_id: int):
    eliminar_camara(camara_id)
    return OkOut()


@router.post("/{camara_id}/activar", response_model=OkOut)
def post_activar(camara_id: int):
    activar_camara(camara_id)
    return OkOut()


@router.post("/{camara_id}/zonas", response_model=OkOut)
def post_zona(camara_id: int, zona: ZonaIn):
    guardar_zona(camara_id, zona.tipo, zona.puntos, zona.color)
    return OkOut()


@router.get("/{camara_id}/frame.jpg")
def get_frame(camara_id: int):
    camara = obtener_camara(camara_id)
    if camara is None:
        raise HTTPException(status_code=404, detail="Cámara no encontrada.")

    fuente = camara["fuente"]
    origen = int(fuente) if str(fuente).isdigit() else fuente

    cap = cv2.VideoCapture(origen)
    ok, frame = cap.read()
    cap.release()

    if not ok:
        raise HTTPException(status_code=404, detail="No se pudo capturar un frame.")

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo codificar el frame.")

    return Response(content=buf.tobytes(), media_type="image/jpeg")
