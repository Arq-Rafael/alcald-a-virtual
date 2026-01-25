"""
Funciones auxiliares para el API de Contingencia
Incluye caché ligera in-memory para plantillas y datos estáticos.
"""

# Cache simple en memoria para datos estáticos
_CACHE = {
    'datos_supata': None,
    'plantillas': {}
}

def obtener_descripcion_base(tipo_evento):
    """Retorna descripción base según tipo de evento"""
    descripciones = {
        'Lluvias': 'Este plan establece los procedimientos para atender una emergencia causada por lluvias intensas o prolongadas que pueden ocasionar deslizamientos, inundaciones y afectaciones a la población. El plan detalla la estructura de respuesta, recursos disponibles y protocolos de activación.',
        'Incendios': 'Este plan define las acciones para responder ante incendios forestales o urbanos que representen un riesgo inminente para la población. Incluye protocolos de evacuación, coordinación interinstitucional y acciones de prevención.',
        'Eventos_masivos': 'Este plan establece medidas de seguridad y atención para eventos de concentración de público, asegurando la disponibilidad de recursos sanitarios, de seguridad y comunicaciones.',
        'Deslizamientos': 'Este plan describe las acciones para prevenir y responder ante deslizamientos de tierra que pongan en riesgo a la población. Incluye identificación de zonas de riesgo, evacuación y asistencia humanitaria.',
        'Sequia': 'Este plan establece estrategias para atender una emergencia por sequía prolongada, incluyendo acciones de racionamiento de agua, protección de cultivos y asistencia a población vulnerable.',
        'Epidemias': 'Este plan detalla las medidas de contención y atención médica ante una epidemia o brote de enfermedad transmisible, incluyendo aislamiento, vigilancia epidemiológica y coordinación sanitaria.',
    }
    return descripciones.get(tipo_evento, 'Descripción del evento y su impacto potencial.')


def obtener_antecedentes(tipo_evento):
    """Retorna antecedentes sugeridos según tipo de evento"""
    antecedentes = {
        'Lluvias': 'Registre aquí eventos previos de lluvias intensas, inundaciones o deslizamientos causados por lluvia en el municipio, incluyendo fechas, impactos y lecciones aprendidas.',
        'Incendios': 'Describa incendios previos en la zona, sus causas, daños ocasionados y medidas que resultaron efectivas en su control.',
        'Eventos_masivos': 'Mencione eventos públicos previos en el municipio, aglomeramientos reportados y situaciones de seguridad presentadas.',
        'Deslizamientos': 'Identifique deslizamientos previos en zonas críticas del municipio, sus causas y la población afectada.',
        'Sequia': 'Registre períodos de sequía previos, su duración, impacto en agricultura y disponibilidad de agua.',
        'Epidemias': 'Mencione brotes previos en el municipio, enfermedades vigiladas y acciones de salud pública implementadas.',
    }
    return antecedentes.get(tipo_evento, 'Describa eventos históricos relevantes.')


def get_datos_supata():
    """Datos básicos del municipio de Supatá para auto-completar formularios oficiales."""
    if _CACHE['datos_supata']:
        return _CACHE['datos_supata']

    _CACHE['datos_supata'] = {
        "municipio": "Supatá",
        "departamento": "Cundinamarca",
        "provincia": "Gualivá",
        "poblacion": 6428,
        "altitud": 1798,
        "area_km2": 128,
        "distancia_bogota_km": 76,
        "clima": "Templado",
        "fundacion": "13 de diciembre de 1882",
        "coordenadas": {
            "latitud": "5°03'40\"N",
            "longitud": "74°14'12\"O",
        },
        "organismos_emergencia": [
            {"nombre": "Bomberos Voluntarios de Supatá", "telefono": "119", "tipo": "bomberos"},
            {"nombre": "Policía Nacional - CAI Supatá", "telefono": "123", "tipo": "policia"},
            {"nombre": "Hospital Municipal de Supatá", "telefono": "(1) xxxx", "tipo": "salud"},
            {"nombre": "Unidad Municipal de Gestión del Riesgo (UMGRD)", "telefono": "(1) xxxx", "tipo": "gestion_riesgo"},
            {"nombre": "Cruz Roja Colombiana", "telefono": "132", "tipo": "salud"},
            {"nombre": "Defensa Civil Colombiana", "telefono": "144", "tipo": "defensa_civil"},
        ],
        "marco_normativo": {
            "ley_1523_2012": "Política Nacional de Gestión del Riesgo de Desastres",
            "decreto_2157_2017": "Directrices para planes de GRD",
            "estrategia_municipal": "Estrategia Municipal de Respuesta a Emergencias",
            "cmgrd": "Comité Municipal de Gestión del Riesgo de Desastres",
        },
    }
    return _CACHE['datos_supata']


