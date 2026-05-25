import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db, create_tables, Usuario
from auth import authenticate_user, create_access_token, get_current_user, get_admin_user, get_password_hash, init_admin_user
from schemas import Token, UsuarioCreate, UsuarioOut
from routers import colorrectal, proctologia, funcionales, general, stats, export

app = FastAPI(title="Registro Quirúrgico Coloproctología", version="1.0.0")

# Static files & templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include routers
app.include_router(colorrectal.router)
app.include_router(proctologia.router)
app.include_router(funcionales.router)
app.include_router(general.router)
app.include_router(stats.router)
app.include_router(export.router)


@app.on_event("startup")
def startup():
    create_tables()
    db = next(get_db())
    try:
        init_admin_user(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = create_access_token({"sub": user.username})
    return Token(
        access_token=token,
        token_type="bearer",
        username=user.username,
        nombre_completo=user.nombre_completo,
        es_admin=user.es_admin,
    )


@app.get("/api/auth/me")
def me(current_user: Usuario = Depends(get_current_user)):
    return {"username": current_user.username, "nombre_completo": current_user.nombre_completo, "es_admin": current_user.es_admin}


# Admin: user management
@app.get("/api/admin/usuarios", response_model=list[UsuarioOut])
def list_users(db: Session = Depends(get_db), _: Usuario = Depends(get_admin_user)):
    return db.query(Usuario).order_by(Usuario.id).all()


@app.post("/api/admin/usuarios", response_model=UsuarioOut)
def create_user(data: UsuarioCreate, db: Session = Depends(get_db), _: Usuario = Depends(get_admin_user)):
    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(400, "El usuario ya existe")
    user = Usuario(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        nombre_completo=data.nombre_completo,
        es_admin=data.es_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/api/admin/usuarios/{uid}/toggle")
def toggle_user(uid: int, db: Session = Depends(get_db), _: Usuario = Depends(get_admin_user)):
    user = db.query(Usuario).filter(Usuario.id == uid).first()
    if not user:
        raise HTTPException(404, "No encontrado")
    user.activo = not user.activo
    db.commit()
    return {"activo": user.activo}


# Search across all tables
@app.get("/api/search")
def search_all(nhc: str, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    from database import CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral
    results = []
    for Model, tipo in [
        (CirugiaColorrectal, "colorrectal"),
        (Proctologia, "proctologia"),
        (TrastornosFuncionales, "funcionales"),
        (CirugiaGeneral, "general"),
    ]:
        rows = db.query(Model).filter(Model.nhc.ilike(f"%{nhc}%")).limit(10).all()
        for r in rows:
            results.append({
                "tipo": tipo,
                "id": r.id,
                "nhc": r.nhc,
                "fecha_intervencion": r.fecha_intervencion.isoformat() if r.fecha_intervencion else None,
                "diagnostico": r.diagnostico,
                "intervencion": r.intervencion,
                "cirujano": r.cirujano,
            })
    return results


@app.get("/", response_class=HTMLResponse)
@app.get("/{path:path}", response_class=HTMLResponse)
def index(request: Request, path: str = ""):
    return templates.TemplateResponse("index.html", {"request": request})
