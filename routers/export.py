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


def _get_rows(db, Model, fecha_desde, fecha_hasta):
    q = db.query(Model)
    if fecha_desde:
        q = q.filter(Model.fecha_intervencion >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Model.fecha_intervencion <= fecha_hasta)
    return q.order_by(Model.fecha_intervencion).all()


def _row_to_dict(obj):
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, date):
            val = val.isoformat()
        result[col.name] = val
    return result


@router.get("/csv")
def export_csv(
    tabla: str = Query("todas"),
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    output = io.StringIO()

    if tabla == "todas":
        models = list(TABLES.items())
    elif tabla in TABLES:
        models = [(tabla, TABLES[tabla])]
    else:
        models = []

    writer = None
    for name, Model in models:
        rows = _get_rows(db, Model, fecha_desde, fecha_hasta)
        if not rows:
            continue
        dicts = [_row_to_dict(r) for r in rows]
        if writer is None:
            writer = csv.DictWriter(output, fieldnames=dicts[0].keys() if dicts else [])
            writer.writeheader()
        for d in dicts:
            writer.writerow({k: d.get(k, "") for k in writer.fieldnames})

    output.seek(0)
    filename = f"coloproctologia_{tabla}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


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

    COLORS = {
        "colorrectal": "FF1565C0",
        "proctologia": "FF2E7D32",
        "funcionales": "FF6A1B9A",
        "general": "FFE65100",
    }

    if tabla == "todas":
        models = list(TABLES.items())
    elif tabla in TABLES:
        models = [(tabla, TABLES[tabla])]
    else:
        models = []

    for name, Model in models:
        rows = _get_rows(db, Model, fecha_desde, fecha_hasta)
        ws = wb.create_sheet(title=name.capitalize())
        if not rows:
            ws.append(["Sin datos"])
            continue
        dicts = [_row_to_dict(r) for r in rows]
        headers = list(dicts[0].keys())
        ws.append(headers)
        header_fill = PatternFill("solid", fgColor=COLORS.get(name, "FF0D2B4E"))
        header_font = Font(bold=True, color="FFFFFFFF")
        for col_idx, _ in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        for row_idx, d in enumerate(dicts, 2):
            for col_idx, key in enumerate(headers, 1):
                ws.cell(row=row_idx, column=col_idx, value=d.get(key))
            if row_idx % 2 == 0:
                for col_idx in range(1, len(headers) + 1):
                    ws.cell(row=row_idx, column=col_idx).fill = PatternFill("solid", fgColor="FFF5F5F5")
        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"coloproctologia_{tabla}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
