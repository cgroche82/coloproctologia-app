"""
CRUD de intervenciones sobre la tabla única.

Sustituye a los cuatro routers por tipo (colorrectal, proctologia, funcionales,
general), que obligaban a tocar el código cada vez que hacía falta un tipo
nuevo. Ahora el tipo es un dato más y se filtra por `tipo_id`.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db, Registro, TipoCirugia
from schemas import RegistroCreate, RegistroOut
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/registros", tags=["registros"])


def _serializar(r: Registro, tipos: dict[int, TipoCirugia]) -> dict:
    d = RegistroOut.model_validate(r).model_dump()
    t = tipos.get(r.tipo_id)
    if t:
        d["tipo_slug"] = t.slug
        d["tipo_nombre"] = t.nombre
        d["tipo_color"] = t.color
    return d


def _mapa_tipos(db: Session) -> dict[int, TipoCirugia]:
    return {t.id: t for t in db.query(TipoCirugia).all()}


@router.get("/next-id")
def next_id(
    tipo_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """
    Siguiente identificador. Es orientativo: el definitivo lo asigna la base de
    datos al guardar, así que dos personas viéndolo a la vez no causan conflicto.
    """
    ultimo = db.query(Registro).order_by(Registro.id.desc()).first()
    return {"next_id": (ultimo.id + 1) if ultimo else 1}


@router.post("", response_model=dict)
def create(
    data: RegistroCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if not db.query(TipoCirugia).filter(TipoCirugia.id == data.tipo_id).first():
        raise HTTPException(404, "Tipo de cirugía no encontrado")
    registro = Registro(**data.model_dump(), created_by=user.username)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return _serializar(registro, _mapa_tipos(db))


# Columnas por las que se puede ordenar pinchando en la cabecera. Es una lista
# blanca a propósito: el nombre llega del navegador y no debe poder apuntar a
# cualquier campo. "tipo" ordena por el nombre del grupo, no por su id.
ORDENABLES = {
    "id": Registro.id,
    "fecha_intervencion": Registro.fecha_intervencion,
    "diagnostico": Registro.diagnostico,
    "intervencion": Registro.intervencion,
    "nhc": Registro.nhc,
    "cirujano": Registro.cirujano,
    "asa": Registro.asa,
    "tipo": TipoCirugia.nombre,
}


@router.get("", response_model=dict)
def list_all(
    page: int = 1,
    page_size: int = 20,
    orden: str = "fecha_intervencion",
    dir: str = "desc",
    tipo_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    diagnostico: Optional[str] = None,
    cirujano: Optional[str] = None,
    asa: Optional[str] = None,
    nhc: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Registro)
    if tipo_id:
        q = q.filter(Registro.tipo_id == tipo_id)
    if nhc:
        q = q.filter(Registro.nhc.ilike(f"%{nhc}%"))
    if fecha_desde:
        q = q.filter(Registro.fecha_intervencion >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Registro.fecha_intervencion <= fecha_hasta)
    if diagnostico:
        q = q.filter(Registro.diagnostico.ilike(f"%{diagnostico}%"))
    if cirujano:
        q = q.filter(Registro.cirujano == cirujano)
    if asa:
        q = q.filter(Registro.asa == asa)

    total = q.count()

    columna = ORDENABLES.get(orden, Registro.fecha_intervencion)
    if orden == "tipo":
        # Ordenar por el nombre del grupo exige traer la tabla de tipos
        q = q.join(TipoCirugia, Registro.tipo_id == TipoCirugia.id)
    criterio = columna.asc() if dir == "asc" else columna.desc()
    # Segundo criterio estable: sin él, las filas con el mismo valor bailan
    # entre páginas y algún registro puede repetirse o no salir nunca
    items = (q.order_by(criterio, Registro.id.desc())
              .offset((page - 1) * page_size).limit(page_size).all())
    tipos = _mapa_tipos(db)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serializar(i, tipos) for i in items],
    }


@router.get("/{id}", response_model=dict)
def get_one(
    id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    r = db.query(Registro).filter(Registro.id == id).first()
    if not r:
        raise HTTPException(404, "No encontrado")
    return _serializar(r, _mapa_tipos(db))


@router.put("/{id}", response_model=dict)
def update(
    id: int,
    data: RegistroCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    r = db.query(Registro).filter(Registro.id == id).first()
    if not r:
        raise HTTPException(404, "No encontrado")
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _serializar(r, _mapa_tipos(db))


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    r = db.query(Registro).filter(Registro.id == id).first()
    if not r:
        raise HTTPException(404, "No encontrado")
    db.delete(r)
    db.commit()
    return {"ok": True}
