"""
Estadísticas del dashboard.

Trabaja sobre la tabla única filtrando por `tipo_id`, así que sirve cualquier
tipo de cirugía existente o futuro sin tocar el código. Antes había un endpoint
escrito a mano por cada una de las cuatro tablas.
"""

from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db, Registro, TipoCirugia
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/stats", tags=["stats"])

CLAVIEN_GE2 = ["II", "IIIa", "IIIb", "IVa", "IVb", "V"]
MINIMAMENTE_INVASIVO = ["Laparoscopia", "Robótico"]
ESTADIOS = ["0", "I", "IIA", "IIB", "IIC", "IIIA", "IIIB", "IIIC", "IVA", "IVB", "IVC"]
INTERVALOS_RECIDIVA = [3, 6, 12, 18, 24, 36, 48, 60]


# ── Ayudas ───────────────────────────────────────────────────────────────────
def _base(db: Session, tipo_id: Optional[int] = None):
    q = db.query(Registro)
    return q.filter(Registro.tipo_id == tipo_id) if tipo_id else q


def _count_val(db, col, val, tipo_id=None):
    return _base(db, tipo_id).filter(getattr(Registro, col) == val).count()


def _count_in(db, col, vals, tipo_id=None):
    return _base(db, tipo_id).filter(getattr(Registro, col).in_(vals)).count()


def _group_by(db, col, tipo_id=None):
    q = db.query(getattr(Registro, col), func.count())
    if tipo_id:
        q = q.filter(Registro.tipo_id == tipo_id)
    return {v: n for v, n in q.group_by(getattr(Registro, col)).all() if v}


def _avg(db, col, tipo_id=None):
    q = db.query(func.avg(getattr(Registro, col)))
    if tipo_id:
        q = q.filter(Registro.tipo_id == tipo_id)
    v = q.scalar()
    return round(float(v), 1) if v else 0.0


def _pct(parte, total):
    return round(parte / total * 100, 1) if total else 0


def _mensual(db, tipo_id=None):
    """Agrupación en Python: evita el alias de SQL que rompía el UNION."""
    filas = _base(db, tipo_id).with_entities(Registro.fecha_intervencion).all()
    m: dict = defaultdict(int)
    for (d,) in filas:
        if d:
            m[d.strftime("%Y-%m")] += 1
    return m


def _estadisticas_comunes(db: Session, tipo_id: Optional[int] = None) -> dict:
    total = _base(db, tipo_id).count()
    lap = _count_in(db, "abordaje", MINIMAMENTE_INVASIVO, tipo_id)

    return {
        "total": total,
        "edad_media": _avg(db, "edad", tipo_id),
        "tq_medio": _avg(db, "tiempo_quirurgico", tipo_id),
        "estancia_media": _avg(db, "estancia", tipo_id),
        "pct_laparoscopia": _pct(lap, total),
        "pct_conversion": _pct(_count_val(db, "conversion", "Si", tipo_id), lap),
        "pct_clavien_ge2": _pct(_count_in(db, "clavien_dindo", CLAVIEN_GE2, tipo_id), total),
        "pct_reintervencion": _pct(_count_val(db, "reintervencion", "Si", tipo_id), total),
        "pct_mortalidad": _pct(_count_val(db, "mortalidad", "Si", tipo_id), total),
        "pct_reingreso_30d": _pct(_count_val(db, "reingreso_30d", "Si", tipo_id), total),
        "por_sexo": _group_by(db, "sexo", tipo_id),
        "por_asa": _group_by(db, "asa", tipo_id),
        "por_abordaje": _group_by(db, "abordaje", tipo_id),
        "por_urgencia": _group_by(db, "urgencia", tipo_id),
        "por_clavien": _group_by(db, "clavien_dindo", tipo_id),
        "por_tipo_complicacion": _group_by(db, "tipo_complicacion", tipo_id),
        "por_cirujano": _group_by(db, "cirujano", tipo_id),
        "por_diagnostico": _group_by(db, "diagnostico", tipo_id),
        "por_intervencion": _group_by(db, "intervencion", tipo_id),
    }


def _estadisticas_oncologicas(db: Session, tipo_id: int) -> dict:
    total = _base(db, tipo_id).count()
    neo = _count_val(db, "neoadyuvancia", "Si", tipo_id)

    estadios = {
        e: _base(db, tipo_id).filter(Registro.estadio_tnm == e).count()
        for e in ESTADIOS
    }
    recidivas = {
        f"{m}m": _base(db, tipo_id)
                 .filter(getattr(Registro, f"recidiva_{m}m") == "Si").count()
        for m in INTERVALOS_RECIDIVA
    }

    return {
        "pct_estoma_proteccion": _pct(_count_val(db, "estoma_proteccion", "Si", tipo_id), total),
        "pct_dehiscencia": _pct(_count_val(db, "dehiscencia", "Si", tipo_id), total),
        "pct_neoadyuvancia": _pct(neo, total),
        "pct_pcr": _pct(_count_val(db, "pcr", "Si", tipo_id), neo),
        "pct_margenes_libres": _pct(_count_val(db, "margenes_libres", "Si", tipo_id), total),
        "pct_adyuvancia": _pct(_count_val(db, "adyuvancia", "Si", tipo_id), total),
        "ganglios_media": _avg(db, "ganglios_analizados", tipo_id),
        "estadios": estadios,
        "recidiva_intervalos": recidivas,
        "por_neoadyuvancia": _group_by(db, "neoadyuvancia", tipo_id),
        "por_adyuvancia": _group_by(db, "adyuvancia", tipo_id),
    }


# ── Global ───────────────────────────────────────────────────────────────────
@router.get("/global")
def global_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _estadisticas_comunes(db)

    tipos = db.query(TipoCirugia).order_by(TipoCirugia.orden, TipoCirugia.id).all()
    por_tipo = [
        {
            "id": t.id,
            "slug": t.slug,
            "nombre": t.nombre,
            "color": t.color,
            "n": db.query(Registro).filter(Registro.tipo_id == t.id).count(),
        }
        for t in tipos
    ]

    mensual = sorted(_mensual(db).items())[-24:]
    stats.update({
        "por_tipo": por_tipo,
        "monthly": [{"mes": m, "n": n} for m, n in mensual],
        "abordaje": stats["por_abordaje"],
        "por_cirujano": dict(sorted(stats["por_cirujano"].items(), key=lambda x: -x[1])),
    })
    return stats


# ── Por tipo ─────────────────────────────────────────────────────────────────
@router.get("/tipo/{tipo_id}")
def stats_por_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    tipo = db.query(TipoCirugia).filter(TipoCirugia.id == tipo_id).first()
    if not tipo:
        raise HTTPException(404, "Tipo de cirugía no encontrado")

    stats = _estadisticas_comunes(db, tipo_id)
    stats["tipo"] = {
        "id": tipo.id, "slug": tipo.slug, "nombre": tipo.nombre,
        "color": tipo.color, "tiene_oncologico": tipo.tiene_oncologico,
    }
    mensual = sorted(_mensual(db, tipo_id).items())[-24:]
    stats["monthly"] = [{"mes": m, "n": n} for m, n in mensual]

    # El bloque oncológico sólo se calcula donde tiene sentido
    if tipo.tiene_oncologico:
        stats.update(_estadisticas_oncologicas(db, tipo_id))
    return stats
