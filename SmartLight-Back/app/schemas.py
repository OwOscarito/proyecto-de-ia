from pydantic import BaseModel


class CamaraOut(BaseModel):
    id: int
    nombre: str
    fuente: str
    fuente_tipo: str
    activa: bool
    latitud: float | None = None
    longitud: float | None = None
    grupo_id: int | None = None
    grupo_nombre: str | None = None
    offset_segundos: int = 0
    es_maestro: bool = False
    tiene_zona_vehicular: bool = False
    tiene_zona_peatonal: bool = False


class CamaraDetalleOut(BaseModel):
    id: int
    nombre: str
    fuente: str
    fuente_tipo: str
    activa: bool
    latitud: float | None = None
    longitud: float | None = None
    grupo_id: int | None = None
    offset_segundos: int = 0
    es_maestro: bool = False
    zona_vehicular: list[list[int]] | None = None
    zona_peatonal: list[list[int]] | None = None
    color_vehicular: str
    color_peatonal: str


class ZonaIn(BaseModel):
    tipo: str
    puntos: list[list[int]]
    color: str | None = None


class GrupoIn(BaseModel):
    nombre: str


class GrupoOut(BaseModel):
    id: int
    nombre: str
    n_camaras: int


class GrupoMiembro(BaseModel):
    id: int
    nombre: str
    offset_segundos: int
    es_maestro: bool
    activa: bool


class GrupoDetalleOut(BaseModel):
    id: int
    nombre: str
    camaras: list[GrupoMiembro]


class AsignarGrupoIn(BaseModel):
    grupo_id: int | None = None
    offset_segundos: int = 0
    es_maestro: bool = False


class OkOut(BaseModel):
    ok: bool = True
