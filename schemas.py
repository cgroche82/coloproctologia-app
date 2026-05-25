from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class CommonBase(BaseModel):
    nhc: str
    fecha_intervencion: date
    fecha_nacimiento: Optional[date] = None
    edad: Optional[int] = None
    sexo: Optional[str] = None
    asa: Optional[str] = None
    cirujano: Optional[str] = None
    ingreso_cma: Optional[str] = None
    diagnostico: Optional[str] = None
    intervencion: Optional[str] = None
    urgencia: Optional[str] = None
    abordaje: Optional[str] = None
    conversion: Optional[str] = None
    tiempo_quirurgico: Optional[int] = None
    clavien_dindo: Optional[str] = None
    tipo_complicacion: Optional[str] = None
    intervencionismo: Optional[str] = None
    reintervencion: Optional[str] = None
    tipo_reintervencion: Optional[str] = None
    mortalidad: Optional[str] = None
    causa_mortalidad: Optional[str] = None
    fecha_alta: Optional[date] = None
    estancia: Optional[int] = None
    reingreso_30d: Optional[str] = None
    observaciones: Optional[str] = None


class ColorrectalCreate(CommonBase):
    estoma_proteccion: Optional[str] = None
    dehiscencia: Optional[str] = None
    tipo_dehiscencia: Optional[str] = None
    t_tnm: Optional[str] = None
    n_tnm: Optional[str] = None
    m_tnm: Optional[str] = None
    estadio_tnm: Optional[str] = None
    localizacion: Optional[str] = None
    distancia_margen_anal: Optional[float] = None
    neoadyuvancia: Optional[str] = None
    tipo_neoadyuvancia: Optional[str] = None
    pcr: Optional[str] = None
    tipo_histologico: Optional[str] = None
    grado: Optional[str] = None
    margenes_libres: Optional[str] = None
    ganglios_analizados: Optional[int] = None
    ganglios_positivos: Optional[int] = None
    invasion_linfovascular: Optional[str] = None
    invasion_perineural: Optional[str] = None
    msi: Optional[str] = None
    adyuvancia: Optional[str] = None
    tipo_adyuvancia: Optional[str] = None
    recidiva_3m: Optional[str] = None
    tipo_recidiva_3m: Optional[str] = None
    recidiva_6m: Optional[str] = None
    tipo_recidiva_6m: Optional[str] = None
    recidiva_12m: Optional[str] = None
    tipo_recidiva_12m: Optional[str] = None
    recidiva_18m: Optional[str] = None
    tipo_recidiva_18m: Optional[str] = None
    recidiva_24m: Optional[str] = None
    tipo_recidiva_24m: Optional[str] = None
    recidiva_36m: Optional[str] = None
    tipo_recidiva_36m: Optional[str] = None
    recidiva_48m: Optional[str] = None
    tipo_recidiva_48m: Optional[str] = None
    recidiva_60m: Optional[str] = None
    tipo_recidiva_60m: Optional[str] = None
    fecha_exitus: Optional[date] = None


class ColorrectalOut(ColorrectalCreate):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProctologiaCreate(CommonBase):
    pass


class ProctologiaOut(ProctologiaCreate):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FuncionalesCreate(CommonBase):
    pass


class FuncionalesOut(FuncionalesCreate):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GeneralCreate(CommonBase):
    pass


class GeneralOut(GeneralCreate):
    id: int
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre_completo: Optional[str] = None
    es_admin: bool = False


class UsuarioOut(BaseModel):
    id: int
    username: str
    nombre_completo: Optional[str] = None
    activo: bool
    es_admin: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    nombre_completo: Optional[str]
    es_admin: bool
