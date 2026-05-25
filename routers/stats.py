from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/stats", tags=["stats"])

ALL_MODELS = [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral]


# ── helpers ──────────────────────────────────────────────────────────────────
def _count_val(db, Model, col, val):
    return db.query(Model).filter(getattr(Model, col) == val).count()

def _count_in(db, Model, col, vals):
    return db.query(Model).filter(getattr(Model, col).in_(vals)).count()

def _group_by(db, Model, col):
    rows = db.query(getattr(Model, col), func.count()).group_by(getattr(Model, col)).all()
    return {v: n for v, n in rows if v}

def _avg(db, Model, col):
    v = db.query(func.avg(getattr(Model, col))).scalar()
    return round(float(v), 1) if v else 0.0

def _monthly(db, Model):
    """Returns {YYYY-MM: count} dict using Python-level grouping (no raw SQL)."""
    rows = db.query(Model.fecha_intervencion).all()
    m: dict = defaultdict(int)
    for (d,) in rows:
        if d:
            key = d.strftime('%Y-%m')
            m[key] += 1
    return m


def _base_stats(db, Model):
    total = db.query(Model).count()
    lap = _count_in(db, Model, 'abordaje', ['Laparoscopia', 'Robótico'])
    conv = _count_val(db, Model, 'conversion', 'Si')
    clavien2 = _count_in(db, Model, 'clavien_dindo', ['II','IIIa','IIIb','IVa','IVb','V'])
    reint = _count_val(db, Model, 'reintervencion', 'Si')
    mort = _count_val(db, Model, 'mortalidad', 'Si')
    reingreso = _count_val(db, Model, 'reingreso_30d', 'Si')

    return {
        "total": total,
        "edad_media": _avg(db, Model, 'edad'),
        "tq_medio": _avg(db, Model, 'tiempo_quirurgico'),
        "estancia_media": _avg(db, Model, 'estancia'),
        "pct_laparoscopia": round(lap / total * 100, 1) if total else 0,
        "pct_conversion": round(conv / lap * 100, 1) if lap else 0,
        "pct_clavien_ge2": round(clavien2 / total * 100, 1) if total else 0,
        "pct_reintervencion": round(reint / total * 100, 1) if total else 0,
        "pct_mortalidad": round(mort / total * 100, 1) if total else 0,
        "pct_reingreso_30d": round(reingreso / total * 100, 1) if total else 0,
        # Distributions
        "por_sexo": _group_by(db, Model, 'sexo'),
        "por_asa": _group_by(db, Model, 'asa'),
        "por_abordaje": _group_by(db, Model, 'abordaje'),
        "por_urgencia": _group_by(db, Model, 'urgencia'),
        "por_clavien": _group_by(db, Model, 'clavien_dindo'),
        "por_tipo_complicacion": _group_by(db, Model, 'tipo_complicacion'),
        "por_cirujano": _group_by(db, Model, 'cirujano'),
        "por_diagnostico": _group_by(db, Model, 'diagnostico'),
        "por_intervencion": _group_by(db, Model, 'intervencion'),
    }


