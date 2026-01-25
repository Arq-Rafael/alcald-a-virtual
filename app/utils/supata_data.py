# -*- coding: utf-8 -*-
"""
Datos automáticos del municipio de Supatá, Cundinamarca
Estos datos se cargan automáticamente en todos los planes de contingencia
"""

SUPATA_DATA = {
    # Información General
    "municipio": "Supatá",
    "departamento": "Cundinamarca",
    "provincia": "Gualivá",
    "pais": "Colombia",
    
    # Datos Demográficos
    "poblacion_total": 6428,
    "poblacion_urbana": 2533,
    "poblacion_rural": 3895,
    "densidad_poblacional": 50.22,  # hab/km²
    "gentilicio": "Supateño(a)",
    "alcalde": "Wílmar Quitián Chila",
    "periodo_alcalde": "2024-2027",
    
    # Datos Geográficos
    "altitud": 1798,  # metros sobre el nivel del mar
    "area_territorial": 128,  # km²
    "coordenadas": {
        "latitud": "5°03'40\"N",
        "longitud": "74°14'12\"O"
    },
    "distancia_bogota": 76,  # km
    "tiempo_viaje_bogota": "2-2.5 horas",
    
    # Clima
    "zona_vida": "Bosque húmedo premontano",
    "temperatura_promedio": "12-16°C",
    "temperatura_min": 8,
    "temperatura_max": 18,
    "precipitacion_anual": "1500-2500 mm",
    "patron_precipitacion": "Bimodal (dos períodos de lluvia)",
    
    # Límites Municipales
    "limites": {
        "noroeste": "Vergara (Río Negro)",
        "norte": "Límite entre Vergara y Pacho",
        "nordeste": "Pacho",
        "oeste": "Vergara",
        "este": "Límite entre Pacho y Subachoque",
        "suroeste": "La Vega",
        "sur": "San Francisco de Sales",
        "sureste": "Subachoque (Cuchilla del Tablero)"
    },
    
    # Servicios Públicos
    "servicios_publicos": {
        "energia": "Enel Colombia",
        "gas": "Alcanos de Colombia",
        "agua": "Acueducto Municipal",
        "comunicaciones": "Cobertura telefónica móvil disponible"
    },
    
    # Vías de Acceso
    "vias_acceso": [
        {
            "nombre": "Ruta Nacional 50",
            "origen": "Puente de Guadua (Bogotá - Calle 80)",
            "ruta": "San Francisco de Sales → Supatá",
            "distancia_total": "76 km",
            "tiempo_viaje": "2-2.5 horas"
        }
    ],
    
    # Organismos de Emergencia
    "organismos_emergencia": [
        {
            "nombre": "Cuerpo de Bomberos Voluntarios",
            "telefono": "119",
            "ubicacion": "Municipios cercanos (Subachoque, Facatativá)",
            "tiempo_respuesta": "15-20 minutos"
        },
        {
            "nombre": "Cruz Roja Colombiana",
            "telefono": "018005198534",
            "cobertura": "Seccional Cundinamarca",
            "servicios": "Ambulancias, Primeros Auxilios"
        },
        {
            "nombre": "Policía Nacional",
            "telefono": "123",
            "tipo": "Estación Local",
            "ubicacion": "Casco urbano de Supatá"
        },
        {
            "nombre": "Defensa Civil Colombiana",
            "cobertura": "Cundinamarca",
            "servicios": "Búsqueda y Rescate"
        }
    ],
    
    # Infraestructura de Salud
    "infraestructura_salud": [
        {
            "nombre": "Puesto de Salud Municipal",
            "tipo": "Nivel 1",
            "ubicacion": "Casco urbano",
            "servicios": "Atención básica, Primeros Auxilios"
        },
        {
            "nombre": "Hospital más cercano",
            "nombre_hospital": "Hospital de Subachoque / Hospital de Facatativá",
            "distancia": "20-30 km",
            "tiempo_traslado": "30-45 minutos"
        }
    ],
    
    # Puntos de Interés Geográfico
    "puntos_interes": [
        "Cerro El Tablazo",
        "Laguna Hispania",
        "Cuchilla del Tablero",
        "Cascadas diversas",
        "Iglesia Parroquial de San Ignacio"
    ],
    
    # Características Especiales
    "caracteristicas_especiales": {
        "fauna_unica": "Rana dorada única en el mundo (20 hectáreas)",
        "flora_notable": "Orquídeas supateñas de valor ornamental",
        "biodiversidad": "Bosque húmedo premontano - ecosistema protegido"
    },
    
    # Historia
    "historia": {
        "fundacion_municipio": "13 de diciembre de 1882",
        "decreto": "Ley 21 - Asamblea Legislativa del Estado Soberano de Cundinamarca",
        "segregacion_de": "Municipio de Subachoque",
        "creacion_parroquia": "13 de marzo de 1872",
        "nombre_parroquia": "Parroquia de San Ignacio de Loyola"
    },
    
    # Economía
    "economia": {
        "sector_predominante": "Agricultura y ganadería tradicionales",
        "poblacion_rural": "61%",
        "poblacion_urbana": "39%",
        "etnografia": "Mestiza predominante, descendientes de pobladores panche"
    }
}

