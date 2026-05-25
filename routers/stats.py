from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _base_stats(db, Model):
    total = db.query(Model).count()
    avg_edad = db.query(func.avg(Model.edad)).scalar() or 0
    avg_estancia = db.query(func.avg(Model.estancia)).scalar() or 0
    lap = db.query(Model).filter(Model.abordaje.in_(["Laparoscopia", "Robótico"])).count()
    conversion = db.query(Model).filter(Model.conversion == "Si").count()
    clavien2 = db.query(Model).filter(Model.clavien_dindo.in_(["II", "IIIa", "IIIb", "IVa", "IVb", "V"])).count()
    reint = db.query(Model).filter(Model.reintervencion == "Si").count()
    mort = db.query(Model).filter(Model.mortalidad == "Si").count()
    reingreso = db.query(Model).filter(Model.reingreso_30d == "Si").count()
    return {
        "total": total,
        "edad_media": round(float(avg_edad), 1),
        "estancia_media": round(float(avg_estancia), 1),
        "pct_laparoscopia": round(lap / total * 100, 1) if total else 0,
        "pct_conversion": round(conversion / lap * 100, 1) if lap else 0,
        "pct_clavien_ge2": round(clavien2 / total * 100, 1) if total else 0,
        "pct_reintervencion": round(reint / total * 100, 1) if total else 0,
        "pct_mortalidad": round(mort / total * 100, 1) if total else 0,
        "pct_reingreso_30d": round(reingreso / total * 100, 1) if total else 0,
    }


