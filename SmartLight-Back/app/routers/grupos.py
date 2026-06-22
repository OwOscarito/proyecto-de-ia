from fastapi import APIRouter, HTTPException

from app.database import crear_grupo, listar_grupos, obtener_grupo
from app.schemas import GrupoDetalleOut, GrupoIn, GrupoOut

router = APIRouter(prefix="/grupos", tags=["grupos"])


@router.get("", response_model=list[GrupoOut])
def get_grupos():
    return listar_grupos()


@router.post("", response_model=GrupoOut)
def post_grupo(grupo: GrupoIn):
    grupo_id = crear_grupo(grupo.nombre)
    return next(g for g in listar_grupos() if g["id"] == grupo_id)


@router.get("/{grupo_id}", response_model=GrupoDetalleOut)
def get_grupo(grupo_id: int):
    grupo = obtener_grupo(grupo_id)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    return grupo