# Cache liviano en memoria
_CACHE = {
    'resumen': None,
    'directorio': None
}


def get_supata_resumen():
    """Retorna un resumen general de Supatá en formato texto"""
    if _CACHE['resumen']:
        return _CACHE['resumen']

    _CACHE['resumen'] = f"""
    INFORMACIÓN GENERAL - MUNICIPIO DE SUPATÁ, CUNDINAMARCA
    
    Ubicación: {SUPATA_DATA['municipio']}, provincia de {SUPATA_DATA['provincia']}, {SUPATA_DATA['departamento']}
    Distancia desde Bogotá: {SUPATA_DATA['distancia_bogota']} km ({SUPATA_DATA['tiempo_viaje_bogota']})
    
    DATOS DEMOGRÁFICOS
    Población total: {SUPATA_DATA['poblacion_total']:,} habitantes
    - Población urbana: {SUPATA_DATA['poblacion_urbana']:,} hab
    - Población rural: {SUPATA_DATA['poblacion_rural']:,} hab
    Densidad: {SUPATA_DATA['densidad_poblacional']} hab/km²
    Gentilicio: {SUPATA_DATA['gentilicio']}
    
    GEOGRAFÍA
    Altitud: {SUPATA_DATA['altitud']} m.s.n.m.
    Área territorial: {SUPATA_DATA['area_territorial']} km²
    Coordenadas: {SUPATA_DATA['coordenadas']['latitud']}, {SUPATA_DATA['coordenadas']['longitud']}
    
    CLIMA
    Temperatura promedio: {SUPATA_DATA['temperatura_promedio']}
    Precipitación anual: {SUPATA_DATA['precipitacion_anual']}
    Zona de vida: {SUPATA_DATA['zona_vida']}
    
    ADMINISTRACIÓN
    Alcalde: {SUPATA_DATA['alcalde']}
    Período: {SUPATA_DATA['periodo_alcalde']}
    """
    return _CACHE['resumen']


def get_organismos_emergencia():
    """Retorna lista formateada de organismos de emergencia"""
    return SUPATA_DATA['organismos_emergencia']


def get_directorio_emergencias():
    """Retorna directorio completo de emergencias para el plan"""
    if _CACHE['directorio']:
        return _CACHE['directorio']

    directorio = []
    for org in SUPATA_DATA['organismos_emergencia']:
        directorio.append({
            'entidad': org['nombre'],
            'telefono': org.get('telefono', 'N/A'),
            'ubicacion': org.get('ubicacion', 'Cundinamarca'),
            'disponibilidad': '24/7'
        })
    _CACHE['directorio'] = directorio
    return directorio
