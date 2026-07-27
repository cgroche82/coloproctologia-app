"""
Siembra inicial de los catálogos.

Traslada a la base de datos las listas que hasta ahora estaban escritas a fuego
en static/js/app.js y templates/index.html. Sólo actúa si el catálogo está
vacío, así que es seguro llamarlo en cada arranque: nunca pisa lo que el
administrador haya editado desde Ajustes.
"""

from sqlalchemy.orm import Session
from database import TipoCirugia, Diagnostico, Intervencion, Cirujano

# ── Tipos de cirugía ─────────────────────────────────────────────────────────
TIPOS = [
    # slug, nombre, color, tiene_oncologico
    ("colorrectal",  "Cirugía Colorrectal",     "#1565C0", True),
    ("proctologia",  "Proctología",             "#2E7D32", False),
    ("funcionales",  "Trastornos Funcionales",  "#6A1B9A", False),
    ("general",      "Cirugía General",         "#E65100", False),
]

# ── Diagnósticos por tipo ────────────────────────────────────────────────────
DIAGNOSTICOS = {
    "colorrectal": [
        "Neoplasia de Colon Derecho", "Neoplasia de Colon Transverso",
        "Neoplasia de Colon Izquierdo", "Neoplasia de Sigma",
        "Neoplasia de Recto", "Neoplasia de Ano",
        "Neoplasia de Intestino Delgado", "Diverticulitis",
        "Enfermedad Inflamatoria Intestinal", "Colitis Isquémica",
        "Colostomía", "Ileostomía",
    ],
    "proctologia": [
        "Fístula Perianal", "Fístula Sacrococcígea", "Absceso Perianal",
        "Hemorroides", "Fisura Anal", "Crohn Perianal", "Prolapso Rectal",
        "Cuerpo Extraño Anorrectal", "Condilomas Anales",
        "Gangrena de Fournier",
    ],
    "funcionales": ["Incontinencia Fecal", "Rectocele"],
    "general": [
        "Hernia Inguinal", "Hernia Umbilical", "Eventración", "Colelitiasis",
        "Colecistitis", "Obstrucción Intestinal",
        "Perforación Gastroduodenal", "Apendicitis", "Hernia Paraostomal",
    ],
}

# Todas las patologías colorrectales comparten hoy el mismo repertorio
_RESECCIONES = [
    "Resección Intestino Delgado", "Resección Ileocecal",
    "Hemicolectomía Derecha", "Hemicolectomía Derecha Ampliada",
    "Resección Segmentaria Ángulo Esplénico", "Hemicolectomía Izquierda",
    "Sigmoidectomía", "Colectomía Subtotal", "Colectomía Total",
    "Panproctocolectomía", "Resección Anterior + EPM",
    "Resección Anterior + ETM", "Amputación Abdominoperineal", "Hartmann",
    "Resección Endoanal", "TAMIS", "Estoma Derivativo",
    "Reconstrucción de Tránsito", "Cierre de Ileostomía",
]
_FISTULA = [
    "Fistulotomía", "Fistulectomía", "Drenaje + Setón", "Colgajo de Avance",
    "LIFT", "TROPIS", "Esfinteroplastia", "Láser",
]

