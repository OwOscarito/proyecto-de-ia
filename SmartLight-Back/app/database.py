from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

from app.config import DB_PATH, UPLOADS_DIR, VIDEO_PATH, ZONA_PEATONAL, ZONA_VEHICULAR

ZONA_VEHICULAR_SEED = ZONA_VEHICULAR.tolist()
ZONA_PEATONAL_SEED = ZONA_PEATONAL.tolist()

COLOR_DEFAULT = {"vehicular": "#63c8ff", "peatonal": "#ff6363"}
MAX_CAMARAS_POR_GRUPO = 4

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Camara(Base):
    __tablename__ = "camaras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    fuente: Mapped[str] = mapped_column(String(500))
    fuente_tipo: Mapped[str] = mapped_column(String(20), default="archivo")
    activa: Mapped[bool] = mapped_column(Boolean, default=False)
    latitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    grupo_id: Mapped[int | None] = mapped_column(
        ForeignKey("grupos.id"), nullable=True
    )
    offset_segundos: Mapped[int] = mapped_column(Integer, default=0)
    es_maestro: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    zonas: Mapped[list["Zona"]] = relationship(
        back_populates="camara", cascade="all, delete-orphan"
    )
    grupo: Mapped["Grupo | None"] = relationship(back_populates="camaras")

    def zona(self, tipo):
        for z in self.zonas:
            if z.tipo == tipo:
                return z.puntos
        return None

    def color(self, tipo):
        for z in self.zonas:
            if z.tipo == tipo:
                return z.color
        return COLOR_DEFAULT[tipo]


class Grupo(Base):
    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))

    camaras: Mapped[list["Camara"]] = relationship(back_populates="grupo")


class Zona(Base):
    __tablename__ = "zonas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camara_id: Mapped[int] = mapped_column(ForeignKey("camaras.id"))
    tipo: Mapped[str] = mapped_column(String(20))
    puntos: Mapped[list] = mapped_column(JSON)
    color: Mapped[str] = mapped_column(String(7), default="#63c8ff")

    camara: Mapped["Camara"] = relationship(back_populates="zonas")


def init_db():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        if session.query(Camara).count() == 0:
            seed = Camara(
                nombre="Cámara 1",
                fuente=VIDEO_PATH,
                fuente_tipo="archivo",
                activa=True,
            )
            seed.zonas.append(
                Zona(
                    tipo="vehicular",
                    puntos=ZONA_VEHICULAR_SEED,
                    color=COLOR_DEFAULT["vehicular"],
                )
            )
            seed.zonas.append(
                Zona(
                    tipo="peatonal",
                    puntos=ZONA_PEATONAL_SEED,
                    color=COLOR_DEFAULT["peatonal"],
                )
            )
            session.add(seed)
            session.commit()


def _camara_a_dict(camara: Camara, detalle=False):
    base = {
        "id": camara.id,
        "nombre": camara.nombre,
        "fuente": camara.fuente,
        "fuente_tipo": camara.fuente_tipo,
        "activa": camara.activa,
        "latitud": camara.latitud,
        "longitud": camara.longitud,
        "grupo_id": camara.grupo_id,
        "offset_segundos": camara.offset_segundos,
        "es_maestro": camara.es_maestro,
    }
    if detalle:
        base["zona_vehicular"] = camara.zona("vehicular")
        base["zona_peatonal"] = camara.zona("peatonal")
        base["color_vehicular"] = camara.color("vehicular")
        base["color_peatonal"] = camara.color("peatonal")
    else:
        base["grupo_nombre"] = camara.grupo.nombre if camara.grupo else None
        base["tiene_zona_vehicular"] = camara.zona("vehicular") is not None
        base["tiene_zona_peatonal"] = camara.zona("peatonal") is not None
    return base


def get_camara_activa():
    with SessionLocal() as session:
        camara = session.query(Camara).filter_by(activa=True).first()
        if camara is None:
            return None
        return _camara_a_dict(camara, detalle=True)


