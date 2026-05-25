from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db, CirugiaGeneral
from schemas import GeneralCreate, GeneralOut
from auth import get_current_user, Usuario

router = APIRouter(prefix="/api/general", tags=["general"])


@router.get("/next-id")
def next_id(db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    last = db.query(CirugiaGeneral).order_by(CirugiaGeneral.id.desc()).first()
    return {"next_id": (last.id + 1) if last else 1}


@router.post("", response_model=GeneralOut)
def create(data: GeneralCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    record = CirugiaGeneral(**data.model_dump(), created_by=user.username)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=dict)
def list_all(
    page: int = 1,
    page_size: int = 20,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    diagnostico: Optional[str] = None,
    cirujano: Optional[str] = None,
    asa: Optional[str] = None,
    nhc: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(CirugiaGeneral)
    if nhc:
        q = q.filter(CirugiaGeneral.nhc.ilike(f"%{nhc}%"))
    if fecha_desde:
        q = q.filter(CirugiaGeneral.fecha_intervencion >= fecha_desde)
    if fecha_hasta:
        q = q.filter(CirugiaGeneral.fecha_intervencion <= fecha_hasta)
    if diagnostico:
        q = q.filter(CirugiaGeneral.diagnostico.ilike(f"%{diagnostico}%"))
    if cirujano:
        q = q.filter(CirugiaGeneral.cirujano == cirujano)
    if asa:
        q = q.filter(CirugiaGeneral.asa == asa)
    total = q.count()
    items = q.order_by(CirugiaGeneral.fecha_intervencion.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [GeneralOut.model_validate(i) for i in items]}


@router.get("/{id}", response_model=GeneralOut)
def get_one(id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    record = db.query(CirugiaGeneral).filter(CirugiaGeneral.id == id).first()
    if not record:
        raise HTTPException(404, "No encontrado")
    return record


@router.put("/{id}", response_model=GeneralOut)
def update(id: int, data: GeneralCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    record = db.query(CirugiaGeneral).filter(CirugiaGeneral.id == id).first()
    if not record:
        raise HTTPException(404, "No encontrado")
    for k, v in data.model_dump().items():
        setattr(record, k, v)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    record = db.query(CirugiaGeneral).filter(CirugiaGeneral.id == id).first()
    if not record:
        raise HTTPException(404, "No encontrado")
    db.delete(record)
    db.commit()
    return {"ok": True}