# ── Intervenciones por diagnóstico ───────────────────────────────────────────
INTERVENCIONES = {
    **{d: _RESECCIONES for d in DIAGNOSTICOS["colorrectal"]},
    "Fístula Perianal": _FISTULA,
    "Crohn Perianal": _FISTULA,
    "Hemorroides": ["Milligan-Morgan", "Láser", "Desarterialización Doppler"],
    "Absceso Perianal": ["Drenaje Simple", "Drenaje + Setón"],
    "Fisura Anal": ["Esfinterotomía Lateral Interna", "Toxina Botulínica"],
    "Fístula Sacrococcígea": [
        "Exéresis + Cierre Primario", "Exéresis", "Marsupialización",
        "Colgajo Cutáneo", "Láser",
    ],
    "Prolapso Rectal": [
        "Rectopexia Ventral", "Rectopexia + Sigmoidectomía", "Delorme",
        "Altemeier",
    ],
    "Cuerpo Extraño Anorrectal": ["Extracción", "Extracción + Estoma"],
    "Condilomas Anales": ["Exéresis"],
    "Gangrena de Fournier": ["Drenaje + Necrosectomía"],
    "Incontinencia Fecal": [
        "NMIS Primer Tiempo", "NMIS Segundo Tiempo", "Esfinteroplastia",
    ],
    "Rectocele": [
        "Reparación Transanal", "Reparación Perineal", "Rectopexia",
    ],
    "Hernia Inguinal": ["Hernioplastia", "Herniorrafia", "TAPP", "TEP"],
    "Hernia Umbilical": ["Hernioplastia", "Herniorrafia"],
    "Eventración": ["Eventroplastia"],
    "Colelitiasis": ["Colecistectomía"],
    "Colecistitis": ["Colecistectomía", "Colecistostomía", "Conservador"],
    "Obstrucción Intestinal": [
        "Adhesiolisis", "Resección Intestinal", "Conservador",
    ],
    "Perforación Gastroduodenal": [
        "Sutura", "Gastrectomía", "Exclusión Duodenal",
    ],
    "Apendicitis": ["Apendicectomía", "Conservador"],
    "Hernia Paraostomal": ["Sugarbaker", "Keyhole", "Pauli", "Eventroplastia"],
}

# ── Cirujanos ────────────────────────────────────────────────────────────────
CIRUJANOS = [
    "DR. MARTÍNEZ", "DR. GRACIA", "DRA. SÁNCHEZ", "DR. SAUDÍ", "DRA. PÉREZ",
    "DR. LAGUNAS", "DRA. GASCÓN", "DRA. SANTERO", "DRA. MATUTE",
    "DRA. MORENO", "DRA. GIMÉNEZ", "DRA. DE MIGUEL",
]


def seed_catalogos(db: Session) -> dict:
    """Siembra sólo lo que falte. Devuelve un recuento de lo insertado."""
    creados = {"tipos": 0, "diagnosticos": 0, "intervenciones": 0, "cirujanos": 0}

    # Tipos
    tipos_por_slug = {}
    for orden, (slug, nombre, color, onco) in enumerate(TIPOS):
        tipo = db.query(TipoCirugia).filter(TipoCirugia.slug == slug).first()
        if not tipo:
            tipo = TipoCirugia(
                slug=slug, nombre=nombre, color=color,
                tiene_oncologico=onco, orden=orden, activo=True,
            )
            db.add(tipo)
            db.flush()
            creados["tipos"] += 1
        tipos_por_slug[slug] = tipo

    # Diagnósticos
    diags_por_nombre = {}
    for slug, nombres in DIAGNOSTICOS.items():
        tipo = tipos_por_slug[slug]
        for orden, nombre in enumerate(nombres):
            diag = db.query(Diagnostico).filter(
                Diagnostico.nombre == nombre, Diagnostico.tipo_id == tipo.id
            ).first()
            if not diag:
                diag = Diagnostico(
                    nombre=nombre, tipo_id=tipo.id, orden=orden, activo=True,
                    # Criterio que usaba el código antiguo, ahora explícito y
                    # editable desde Ajustes
                    es_oncologico=nombre.startswith("Neoplasia"),
                )
                db.add(diag)
                db.flush()
                creados["diagnosticos"] += 1
            diags_por_nombre[nombre] = diag

    # Intervenciones
    for nombre_diag, intervs in INTERVENCIONES.items():
        diag = diags_por_nombre.get(nombre_diag)
        if not diag:
            continue
        for orden, nombre in enumerate(intervs):
            existe = db.query(Intervencion).filter(
                Intervencion.nombre == nombre,
                Intervencion.diagnostico_id == diag.id,
            ).first()
            if not existe:
                db.add(Intervencion(
                    nombre=nombre, diagnostico_id=diag.id,
                    orden=orden, activo=True,
                ))
                creados["intervenciones"] += 1

    # Cirujanos
    for orden, nombre in enumerate(CIRUJANOS):
        if not db.query(Cirujano).filter(Cirujano.nombre == nombre).first():
            db.add(Cirujano(nombre=nombre, orden=orden, activo=True))
            creados["cirujanos"] += 1

    db.commit()
    return creados
