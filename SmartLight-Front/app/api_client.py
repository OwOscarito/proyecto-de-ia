"""Cliente HTTP hacia SmartLight-Back. Mantiene las mismas firmas que el
`database.py` que usaba el frontend cuando compartía la BD directo con el
backend (antes de separarse en dos proyectos `uv`), para que el resto del
código del admin cambie lo mínimo posible."""

import httpx

from app.config import BACKEND_URL


def _client():
    return httpx.AsyncClient(base_url=BACKEND_URL, timeout=30)


async def listar_camaras():
    async with _client() as client:
        r = await client.get("/camaras")
        r.raise_for_status()
        return r.json()


async def obtener_camara(camara_id):
    async with _client() as client:
        r = await client.get(f"/camaras/{camara_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


def _form_camara(nombre, fuente_tipo, device_index, latitud, longitud, grupo_id, offset_segundos, es_maestro):
    data = {
        "nombre": nombre,
        "fuente_tipo": fuente_tipo,
        "offset_segundos": str(offset_segundos or 0),
        "es_maestro": "true" if es_maestro else "false",
    }
    if device_index is not None:
        data["device_index"] = device_index
    if latitud is not None:
        data["latitud"] = str(latitud)
    if longitud is not None:
        data["longitud"] = str(longitud)
    if grupo_id is not None:
        data["grupo_id"] = str(grupo_id)
    return data


async def crear_camara(
    nombre,
    fuente_tipo="archivo",
    archivo=None,
    device_index=None,
    latitud=None,
    longitud=None,
    grupo_id=None,
    offset_segundos=0,
    es_maestro=False,
):
    data = _form_camara(
        nombre, fuente_tipo, device_index, latitud, longitud, grupo_id, offset_segundos, es_maestro
    )
    files = {"video": (archivo[0], archivo[1], archivo[2])} if archivo else None

    async with _client() as client:
        r = await client.post("/camaras", data=data, files=files)
        r.raise_for_status()
        return r.json()


async def editar_camara(
    camara_id,
    nombre,
    fuente_tipo="archivo",
    archivo=None,
    device_index=None,
    latitud=None,
    longitud=None,
    grupo_id=None,
    offset_segundos=0,
    es_maestro=False,
):
    data = _form_camara(
        nombre, fuente_tipo, device_index, latitud, longitud, grupo_id, offset_segundos, es_maestro
    )
    files = {"video": (archivo[0], archivo[1], archivo[2])} if archivo else None

    async with _client() as client:
        r = await client.put(f"/camaras/{camara_id}", data=data, files=files)
        r.raise_for_status()
        return r.json()


async def eliminar_camara(camara_id):
    async with _client() as client:
        r = await client.delete(f"/camaras/{camara_id}")
        r.raise_for_status()


async def activar_camara(camara_id):
    async with _client() as client:
        r = await client.post(f"/camaras/{camara_id}/activar")
        r.raise_for_status()


async def guardar_zona(camara_id, tipo, puntos, color=None):
    async with _client() as client:
        r = await client.post(
            f"/camaras/{camara_id}/zonas",
            json={"tipo": tipo, "puntos": puntos, "color": color},
        )
        r.raise_for_status()


async def listar_grupos():
    async with _client() as client:
        r = await client.get("/grupos")
        r.raise_for_status()
        return r.json()


async def crear_grupo(nombre):
    async with _client() as client:
        r = await client.post("/grupos", json={"nombre": nombre})
        r.raise_for_status()
        return r.json()


async def obtener_grupo(grupo_id):
    async with _client() as client:
        r = await client.get(f"/grupos/{grupo_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
