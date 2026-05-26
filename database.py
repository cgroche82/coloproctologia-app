import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = os.environ.get("DB_PATH", "/app/data/coloproctologia.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Common mixin ──────────────────────────────────────────────────────────────
class CommonFields:
    id = Column(Integer, primary_key=True, index=True)
    nhc = Column(String(50), nullable=False, index=True)
    fecha_intervencion = Column(Date, nullable=False)
    fecha_nacimiento = Column(Date)
    edad = Column(Integer)
    sexo = Column(String(10))
    asa = Column(String(5))
    cirujano = Column(String(100))
    ingreso_cma = Column(String(20))
    diagnostico = Column(String(200))
    intervencion = Column(String(200))
    urgencia = Column(String(20))
    abordaje = Column(String(50))
    conversion = Column(String(5))
    tiempo_quirurgico = Column(Integer)
    clavien_dindo = Column(String(10))
    tipo_complicacion = Column(String(100))
    intervencionismo = Column(String(50))
    reintervencion = Column(String(5))
    tipo_reintervencion = Column(Text)
    mortalidad = Column(String(5))
    causa_mortalidad = Column(Text)
    fecha_alta = Column(Date)
    estancia = Column(Integer)
    reingreso_30d = Column(String(5))
    observaciones = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class CirugiaColorrectal(Base, CommonFields):
    __tablename__ = "cirugia_colorrectal"

    estoma_proteccion = Column(String(5))
    dehiscencia = Column(String(5))
    tipo_dehiscencia = Column(String(5))
    t_tnm = Column(String(10))
    n_tnm = Column(String(10))
    m_tnm = Column(String(10))
    estadio_tnm = Column(String(10))
    localizacion = Column(String(50))
    distancia_margen_anal = Column(Float)
    neoadyuvancia = Column(String(5))
    tipo_neoadyuvancia = Column(String(50))
    pcr = Column(String(5))
    tipo_histologico = Column(String(50))
    grado = Column(String(5))
    margenes_libres = Column(String(5))
    ganglios_analizados = Column(Integer)
    ganglios_positivos = Column(Integer)
    invasion_linfovascular = Column(String(5))
    invasion_perineural = Column(String(5))
    msi = Column(String(20))
    adyuvancia = Column(String(5))
    tipo_adyuvancia = Column(String(20))
    recidiva_3m = Column(String(5))
    tipo_recidiva_3m = Column(String(30))
    recidiva_6m = Column(String(5))
    tipo_recidiva_6m = Column(String(30))
    recidiva_12m = Column(String(5))
    tipo_recidiva_12m = Column(String(30))
    recidiva_18m = Column(String(5))
    tipo_recidiva_18m = Column(String(30))
    recidiva_24m = Column(String(5))
    tipo_recidiva_24m = Column(String(30))
    recidiva_36m = Column(String(5))
    tipo_recidiva_36m = Column(String(30))
    recidiva_48m = Column(String(5))
    tipo_recidiva_48m = Column(String(30))
    recidiva_60m = Column(String(5))
    tipo_recidiva_60m = Column(String(30))
    fecha_exitus = Column(Date)


class Proctologia(Base, CommonFields):
    __tablename__ = "proctologia"


class TrastornosFuncionales(Base, CommonFields):
    __tablename__ = "trastornos_funcionales"


class CirugiaGeneral(Base, CommonFields):
    __tablename__ = "cirugia_general"


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    nombre_completo = Column(String(100))
    activo = Column(Boolean, default=True)
    es_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def recreate_engine():
    """Re-initialize engine and session factory after DB file replacement (restore)."""
    global engine, SessionLocal
    engine.dispose()
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
