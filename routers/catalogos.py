"""
CRUD de los catálogos editables desde Ajustes.

Lectura: cualquier usuario autenticado (los desplegables del formulario).
Escritura: sólo administradores.

Nunca se borra físicamente nada que pueda estar en uso: se desactiva. Los
registros guardan estos valores como texto, así que desactivar un diagnóstico
lo retira de los desplegables sin tocar los casos ya grabados.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, TipoCirugia, Diagnostico, Intervencion, Cirujano
from auth import get_current_user, get_admin_user, Usuario

router = APIRouter(prefix="/api/catalogos", tags=["catalogos"])


# ── Esquemas ─────────────────────────────────────────────────────────────────
class TipoIn(BaseModel):
    nombre: str
    color: Optional[str] = "#1565C0"
    tiene_oncologico: bool = False


class DiagnosticoIn(BaseModel):
    nombre: str
    tipo_id: int
    es_oncologico: bool = False


class IntervencionIn(BaseModel):
    nombre: str
    diagnostico_id: int


class CirujanoIn(BaseModel):
    nombre: str


class RenombrarIn(BaseModel):
    nombre: str


# ── Árbol completo (lo que consume el formulario) ────────────────────────────
@router.get("/arbol")
def arbol(
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Tipos → diagnósticos → intervenciones, en un solo viaje."""
    q_tipos = db.query(TipoCirugia)
    if not incluir_inactivos:
        q_tipos = q_tipos.filter(TipoCirugia.activo == True)
    tipos = q_tipos.order_by(TipoCirugia.orden, TipoCirugia.id).all()

    q_diag = db.query(Diagnostico)
    q_int = db.query(Intervencion)
    if not incluir_inactivos:
        q_diag = q_diag.filter(Diagnostico.activo == True)
        q_int = q_int.filter(Intervencion.activo == True)
    diags = q_diag.order_by(Diagnostico.orden, Diagnostico.id).all()
    intervs = q_int.order_by(Intervencion.orden, Intervencion.id).all()

    por_diag: dict[int, list] = {}
    for i in intervs:
        por_diag.setdefault(i.diagnostico_id, []).append(
            {"id": i.id, "nombre": i.nombre, "activo": i.activo}
        )

    por_tipo: dict[int, list] = {}
    for d in diags:
        por_tipo.setdefault(d.tipo_id, []).append({
            "id": d.id,
            "nombre": d.nombre,
            "activo": d.activo,
            "es_oncologico": d.es_oncologico,
            "intervenciones": por_diag.get(d.id, []),
        })

    return [
        {
            "id": t.id,
            "slug": t.slug,
            "nombre": t.nombre,
            "color": t.color,
            "tiene_oncologico": t.tiene_oncologico,
            "activo": t.activo,
            "diagnosticos": por_tipo.get(t.id, []),
        }
        for t in tipos
    ]


# ── Cirujanos ────────────────────────────────────────────────────────────────
@router.get("/cirujanos")
def listar_cirujanos(
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Cirujano)
    if not incluir_inactivos:
        q = q.filter(Cirujano.activo == True)
    return [
        {"id": c.id, "nombre": c.nombre, "activo": c.activo}
        for c in q.order_by(Cirujano.orden, Cirujano.nombre).all()
    ]


@router.post("/cirujanos")
def crear_cirujano(
    data: CirujanoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    if db.query(Cirujano).filter(Cirujano.nombre == nombre).first():
        raise HTTPException(400, "Ese cirujano ya existe")
    ultimo = db.query(Cirujano).order_by(Cirujano.orden.desc()).first()
    c = Cirujano(nombre=nombre, orden=(ultimo.orden + 1) if ultimo else 0)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "nombre": c.nombre, "activo": c.activo}