def get_plantilla_por_tipo(tipo_evento: str, seccion: str):
    """Plantillas preconfiguradas por tipo de evento y sección."""
    tipo_evento = (tipo_evento or "").lower()
    seccion = (seccion or "").lower()

    cache_key = f"{tipo_evento}:{seccion}"
    if cache_key in _CACHE['plantillas']:
        return _CACHE['plantillas'][cache_key]

    plantillas_default = {
        "lluvias": {
            "riesgos": {
                "amenazas_naturales": ["Lluvias torrenciales", "Inundaciones rápidas", "Deslizamientos"],
                "medidas": [
                    "Monitoreo IDEAM 24/7",
                    "Drenajes despejados y señalizados",
                    "Rutas de evacuación demarcadas",
                ],
            }
        },
        "incendios": {
            "riesgos": {
                "amenazas_tecnologicas": [
                    "Incendio estructural",
                    "Explosión de gas",
                    "Cortocircuitos en escenario",
                ],
                "medidas": [
                    "Extintores ABC operativos",
                    "Personal entrenado en control inicial",
                    "Coordinación directa con Bomberos",
                ],
            }
        },
        "eventos_masivos": {
            "riesgos": {
                "amenazas_antropicas": [
                    "Estampidas por pánico",
                    "Aglomeraciones por sobrecupo",
                    "Disturbios y riñas",
                ],
                "medidas": [
                    "Control estricto de aforo",
                    "Puntos de hidratación y PMA",
                    "Seguridad privada y apoyo Policía",
                ],
            }
        },
    }

    plantilla = plantillas_default.get(tipo_evento, {}).get(seccion, {})
    _CACHE['plantillas'][cache_key] = plantilla
    return plantilla


TIPOS_EVENTOS_EXPANDED = {
    'Lluvias': {
        'icon': 'cloud-rain',
        'color': '#2563eb',
        'umbrales': {
            'verde': '0-50 mm/24h',
            'amarillo': '51-100 mm/24h',
            'naranja': '101-150 mm/24h',
            'rojo': '> 150 mm/24h'
        },
        'sectores': ['Salud', 'Logística', 'Seguridad', 'Tránsito', 'WASH', 'Comunicaciones']
    },
    'Incendios': {
        'icon': 'fire',
        'color': '#dc2626',
        'umbrales': {
            'verde': 'Índice < 15 (Bajo)',
            'amarillo': 'Índice 15-30 (Moderado)',
            'naranja': 'Índice 30-45 (Alto)',
            'rojo': 'Índice > 45 (Crítico)'
        },
        'sectores': ['Logística', 'Seguridad', 'WASH', 'Salud', 'Comunicaciones']
    },
    'Eventos_masivos': {
        'icon': 'people-fill',
        'color': '#7c3aed',
        'umbrales': {
            'verde': '< 1000 personas',
            'amarillo': '1000-5000 personas',
            'naranja': '5000-10000 personas',
            'rojo': '> 10000 personas'
        },
        'sectores': ['Seguridad', 'Salud', 'Tránsito', 'Comunicaciones', 'Logística']
    },
    'Deslizamientos': {
        'icon': 'exclamation-triangle',
        'color': '#ea580c',
        'umbrales': {
            'verde': 'Estable',
            'amarillo': 'Riesgo bajo',
            'naranja': 'Riesgo moderado',
            'rojo': 'Riesgo alto inminente'
        },
        'sectores': ['Seguridad', 'Logística', 'Salud', 'Comunicaciones']
    },
    'Sequia': {
        'icon': 'sun-fill',
        'color': '#f59e0b',
        'umbrales': {
            'verde': 'Precipitación normal',
            'amarillo': 'Déficit moderado (10-25%)',
            'naranja': 'Déficit alto (25-50%)',
            'rojo': 'Déficit crítico (> 50%)'
        },
        'sectores': ['Logística', 'Salud', 'Comunicaciones', 'Seguridad']
    },
    'Epidemias': {
        'icon': 'virus2',
        'color': '#8b5cf6',
        'umbrales': {
            'verde': 'Sin casos',
            'amarillo': 'Casos esporádicos',
            'naranja': 'Brote confirmado',
            'rojo': 'Epidemia en curso'
        },
        'sectores': ['Salud', 'Comunicaciones', 'Logística', 'Seguridad']
    }
}
