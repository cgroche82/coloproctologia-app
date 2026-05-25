import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db, Usuario

SECRET_KEY = os.environ.get("SECRET_KEY", "coloproctologia_secret_key_2024_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, username: str, password: str) -> Optional[Usuario]:
    user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")
    return current_user

def init_admin_user(db: Session):
    existing = db.query(Usuario).filter(Usuario.username == "admin").first()
    if not existing:
        admin = Usuario(
            username="admin",
            hashed_password=get_password_hash("coloproct2024"),
            nombre_completo="Administrador",
            activo=True,
            es_admin=True,
        )
        db.add(admin)
        db.commit()