@router.patch("/cirujanos/{cid}")
def renombrar_cirujano(
    cid: int,
    data: RenombrarIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    c = db.query(Cirujano).filter(Cirujano.id == cid).first()
    if not c:
        raise HTTPException(404, "No encontrado")
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    c.nombre = nombre
    db.commit()
    return {"id": c.id, "nombre": c.nombre, "activo": c.activo}


@router.patch("/cirujanos/{cid}/toggle")
def toggle_cirujano(
    cid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    c = db.query(Cirujano).filter(Cirujano.id == cid).first()
    if not c:
        raise HTTPException(404, "No encontrado")
    c.activo = not c.activo
    db.commit()
    return {"id": c.id, "activo": c.activo}


# ── Tipos de cirugía ─────────────────────────────────────────────────────────
# En la Fase 1 los 4 tipos originales van ligados a una tabla del esquema, así
# que sólo se permite renombrarlos y cambiar color/oncológico, no eliminarlos.
@router.patch("/tipos/{tid}")
def editar_tipo(
    tid: int,
    data: TipoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    t = db.query(TipoCirugia).filter(TipoCirugia.id == tid).first()
    if not t:
        raise HTTPException(404, "No encontrado")
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    t.nombre = nombre
    t.color = data.color or t.color
    t.tiene_oncologico = data.tiene_oncologico
    db.commit()
    return {"id": t.id, "nombre": t.nombre, "color": t.color,
            "tiene_oncologico": t.tiene_oncologico}


# ── Diagnósticos ─────────────────────────────────────────────────────────────
@router.post("/diagnosticos")
def crear_diagnostico(
    data: DiagnosticoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    if not db.query(TipoCirugia).filter(TipoCirugia.id == data.tipo_id).first():
        raise HTTPException(404, "Tipo de cirugía no encontrado")
    dup = db.query(Diagnostico).filter(
        Diagnostico.nombre == nombre, Diagnostico.tipo_id == data.tipo_id
    ).first()
    if dup:
        raise HTTPException(400, "Ese diagnóstico ya existe en este tipo")
    ultimo = db.query(Diagnostico).filter(
        Diagnostico.tipo_id == data.tipo_id
    ).order_by(Diagnostico.orden.desc()).first()
    d = Diagnostico(
        nombre=nombre, tipo_id=data.tipo_id,
        es_oncologico=data.es_oncologico,
        orden=(ultimo.orden + 1) if ultimo else 0,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id": d.id, "nombre": d.nombre, "activo": d.activo,
            "es_oncologico": d.es_oncologico}


@router.patch("/diagnosticos/{did}")
def renombrar_diagnostico(
    did: int,
    data: RenombrarIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    d = db.query(Diagnostico).filter(Diagnostico.id == did).first()
    if not d:
        raise HTTPException(404, "No encontrado")
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    d.nombre = nombre
    db.commit()
    return {"id": d.id, "nombre": d.nombre, "activo": d.activo}


@router.patch("/diagnosticos/{did}/oncologico")
def toggle_oncologico(
    did: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    d = db.query(Diagnostico).filter(Diagnostico.id == did).first()
    if not d:
        raise HTTPException(404, "No encontrado")
    d.es_oncologico = not d.es_oncologico
    db.commit()
    return {"id": d.id, "es_oncologico": d.es_oncologico}


@router.patch("/diagnosticos/{did}/toggle")
def toggle_diagnostico(
    did: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    d = db.query(Diagnostico).filter(Diagnostico.id == did).first()
    if not d:
        raise HTTPException(404, "No encontrado")
    d.activo = not d.activo
    db.commit()
    return {"id": d.id, "activo": d.activo}


# ── Intervenciones ───────────────────────────────────────────────────────────
@router.post("/intervenciones")
def crear_intervencion(
    data: IntervencionIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    diag = db.query(Diagnostico).filter(
        Diagnostico.id == data.diagnostico_id
    ).first()
    if not diag:
        raise HTTPException(404, "Diagnóstico no encontrado")
    dup = db.query(Intervencion).filter(
        Intervencion.nombre == nombre,
        Intervencion.diagnostico_id == data.diagnostico_id,
    ).first()
    if dup:
        raise HTTPException(400, "Esa intervención ya existe en este diagnóstico")
    ultimo = db.query(Intervencion).filter(
        Intervencion.diagnostico_id == data.diagnostico_id
    ).order_by(Intervencion.orden.desc()).first()
    i = Intervencion(
        nombre=nombre, diagnostico_id=data.diagnostico_id,
        orden=(ultimo.orden + 1) if ultimo else 0,
    )
    db.add(i)
    db.commit()
    db.refresh(i)
    return {"id": i.id, "nombre": i.nombre, "activo": i.activo}


@router.patch("/intervenciones/{iid}")
def renombrar_intervencion(
    iid: int,
    data: RenombrarIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    i = db.query(Intervencion).filter(Intervencion.id == iid).first()
    if not i:
        raise HTTPException(404, "No encontrada")
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    i.nombre = nombre
    db.commit()
    return {"id": i.id, "nombre": i.nombre, "activo": i.activo}


@router.patch("/intervenciones/{iid}/toggle")
def toggle_intervencion(
    iid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    i = db.query(Intervencion).filter(Intervencion.id == iid).first()
    if not i:
        raise HTTPException(404, "No encontrada")
    i.activo = not i.activo
    db.commit()
    return {"id": i.id, "activo": i.activo}
