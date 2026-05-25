import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db, CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/export", tags=["export"])

TABLES = {
    "colorrectal": CirugiaColorrectal,
    "proctologia": Proctologia,
    "funcionales": TrastornosFuncionales,
    "general": CirugiaGeneral,
}

# ── Explicit column order ────────────────────────────────────────────────────
COMMON_COLS = [
    'id', 'nhc', 'fecha_intervencion', 'fecha_nacimiento', 'edad', 'sexo',
    'asa', 'cirujano', 'ingreso_cma', 'diagnostico', 'intervencion',
    'urgencia', 'abordaje', 'conversion', 'tiempo_quirurgico',
    'clavien_dindo', 'tipo_complicacion', 'intervencionismo',
    'reintervencion', 'tipo_reintervencion', 'mortalidad', 'causa_mortalidad',
    'fecha_alta', 'estancia', 'reingreso_30d', 'observaciones',
    'created_by', 'created_at',
]

COLORRECTAL_COLS = [
    'id', 'nhc', 'fecha_intervencion', 'fecha_nacimiento', 'edad', 'sexo',
    'asa', 'cirujano', 'ingreso_cma', 'diagnostico', 'intervencion',
    'urgencia', 'abordaje', 'conversion', 'tiempo_quirurgico',
    'estoma_proteccion',
    'clavien_dindo', 'dehiscencia', 'tipo_dehiscencia',
    'tipo_complicacion', 'intervencionismo',
    'reintervencion', 'tipo_reintervencion', 'mortalidad', 'causa_mortalidad',
    'fecha_alta', 'estancia', 'reingreso_30d',
    # Oncológico
    't_tnm', 'n_tnm', 'm_tnm', 'estadio_tnm',
    'localizacion', 'distancia_margen_anal',
    'neoadyuvancia', 'tipo_neoadyuvancia', 'pcr',
    'tipo_histologico', 'grado', 'margenes_libres',
    'ganglios_analizados', 'ganglios_positivos',
    'invasion_linfovascular', 'invasion_perineural', 'msi',
    'adyuvancia', 'tipo_adyuvancia',
    # Seguimiento
    'recidiva_3m', 'tipo_recidiva_3m',
    'recidiva_6m', 'tipo_recidiva_6m',
    'recidiva_12m', 'tipo_recidiva_12m',
    'recidiva_18m', 'tipo_recidiva_18m',
    'recidiva_24m', 'tipo_recidiva_24m',
    'recidiva_36m', 'tipo_recidiva_36m',
    'recidiva_48m', 'tipo_recidiva_48m',
    'recidiva_60m', 'tipo_recidiva_60m',
    'fecha_exitus',
    'observaciones', 'created_by', 'created_at',
]

COLS_MAP = {
    "colorrectal": COLORRECTAL_COLS,
    "proctologia": COMMON_COLS,
    "funcionales": COMMON_COLS,
    "general": COMMON_COLS,
}


def _get_rows(db, Model, fecha_desde, fecha_hasta):
    q = db.query(Model)
    if fecha_desde:
        q = q.filter(Model.fecha_intervencion >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Model.fecha_intervencion <= fecha_hasta)
    return q.order_by(Model.fecha_intervencion).all()


def _row_to_dict(obj, cols):
    result = {}
    for col in cols:
        val = getattr(obj, col, None)
        if isinstance(val, date):
            val = val.isoformat()
        result[col] = val if val is not None else ''
    return result


# ── CSV ──────────────────────────────────────────────────────────────────────
@router.get("/csv")
def export_csv(
    tabla: str = Query("todas"),
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    output = io.StringIO()
    models = list(TABLES.items()) if tabla == "todas" else (
        [(tabla, TABLES[tabla])] if tabla in TABLES else []
    )

    writer = None
    for name, Model in models:
        cols = COLS_MAP[name]
        # For "todas" we use common cols to keep a single CSV
        write_cols = COMMON_COLS if tabla == "todas" else cols
        rows = _get_rows(db, Model, fecha_desde, fecha_hasta)
        if not rows:
            continue
        if writer is None:
            # Add tipo_cirugia column at the start when exporting all tables
            fieldnames = (['tipo_cirugia'] + write_cols) if tabla == "todas" else write_cols
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
        for r in rows:
            d = _row_to_dict(r, write_cols)
            if tabla == "todas":
                d = {'tipo_cirugia': name, **d}
            writer.writerow({k: d.get(k, '') for k in writer.fieldnames})

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=coloproctologia_{tabla}.csv"},
    )


# ── XLSX ─────────────────────────────────────────────────────────────────────
@router.get("/xlsx")
def export_xlsx(
    tabla: str = Query("todas"),
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    wb.remove(wb.active)

    HEADER_COLORS = {
        "colorrectal": "FF1565C0",
        "proctologia": "FF2E7D32",
        "funcionales": "FF6A1B9A",
        "general": "FFE65100",
    }
    SECTION_COLOR = "FFBBDEFB"   # light blue for oncological block header

    models = list(TABLES.items()) if tabla == "todas" else (
        [(tabla, TABLES[tabla])] if tabla in TABLES else []
    )

    for name, Model in models:
        cols = COLS_MAP[name]
        ws = wb.create_sheet(title=name.capitalize())
        rows = _get_rows(db, Model, fecha_desde, fecha_hasta)
        if not rows:
            ws.append(["Sin datos para el período seleccionado"])
            continue

        dicts = [_row_to_dict(r, cols) for r in rows]

        # Header row
        ws.append(cols)
        hdr_fill = PatternFill("solid", fgColor=HEADER_COLORS.get(name, "FF0D2B4E"))
        hdr_font = Font(bold=True, color="FFFFFFFF", size=10)
        for ci, col_name in enumerate(cols, 1):
            cell = ws.cell(row=1, column=ci)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        # Data rows
        LIGHT_GRAY = PatternFill("solid", fgColor="FFF5F5F5")
        for ri, d in enumerate(dicts, 2):
            row_fill = LIGHT_GRAY if ri % 2 == 0 else None
            for ci, col_name in enumerate(cols, 1):
                cell = ws.cell(row=ri, column=ci, value=d.get(col_name, ''))
                if row_fill:
                    cell.fill = row_fill
                cell.alignment = Alignment(horizontal="left", vertical="center")

        # Column widths — wider for date/text cols
        for ci, col_name in enumerate(cols, 1):
            if 'fecha' in col_name or 'observacion' in col_name or col_name in ('diagnostico','intervencion','tipo_reintervencion','causa_mortalidad'):
                ws.column_dimensions[get_column_letter(ci)].width = 22
            elif col_name in ('id','asa','sexo','t_tnm','n_tnm','m_tnm','grado'):
                ws.column_dimensions[get_column_letter(ci)].width = 8
            else:
                ws.column_dimensions[get_column_letter(ci)].width = 16
        ws.row_dimensions[1].height = 30

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=coloproctologia_{tabla}.xlsx"},
    )