# ── GLOBAL ───────────────────────────────────────────────────────────────────
@router.get("/global")
def global_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    counts = {
        'colorrectal': db.query(CirugiaColorrectal).count(),
        'proctologia': db.query(Proctologia).count(),
        'funcionales': db.query(TrastornosFuncionales).count(),
        'general': db.query(CirugiaGeneral).count(),
    }
    total = sum(counts.values())

    # Weighted averages across all tables
    def _weighted_avg(col):
        acc_sum, acc_n = 0.0, 0
        for M in ALL_MODELS:
            v = db.query(func.avg(getattr(M, col))).scalar()
            n = db.query(M).count()
            if v and n:
                acc_sum += float(v) * n
                acc_n += n
        return round(acc_sum / acc_n, 1) if acc_n else 0.0

    # Aggregate counts across tables
    def _sum_count(col, vals=None, val=None):
        out = 0
        for M in ALL_MODELS:
            if vals is not None:
                out += _count_in(db, M, col, vals)
            else:
                out += _count_val(db, M, col, val)
        return out

    lap_total = _sum_count('abordaje', vals=['Laparoscopia', 'Robótico'])
    conv_total = _sum_count('conversion', val='Si')
    clavien2_total = _sum_count('clavien_dindo', vals=['II','IIIa','IIIb','IVa','IVb','V'])
    reint_total = _sum_count('reintervencion', val='Si')
    mort_total = _sum_count('mortalidad', val='Si')
    reingreso_total = _sum_count('reingreso_30d', val='Si')

    # Monthly — pure Python, no UNION SQL
    monthly_combined: dict = defaultdict(int)
    for M in ALL_MODELS:
        for k, v in _monthly(db, M).items():
            monthly_combined[k] += v
    monthly_sorted = [{"mes": m, "n": n} for m, n in sorted(monthly_combined.items())[-24:]]

    # Abordaje across all tables
    abordaje_map: dict = defaultdict(int)
    for M in ALL_MODELS:
        for k, v in _group_by(db, M, 'abordaje').items():
            abordaje_map[k] += v

    # Cirujano across all tables
    cir_map: dict = defaultdict(int)
    for M in ALL_MODELS:
        for k, v in _group_by(db, M, 'cirujano').items():
            cir_map[k] += v

    return {
        "total": total,
        **counts,
        "edad_media": _weighted_avg('edad'),
        "estancia_media": _weighted_avg('estancia'),
        "pct_laparoscopia": round(lap_total / total * 100, 1) if total else 0,
        "pct_conversion": round(conv_total / lap_total * 100, 1) if lap_total else 0,
        "pct_clavien_ge2": round(clavien2_total / total * 100, 1) if total else 0,
        "pct_reintervencion": round(reint_total / total * 100, 1) if total else 0,
        "pct_mortalidad": round(mort_total / total * 100, 1) if total else 0,
        "pct_reingreso_30d": round(reingreso_total / total * 100, 1) if total else 0,
        "monthly": monthly_sorted,
        "abordaje": dict(abordaje_map),
        "por_cirujano": dict(sorted(cir_map.items(), key=lambda x: -x[1])),
    }


# ── COLORRECTAL ──────────────────────────────────────────────────────────────
@router.get("/colorrectal")
def colorrectal_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _base_stats(db, CirugiaColorrectal)
    total = stats["total"]

    M = CirugiaColorrectal
    estoma = _count_val(db, M, 'estoma_proteccion', 'Si')
    dehiscencia = _count_val(db, M, 'dehiscencia', 'Si')
    neo = _count_val(db, M, 'neoadyuvancia', 'Si')
    pcr = _count_val(db, M, 'pcr', 'Si')
    margenes = _count_val(db, M, 'margenes_libres', 'Si')
    ady = _count_val(db, M, 'adyuvancia', 'Si')
    ganglios_media = _avg(db, M, 'ganglios_analizados')

    estadios = {}
    for est in ["0","I","IIA","IIB","IIC","IIIA","IIIB","IIIC","IVA","IVB","IVC"]:
        estadios[est] = db.query(M).filter(M.estadio_tnm == est).count()

    intervalos = {}
    for mo in [3, 6, 12, 18, 24, 36, 48, 60]:
        col = getattr(M, f"recidiva_{mo}m")
        intervalos[f"{mo}m"] = db.query(M).filter(col == "Si").count()

    stats.update({
        "pct_estoma_proteccion": round(estoma / total * 100, 1) if total else 0,
        "pct_dehiscencia": round(dehiscencia / total * 100, 1) if total else 0,
        "pct_neoadyuvancia": round(neo / total * 100, 1) if total else 0,
        "pct_pcr": round(pcr / neo * 100, 1) if neo else 0,
        "pct_margenes_libres": round(margenes / total * 100, 1) if total else 0,
        "pct_adyuvancia": round(ady / total * 100, 1) if total else 0,
        "ganglios_media": ganglios_media,
        "estadios": estadios,
        "recidiva_intervalos": intervalos,
        "por_neoadyuvancia": _group_by(db, M, 'neoadyuvancia'),
        "por_adyuvancia": _group_by(db, M, 'adyuvancia'),
    })
    return stats


# ── PROCTOLOGÍA ──────────────────────────────────────────────────────────────
@router.get("/proctologia")
def proctologia_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return _base_stats(db, Proctologia)


# ── FUNCIONALES ──────────────────────────────────────────────────────────────
@router.get("/funcionales")
def funcionales_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return _base_stats(db, TrastornosFuncionales)


# ── GENERAL ──────────────────────────────────────────────────────────────────
@router.get("/general")
def general_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return _base_stats(db, CirugiaGeneral)
