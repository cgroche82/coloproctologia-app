"""
Migración de las cuatro tablas por tipo a la tabla única `registros`.

Se ejecuta sola al arrancar. Es idempotente: si `registros` ya tiene filas o
las tablas antiguas están vacías, no hace nada.

Las tablas antiguas NO se borran. Ocupan poco y son la red de seguridad si
algo saliera mal en el traspaso.
"""

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from database import (
    engine, Registro, TipoCirugia,
    CirugiaColorrectal, Proctologia, TrastornosFuncionales, CirugiaGeneral,
)

# Los cuatro tipos antiguos repartidos entre los siete grupos nuevos.
# Lo colorrectal se manda a Neoplasias por ser el destino más frecuente con
# diferencia; al no distinguirse el grupo en el esquema viejo, cualquier caso
# que fuese benigno habrá que reasignarlo desde la app.
ORIGEN_A_GRUPO = {
    CirugiaColorrectal:   "neoplasias",
    Proctologia:          "proctologia",
    TrastornosFuncionales: "neuromodulacion",
    CirugiaGeneral:       "general",
}

# Campos que no se copian: el id se reasigna y tipo_id se calcula
_EXCLUIR = {"id", "tipo_id", "tipo"}


def _existe(nombre: str) -> bool:
    return nombre in inspect(engine).get_table_names()


def migrar(db: Session) -> dict:
    """Devuelve un recuento por tabla de origen. Vacío si no había nada que hacer."""
    movidos: dict[str, int] = {}

    if db.query(Registro).count() > 0:
        return movidos  # ya migrado

    columnas_destino = {c.key for c in Registro.__table__.columns} - _EXCLUIR

    for Modelo, slug in ORIGEN_A_GRUPO.items():
        if not _existe(Modelo.__tablename__):
            continue
        filas = db.query(Modelo).all()
        if not filas:
            continue

        tipo = db.query(TipoCirugia).filter(TipoCirugia.slug == slug).first()
        if not tipo:
            raise RuntimeError(
                f"No existe el tipo '{slug}'; siembra los catálogos antes de migrar"
            )

        for fila in filas:
            datos = {
                col: getattr(fila, col)
                for col in columnas_destino
                if hasattr(fila, col)
            }
            db.add(Registro(tipo_id=tipo.id, **datos))
        movidos[Modelo.__tablename__] = len(filas)

    if movidos:
        db.commit()
    return movidos
