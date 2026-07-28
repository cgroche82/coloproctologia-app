"""
CRUD de los catálogos editables desde Ajustes.

Lectura: cualquier usuario autenticado (los desplegables del formulario).
Escritura: sólo administradores.

Nunca se borra físicamente nada que pueda estar en uso: se desactiva. Los
registros guardan estos valores como texto, así que desactivar un diagnóstico
lo retira de los desplegables sin tocar los casos ya grabados.
"""

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Registro, TipoCirugia, Diagnostico, Intervencion, Cirujano
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
# Con la tabla única el tipo es un dato más, así que ya pueden crearse desde
# aquí: cada uno trae su exportación y sus estadísticas sin tocar el código.
def _slug(nombre: str) -> str:
    base = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-zA-Z0-9]+", "_", base).strip("_").lower()
    return base or "tipo"


@router.post("/tipos")
def crear_tipo(
    data: TipoIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    nombre = data.nombre.strip()
    if not nombre:
        raise HTTPException(400, "El nombre no puede estar vacío")
    if db.query(TipoCirugia).filter(TipoCirugia.nombre == nombre).first():
        raise HTTPException(400, "Ya existe un tipo con ese nombre")

    # El slug debe ser único: se numera si hiciera falta
    base = _slug(nombre)
    slug, n = base, 2
    while db.query(TipoCirugia).filter(TipoCirugia.slug == slug).first():
        slug, n = f"{base}_{n}", n + 1

    ultimo = db.query(TipoCirugia).order_by(TipoCirugia.orden.desc()).first()
    t = TipoCirugia(
        slug=slug, nombre=nombre, color=data.color or "#1565C0",
        tiene_oncologico=data.tiene_oncologico,
        orden=(ultimo.orden + 1) if ultimo else 0, activo=True,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "slug": t.slug, "nombre": t.nombre,
            "color": t.color, "tiene_oncologico": t.tiene_oncologico}


@router.patch("/tipos/{tid}/toggle")
def toggle_tipo(
    tid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    t = db.query(TipoCirugia).filter(TipoCirugia.id == tid).first()
    if not t:
        raise HTTPException(404, "No encontrado")
    # Desactivar un tipo con casos los dejaría fuera de los filtros por grupo,
    # así que se avisa con el recuento en vez de impedirlo sin explicación
    if t.activo:
        n = db.query(Registro).filter(Registro.tipo_id == tid).count()
        if n:
            raise HTTPException(
                400,
                f"«{t.nombre}» tiene {n} registro(s). Reasígnalos a otro grupo "
                f"antes de desactivarlo para que no queden descolgados."
            )
    t.activo = not t.activo
    db.commit()
    return {"id": t.id, "activo": t.activo}


@router.get("/tipos/{tid}/uso")
def uso_tipo(
    tid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    """Cuántos registros hay en el grupo. La UI lo consulta antes de borrar."""
    return {"registros": db.query(Registro).filter(Registro.tipo_id == tid).count()}


@router.delete("/tipos/{tid}")
def eliminar_tipo(
    tid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    """
    Borrado definitivo del grupo, con sus diagnósticos e intervenciones.

    A diferencia de los demás catálogos, los registros apuntan al grupo por
    identificador, no por texto: borrar uno que tenga casos los dejaría
    huérfanos. Por eso aquí sí se exige vaciarlo antes.
    """
    t = db.query(TipoCirugia).filter(TipoCirugia.id == tid).first()
    if not t:
        raise HTTPException(404, "No encontrado")

    n = db.query(Registro).filter(Registro.tipo_id == tid).count()
    if n:
        raise HTTPException(
            400,
            f"«{t.nombre}» tiene {n} registro(s). Muévelos a otro grupo antes "
            f"de eliminarlo, o se quedarían sin grupo."
        )

    diags = db.query(Diagnostico).filter(Diagnostico.tipo_id == tid).all()
    for d in diags:
        db.query(Intervencion).filter(Intervencion.diagnostico_id == d.id).delete()
        db.delete(d)
    db.delete(t)
    db.commit()
    return {"ok": True, "diagnosticos_eliminados": len(diags)}


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


# Los registros guardan diagnóstico, intervención y cirujano como TEXTO, así
# que eliminarlos del catálogo nunca altera los casos ya grabados: sólo dejan
# de ofrecerse. Se devuelve el número de usos para poder avisar antes.
@router.get("/diagnosticos/{did}/uso")
def uso_diagnostico(
    did: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    d = db.query(Diagnostico).filter(Diagnostico.id == did).first()
    if not d:
        raise HTTPException(404, "No encontrado")
    return {
        "registros": db.query(Registro).filter(Registro.diagnostico == d.nombre).count(),
        "intervenciones": db.query(Intervencion)
                            .filter(Intervencion.diagnostico_id == did).count(),
    }


@router.delete("/diagnosticos/{did}")
def eliminar_diagnostico(
    did: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    d = db.query(Diagnostico).filter(Diagnostico.id == did).first()
    if not d:
        raise HTTPException(404, "No encontrado")
    n = db.query(Intervencion).filter(Intervencion.diagnostico_id == did).delete()
    db.delete(d)
    db.commit()
    return {"ok": True, "intervenciones_eliminadas": n}


@router.get("/intervenciones/{iid}/uso")
def uso_intervencion(
    iid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    i = db.query(Intervencion).filter(Intervencion.id == iid).first()
    if not i:
        raise HTTPException(404, "No encontrada")
    return {"registros": db.query(Registro)
                           .filter(Registro.intervencion == i.nombre).count()}


@router.delete("/intervenciones/{iid}")
def eliminar_intervencion(
    iid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    i = db.query(Intervencion).filter(Intervencion.id == iid).first()
    if not i:
        raise HTTPException(404, "No encontrada")
    db.delete(i)
    db.commit()
    return {"ok": True}


@router.get("/cirujanos/{cid}/uso")
def uso_cirujano(
    cid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    c = db.query(Cirujano).filter(Cirujano.id == cid).first()
    if not c:
        raise HTTPException(404, "No encontrado")
    return {"registros": db.query(Registro)
                           .filter(Registro.cirujano == c.nombre).count()}


@router.delete("/cirujanos/{cid}")
def eliminar_cirujano(
    cid: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    c = db.query(Cirujano).filter(Cirujano.id == cid).first()
    if not c:
        raise HTTPException(404, "No encontrado")
    db.delete(c)
    db.commit()
    return {"ok": True}


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