@router.get("/global")
def global_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    cr = db.query(CirugiaColorrectal).count()
    pr = db.query(Proctologia).count()
    fu = db.query(TrastornosFuncionales).count()
    ge = db.query(CirugiaGeneral).count()
    total = cr + pr + fu + ge

    # Casos por mes (últimos 24 meses) — union approach
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT strftime('%Y-%m', fecha_intervencion) as mes, COUNT(*) as n FROM cirugia_colorrectal GROUP BY mes
        UNION ALL
        SELECT strftime('%Y-%m', fecha_intervencion), COUNT(*) FROM proctologia GROUP BY mes
        UNION ALL
        SELECT strftime('%Y-%m', fecha_intervencion), COUNT(*) FROM trastornos_funcionales GROUP BY mes
        UNION ALL
        SELECT strftime('%Y-%m', fecha_intervencion), COUNT(*) FROM cirugia_general GROUP BY mes
    """)).fetchall()

    from collections import defaultdict
    monthly: dict = defaultdict(int)
    for mes, n in rows:
        if mes:
            monthly[mes] += n
    monthly_sorted = sorted(monthly.items())[-24:]

    # Abordaje distribution
    abordaje_rows = db.execute(text("""
        SELECT abordaje, COUNT(*) FROM cirugia_colorrectal GROUP BY abordaje
        UNION ALL SELECT abordaje, COUNT(*) FROM proctologia GROUP BY abordaje
        UNION ALL SELECT abordaje, COUNT(*) FROM trastornos_funcionales GROUP BY abordaje
        UNION ALL SELECT abordaje, COUNT(*) FROM cirugia_general GROUP BY abordaje
    """)).fetchall()
    abordaje_map: dict = defaultdict(int)
    for ab, n in abordaje_rows:
        if ab:
            abordaje_map[ab] += n

    # Casos por cirujano
    cir_rows = db.execute(text("""
        SELECT cirujano, COUNT(*) FROM cirugia_colorrectal GROUP BY cirujano
        UNION ALL SELECT cirujano, COUNT(*) FROM proctologia GROUP BY cirujano
        UNION ALL SELECT cirujano, COUNT(*) FROM trastornos_funcionales GROUP BY cirujano
        UNION ALL SELECT cirujano, COUNT(*) FROM cirugia_general GROUP BY cirujano
    """)).fetchall()
    cir_map: dict = defaultdict(int)
    for cir, n in cir_rows:
        if cir:
            cir_map[cir] += n

    stats = {}
    if total > 0:
        all_ages = []
        all_estancias = []
        for Model in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral]:
            a = db.query(func.avg(Model.edad)).scalar()
            e = db.query(func.avg(Model.estancia)).scalar()
            c = db.query(Model).count()
            if a and c:
                all_ages.append((float(a), c))
            if e and c:
                all_estancias.append((float(e), c))
        edad_media = sum(a * c for a, c in all_ages) / sum(c for _, c in all_ages) if all_ages else 0
        estancia_media = sum(e * c for e, c in all_estancias) / sum(c for _, c in all_estancias) if all_estancias else 0

        lap_total = sum(
            db.query(M).filter(M.abordaje.in_(["Laparoscopia", "Robótico"])).count()
            for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral]
        )
        conv_total = sum(
            db.query(M).filter(M.conversion == "Si").count()
            for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral]
        )
        clavien2_total = sum(
            db.query(M).filter(M.clavien_dindo.in_(["II", "IIIa", "IIIb", "IVa", "IVb", "V"])).count()
            for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral]
        )
        reint_total = sum(db.query(M).filter(M.reintervencion == "Si").count() for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral])
        mort_total = sum(db.query(M).filter(M.mortalidad == "Si").count() for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral])
        reingreso_total = sum(db.query(M).filter(M.reingreso_30d == "Si").count() for M in [CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral])

        stats = {
            "total": total,
            "colorrectal": cr,
            "proctologia": pr,
            "funcionales": fu,
            "general": ge,
            "edad_media": round(edad_media, 1),
            "estancia_media": round(estancia_media, 1),
            "pct_laparoscopia": round(lap_total / total * 100, 1),
            "pct_conversion": round(conv_total / lap_total * 100, 1) if lap_total else 0,
            "pct_clavien_ge2": round(clavien2_total / total * 100, 1),
            "pct_reintervencion": round(reint_total / total * 100, 1),
            "pct_mortalidad": round(mort_total / total * 100, 1),
            "pct_reingreso_30d": round(reingreso_total / total * 100, 1),
            "monthly": [{"mes": m, "n": n} for m, n in monthly_sorted],
            "abordaje": dict(abordaje_map),
            "por_cirujano": dict(sorted(cir_map.items(), key=lambda x: -x[1])),
        }
    else:
        stats = {
            "total": 0, "colorrectal": 0, "proctologia": 0, "funcionales": 0, "general": 0,
            "edad_media": 0, "estancia_media": 0, "pct_laparoscopia": 0, "pct_conversion": 0,
            "pct_clavien_ge2": 0, "pct_reintervencion": 0, "pct_mortalidad": 0, "pct_reingreso_30d": 0,
            "monthly": [], "abordaje": {}, "por_cirujano": {},
        }
    return stats


@router.get("/colorrectal")
def colorrectal_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _base_stats(db, CirugiaColorrectal)
    total = stats["total"]

    estadios = {}
    for est in ["0", "I", "IIA", "IIB", "IIC", "IIIA", "IIIB", "IIIC", "IVA", "IVB", "IVC"]:
        estadios[est] = db.query(CirugiaColorrectal).filter(CirugiaColorrectal.estadio_tnm == est).count()

    neo = db.query(CirugiaColorrectal).filter(CirugiaColorrectal.neoadyuvancia == "Si").count()
    pcr = db.query(CirugiaColorrectal).filter(CirugiaColorrectal.pcr == "Si").count()
    margenes = db.query(CirugiaColorrectal).filter(CirugiaColorrectal.margenes_libres == "Si").count()
    dehiscencia = db.query(CirugiaColorrectal).filter(CirugiaColorrectal.dehiscencia == "Si").count()

    intervalos = {}
    for m in [3, 6, 12, 18, 24, 36, 48, 60]:
        col = getattr(CirugiaColorrectal, f"recidiva_{m}m")
        intervalos[f"{m}m"] = db.query(CirugiaColorrectal).filter(col == "Si").count()

    diag_rows = db.query(CirugiaColorrectal.diagnostico, func.count()).group_by(CirugiaColorrectal.diagnostico).all()
    interv_rows = db.query(CirugiaColorrectal.intervencion, func.count()).group_by(CirugiaColorrectal.intervencion).all()

    stats.update({
        "estadios": estadios,
        "pct_neoadyuvancia": round(neo / total * 100, 1) if total else 0,
        "pct_pcr": round(pcr / neo * 100, 1) if neo else 0,
        "pct_margenes_libres": round(margenes / total * 100, 1) if total else 0,
        "pct_dehiscencia": round(dehiscencia / total * 100, 1) if total else 0,
        "recidiva_intervalos": intervalos,
        "por_diagnostico": {d: n for d, n in diag_rows if d},
        "por_intervencion": {i: n for i, n in interv_rows if i},
    })
    return stats


@router.get("/proctologia")
def proctologia_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _base_stats(db, Proctologia)
    diag_rows = db.query(Proctologia.diagnostico, func.count()).group_by(Proctologia.diagnostico).all()
    interv_rows = db.query(Proctologia.intervencion, func.count()).group_by(Proctologia.intervencion).all()
    stats.update({
        "por_diagnostico": {d: n for d, n in diag_rows if d},
        "por_intervencion": {i: n for i, n in interv_rows if i},
    })
    return stats


@router.get("/funcionales")
def funcionales_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _base_stats(db, TrastornosFuncionales)
    diag_rows = db.query(TrastornosFuncionales.diagnostico, func.count()).group_by(TrastornosFuncionales.diagnostico).all()
    interv_rows = db.query(TrastornosFuncionales.intervencion, func.count()).group_by(TrastornosFuncionales.intervencion).all()
    stats.update({
        "por_diagnostico": {d: n for d, n in diag_rows if d},
        "por_intervencion": {i: n for i, n in interv_rows if i},
    })
    return stats


@router.get("/general")
def general_stats(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    stats = _base_stats(db, CirugiaGeneral)
    diag_rows = db.query(CirugiaGeneral.diagnostico, func.count()).group_by(CirugiaGeneral.diagnostico).all()
    interv_rows = db.query(CirugiaGeneral.intervencion, func.count()).group_by(CirugiaGeneral.intervencion).all()
    stats.update({
        "por_diagnostico": {d: n for d, n in diag_rows if d},
        "por_intervencion": {i: n for i, n in interv_rows if i},
    })
    return stats
