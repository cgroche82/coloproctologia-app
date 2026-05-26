import os
import time
import secrets
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, create_tables, Usuario
from auth import (
    authenticate_user, create_access_token,
    get_current_user, get_admin_user,
    get_password_hash, verify_password,
    init_admin_user,
)
from schemas import Token, UsuarioCreate, UsuarioOut

# ── Pydantic models for password operations ───────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AdminPasswordRequest(BaseModel):
    new_password: str

class RecoveryCodeRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    code: str
    new_password: str

# ── In-memory recovery codes: {code: (username, expires_timestamp)} ───────────
_recovery_codes: dict[str, tuple[str, float]] = {}
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


# ── Change own password ──────────────────────────────────────────────────────
@app.post("/api/auth/change-password")
def change_own_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(400, "Contraseña actual incorrecta")
    if len(data.new_password) < 6:
        raise HTTPException(400, "La nueva contraseña debe tener al menos 6 caracteres")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"ok": True}


# ── Admin: change any user's password ────────────────────────────────────────
@app.patch("/api/admin/usuarios/{uid}/password")
def admin_change_password(
    uid: int,
    data: AdminPasswordRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_admin_user),
):
    user = db.query(Usuario).filter(Usuario.id == uid).first()
    if not user:
        raise HTTPException(404, "No encontrado")
    if len(data.new_password) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"ok": True, "username": user.username}


# ── Recovery: generate 6-digit code (logged server-side only) ────────────────
@app.post("/api/auth/recovery-code")
def request_recovery_code(data: RecoveryCodeRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(
        Usuario.username == data.username, Usuario.activo == True
    ).first()
    if user:
        # Invalidate any previous code for this user
        for k, (uname, _) in list(_recovery_codes.items()):
            if uname == data.username:
                del _recovery_codes[k]
        code = "".join(str(secrets.randbelow(10)) for _ in range(6))
        _recovery_codes[code] = (data.username, time.time() + 1800)
        # Code is ONLY visible in Railway server logs
        print(
            f"[RECOVERY] Código para '{data.username}': {code} (válido 30 min)",
            flush=True,
        )
    # Always return 200 — don't reveal whether the user exists
    return {"ok": True, "message": "Si el usuario existe, se ha generado un código en los logs del servidor"}


# ── Recovery: use code to reset password ─────────────────────────────────────
@app.post("/api/auth/reset-password")
def reset_password_with_code(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    code = data.code.strip()
    if not code or not data.new_password:
        raise HTTPException(400, "Código y nueva contraseña son obligatorios")
    if len(data.new_password) < 6:
        raise HTTPException(400, "La nueva contraseña debe tener al menos 6 caracteres")
    if code not in _recovery_codes:
        raise HTTPException(400, "Código inválido o ya utilizado")
    username, expires_at = _recovery_codes[code]
    if time.time() > expires_at:
        del _recovery_codes[code]
        raise HTTPException(400, "El código ha expirado. Solicita uno nuevo")
    user = db.query(Usuario).filter(
        Usuario.username == username, Usuario.activo == True
    ).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    del _recovery_codes[code]
    print(f"[RECOVERY] Contraseña de '{username}' restablecida correctamente", flush=True)
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
@app.get("/{path:path}", response_class=HTMLResponse)
def index(request: Request, path: str = ""):
    return templates.TemplateResponse("index.html", {"request": request})
