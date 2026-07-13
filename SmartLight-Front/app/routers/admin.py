import httpx
from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import api_client
from app.config import APP_DIR, BACKEND_PUBLIC_URL

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def _parse_float(valor: str | None):
    valor = (valor or "").strip()
    return float(valor) if valor else None


def _parse_int(valor: str | None):
    valor = (valor or "").strip()
    return int(valor) if valor else None


async def _archivo_o_none(video: UploadFile | None):
    if video is not None and video.filename:
        contenido = await video.read()
        return (video.filename, contenido, video.content_type)
    return None


@router.get("/", name="admin_lista")
async def lista(request: Request):
    camaras = await api_client.listar_camaras()
    return templates.TemplateResponse(
        request,
        "admin/lista.html",
        {"camaras": camaras, "activo": "camaras", "backend_url": BACKEND_PUBLIC_URL},
    )


@router.get("/camaras/nueva", name="admin_nueva_camara")
async def get_nueva_camara(request: Request):
    grupos = await api_client.listar_grupos()
    return templates.TemplateResponse(
        request,
        "admin/form.html",
        {"camara": None, "paso_nuevo": True, "grupos": grupos, "error": None},
    )


@router.post("/camaras/nueva", name="admin_crear_camara")
async def post_nueva_camara(
    request: Request,
    nombre: str = Form(...),
    fuente_tipo: str = Form("archivo"),
    video: UploadFile | None = None,
    device_index: str | None = Form(None),
    latitud: str = Form(""),
    longitud: str = Form(""),
    grupo_id: str = Form(""),
    offset_segundos: str = Form("0"),
    es_maestro: str | None = Form(None),
):
    archivo = await _archivo_o_none(video)

    try:
        camara = await api_client.crear_camara(
            nombre,
            fuente_tipo,
            archivo=archivo,
            device_index=device_index,
            latitud=_parse_float(latitud),
            longitud=_parse_float(longitud),
            grupo_id=_parse_int(grupo_id),
            offset_segundos=int(offset_segundos or 0),
            es_maestro=es_maestro == "on",
        )
    except httpx.HTTPStatusError as exc:
        grupos = await api_client.listar_grupos()
        return templates.TemplateResponse(
            request,
            "admin/form.html",
            {
                "camara": None,
                "paso_nuevo": True,
                "grupos": grupos,
                "error": exc.response.json().get("detail", "Error al crear la cámara."),
            },
        )

    return RedirectResponse(
        f"/admin/camaras/{camara['id']}/zonas?nuevo=1", status_code=303
    )


@router.get("/camaras/{camara_id}/editar", name="admin_editar_camara")
async def get_editar(request: Request, camara_id: int):
    camara = await api_client.obtener_camara(camara_id)
    if camara is None:
        return RedirectResponse("/admin/", status_code=303)

    grupos = await api_client.listar_grupos()
    return templates.TemplateResponse(
        request,
        "admin/form.html",
        {"camara": camara, "paso_nuevo": False, "grupos": grupos, "error": None},
    )


@router.post("/camaras/{camara_id}/editar", name="admin_guardar_camara")
async def post_editar(
    request: Request,
    camara_id: int,
    nombre: str = Form(...),
    fuente_tipo: str = Form("archivo"),
    video: UploadFile | None = None,
    device_index: str | None = Form(None),
    latitud: str = Form(""),
    longitud: str = Form(""),
    grupo_id: str = Form(""),
    offset_segundos: str = Form("0"),
    es_maestro: str | None = Form(None),
):
    archivo = await _archivo_o_none(video)

    try:
        await api_client.editar_camara(
            camara_id,
            nombre,
            fuente_tipo,
            archivo=archivo,
            device_index=device_index,
            latitud=_parse_float(latitud),
            longitud=_parse_float(longitud),
            grupo_id=_parse_int(grupo_id),
            offset_segundos=int(offset_segundos or 0),
            es_maestro=es_maestro == "on",
        )
    except httpx.HTTPStatusError as exc:
        camara = await api_client.obtener_camara(camara_id)
        grupos = await api_client.listar_grupos()
        return templates.TemplateResponse(
            request,
            "admin/form.html",
            {
                "camara": camara,
                "paso_nuevo": False,
                "grupos": grupos,
                "error": exc.response.json().get(
                    "detail", "Error al guardar la cámara."
                ),
            },
        )

    return RedirectResponse("/admin/", status_code=303)


@router.post("/camaras/{camara_id}/eliminar", name="admin_eliminar_camara")
async def post_eliminar(camara_id: int):
    await api_client.eliminar_camara(camara_id)
    return RedirectResponse("/admin/", status_code=303)


@router.post("/camaras/{camara_id}/activar", name="admin_activar_camara")
async def post_activar(camara_id: int):
    await api_client.activar_camara(camara_id)
    return RedirectResponse("/?activada=1", status_code=303)


@router.get("/camaras/{camara_id}/zonas", name="admin_zonas_camara")
async def get_zonas(request: Request, camara_id: int, nuevo: str | None = None):
    camara = await api_client.obtener_camara(camara_id)
    if camara is None:
        return RedirectResponse("/admin/", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/zonas.html",
        {
            "camara": camara,
            "paso_nuevo": nuevo == "1",
            "backend_url": BACKEND_PUBLIC_URL,
        },
    )


@router.post("/camaras/{camara_id}/zonas", name="admin_guardar_zona")
async def post_zonas(camara_id: int, payload: dict):
    await api_client.guardar_zona(
        camara_id, payload["tipo"], payload["puntos"], payload.get("color")
    )
    return {"ok": True}


@router.get("/mapa", name="admin_mapa")
async def mapa(request: Request):
    camaras = await api_client.listar_camaras()
    return templates.TemplateResponse(
        request, "admin/mapa.html", {"camaras": camaras, "activo": "mapa"}
    )


@router.get("/grupos", name="admin_grupos")
async def grupos(request: Request):
    lista_grupos = await api_client.listar_grupos()
    return templates.TemplateResponse(
        request,
        "admin/grupos.html",
        {"grupos": lista_grupos, "activo": "grupos"},
    )


@router.post("/grupos", name="admin_crear_grupo")
async def post_grupo(nombre: str = Form(...)):
    await api_client.crear_grupo(nombre)
    return RedirectResponse("/admin/grupos", status_code=303)


@router.get("/grupos/{grupo_id}", name="admin_grupo_detalle")
async def grupo_detalle(request: Request, grupo_id: int):
    grupo = await api_client.obtener_grupo(grupo_id)
    if grupo is None:
        return RedirectResponse("/admin/grupos", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/grupo_detalle.html",
        {"grupo": grupo, "activo": "grupos", "max_camaras": 4},
    )


@router.get("/grupos/{grupo_id}/corredor", name="admin_corredor")
async def corredor(request: Request, grupo_id: int):
    grupo = await api_client.obtener_grupo(grupo_id)
    if grupo is None:
        return RedirectResponse("/admin/grupos", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/corredor.html",
        {"grupo": grupo, "activo": "grupos", "backend_url": BACKEND_PUBLIC_URL},
    )