def listar_camaras():
    with SessionLocal() as session:
        camaras = session.query(Camara).order_by(Camara.id).all()
        return [_camara_a_dict(c) for c in camaras]


def obtener_camara(camara_id):
    with SessionLocal() as session:
        camara = session.get(Camara, camara_id)
        if camara is None:
            return None
        return _camara_a_dict(camara, detalle=True)


def crear_camara(nombre, fuente, fuente_tipo="archivo", latitud=None, longitud=None):
    with SessionLocal() as session:
        camara = Camara(
            nombre=nombre,
            fuente=fuente,
            fuente_tipo=fuente_tipo,
            latitud=latitud,
            longitud=longitud,
        )
        session.add(camara)
        session.commit()
        return camara.id


def editar_camara(
    camara_id, nombre, fuente, fuente_tipo="archivo", latitud=None, longitud=None
):
    with SessionLocal() as session:
        camara = session.get(Camara, camara_id)
        if camara is None:
            return
        camara.nombre = nombre
        camara.fuente = fuente
        camara.fuente_tipo = fuente_tipo
        camara.latitud = latitud
        camara.longitud = longitud
        session.commit()


def eliminar_camara(camara_id):
    with SessionLocal() as session:
        camara = session.get(Camara, camara_id)
        if camara is None:
            return
        session.delete(camara)
        session.commit()


def activar_camara(camara_id):
    with SessionLocal() as session:
        session.query(Camara).update({Camara.activa: False})
        camara = session.get(Camara, camara_id)
        if camara is not None:
            camara.activa = True
        session.commit()


def guardar_zona(camara_id, tipo, puntos, color=None):
    with SessionLocal() as session:
        zona = session.query(Zona).filter_by(camara_id=camara_id, tipo=tipo).first()
        if zona is None:
            zona = Zona(
                camara_id=camara_id,
                tipo=tipo,
                puntos=puntos,
                color=color or COLOR_DEFAULT[tipo],
            )
            session.add(zona)
        else:
            zona.puntos = puntos
            if color:
                zona.color = color
        session.commit()


def crear_grupo(nombre):
    with SessionLocal() as session:
        grupo = Grupo(nombre=nombre)
        session.add(grupo)
        session.commit()
        return grupo.id


def listar_grupos():
    with SessionLocal() as session:
        grupos = session.query(Grupo).order_by(Grupo.id).all()
        return [
            {"id": g.id, "nombre": g.nombre, "n_camaras": len(g.camaras)}
            for g in grupos
        ]


def obtener_grupo(grupo_id):
    with SessionLocal() as session:
        grupo = session.get(Grupo, grupo_id)
        if grupo is None:
            return None
        return {
            "id": grupo.id,
            "nombre": grupo.nombre,
            "camaras": [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "offset_segundos": c.offset_segundos,
                    "es_maestro": c.es_maestro,
                    "activa": c.activa,
                }
                for c in sorted(grupo.camaras, key=lambda c: c.id)
            ],
        }


def contar_camaras_en_grupo(grupo_id):
    with SessionLocal() as session:
        return session.query(Camara).filter_by(grupo_id=grupo_id).count()


def asignar_grupo(camara_id, grupo_id, offset_segundos=0, es_maestro=False):
    with SessionLocal() as session:
        if grupo_id is not None and es_maestro:
            session.query(Camara).filter_by(grupo_id=grupo_id).update(
                {Camara.es_maestro: False}
            )

        camara = session.get(Camara, camara_id)
        if camara is None:
            return
        camara.grupo_id = grupo_id
        camara.offset_segundos = offset_segundos if grupo_id else 0
        camara.es_maestro = es_maestro if grupo_id else False
        session.commit()


def quitar_de_grupo(camara_id):
    with SessionLocal() as session:
        camara = session.get(Camara, camara_id)
        if camara is None:
            return
        camara.grupo_id = None
        camara.offset_segundos = 0
        camara.es_maestro = False
        session.commit()
