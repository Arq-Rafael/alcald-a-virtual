# -*- coding: utf-8 -*-
"""
Modelo actualizado para Planes de Contingencia
Estructura según normas APPA y Ley 1523 de 2012
"""
from app import db
from datetime import datetime
import json

class PlanContingenciaV2(db.Model):
    __tablename__ = 'planes_contingencia_v2'
    
    # CAMPOS PRINCIPALES
    id = db.Column(db.Integer, primary_key=True)
    numero_plan = db.Column(db.String(50), unique=True, nullable=False)
    nombre_plan = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.String(50), default='BORRADOR')  # BORRADOR, EN_REVISIÓN, APROBADO, APROBADO_COMITÉ
    tipo_evento = db.Column(db.String(100))  # Lluvia, Incendio, Eventos Masivos, etc.
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.String(10), default='1.0')
    
    # SECCIÓN 1: INTRODUCCIÓN
    introduccion_descripcion = db.Column(db.Text)  # Descripción del evento
    introduccion_justificacion = db.Column(db.Text)  # Justificación del plan
    introduccion_contexto = db.Column(db.Text)  # Contexto general
    
    # SECCIÓN 2: OBJETIVOS Y ALCANCE
    objetivo_general = db.Column(db.Text)
    objetivos_especificos = db.Column(db.JSON)  # Lista de objetivos
    alcance_evento = db.Column(db.Text)  # A qué evento aplica
    alcance_ubicacion = db.Column(db.Text)  # Ubicación física
    alcance_duracion = db.Column(db.String(255))  # Fechas y duración
    alcance_aforo = db.Column(db.Integer)  # Número de asistentes esperados
    
    # SECCIÓN 3: MARCO NORMATIVO
    marco_normativo = db.Column(db.JSON)  # Lista de normas aplicables
    
    # SECCIÓN 4: ORGANIZACIÓN Y ROLES
    estructura_organizativa = db.Column(db.JSON)  # Tabla de coordinadores y roles
    pmu_ubicacion = db.Column(db.String(255))  # Ubicación del Puesto de Mando Unificado
    organismos_apoyo = db.Column(db.JSON)  # Lista de organismos externos
    directorio_contactos = db.Column(db.JSON)  # Directorio de emergencias
    
    # SECCIÓN 5: AMENAZAS Y ANÁLISIS DE RIESGOS
    descripcion_escenario = db.Column(db.Text)  # Características del evento
    amenazas_identificadas = db.Column(db.JSON)  # Lista de amenazas
    matriz_riesgos = db.Column(db.JSON)  # Tabla de matriz de riesgos
    vulnerabilidades = db.Column(db.JSON)  # Análisis de vulnerabilidades
    escenarios_priorizados = db.Column(db.JSON)  # Escenarios críticos
    
    # SECCIÓN 6: MEDIDAS DE REDUCCIÓN
    medidas_seguridad = db.Column(db.JSON)  # Medidas de seguridad específicas
    adecuacion_lugar = db.Column(db.JSON)  # Adecuaciones del sitio
    medidas_sanitarias = db.Column(db.JSON)  # Medidas sanitarias
    plan_vigilancia = db.Column(db.Text)  # Plan de seguridad y vigilancia
    capacitacion_personal = db.Column(db.Text)  # Capacitación prevista
    seguros_contingencias = db.Column(db.Text)  # Pólizas de seguro
    
    # SECCIÓN 7: PLAN DE RESPUESTA
    niveles_alerta = db.Column(db.JSON)  # Verde, Amarilla, Naranja, Roja
    procedimiento_general = db.Column(db.Text)  # Protocolo general de respuesta
    protocolos_especificos = db.Column(db.JSON)  # Protocolos por escenario
    rutas_evacuacion = db.Column(db.JSON)  # Rutas y salidas
    puntos_encuentro = db.Column(db.JSON)  # Puntos de reunión
    capacidad_rutas = db.Column(db.Text)  # Tiempos de evacuación
    recursos_disponibles = db.Column(db.JSON)  # Inventario de recursos
    equipo_primeros_auxilios = db.Column(db.JSON)  # Equipos médicos disponibles
    ambulancias = db.Column(db.JSON)  # Ambulancias de apoyo
    comunicaciones_plan = db.Column(db.JSON)  # Canales de comunicación
    estrategia_recuperacion = db.Column(db.Text)  # Recuperación post-emergencia
    
    # SECCIÓN 8: ACTUALIZACIÓN Y MEJORA
    responsable_actualizacion = db.Column(db.String(255))
    frecuencia_actualizacion = db.Column(db.String(100))
    simulacros_realizados = db.Column(db.JSON)  # Historial de simulacros
    
    # SECCIÓN 9: ANEXOS Y DOCUMENTOS
    documentos_adjuntos = db.Column(db.JSON)  # Referencias a archivos
    planos_adjuntos = db.Column(db.JSON)  # Ubicación de planos
    
    # DATOS AUTOMÁTICOS DE SUPATÁ (pre-cargados)
    municipio = db.Column(db.String(100), default='Supatá')
    departamento = db.Column(db.String(100), default='Cundinamarca')
    poblacion_municipio = db.Column(db.Integer, default=6428)
    altitud_municipio = db.Column(db.Integer, default=1798)
    clima_municipio = db.Column(db.String(255), default='Bosque húmedo premontano')
    
    # METADATOS
    creado_por = db.Column(db.String(255))
    ultima_modificacion_por = db.Column(db.String(255))
    observaciones = db.Column(db.Text)
    
    def __repr__(self):
        return f'<PlanContingenciaV2 {self.numero_plan}>'
    
    def to_dict(self):
        """Convertir objeto a diccionario"""
        return {
            'id': self.id,
            'numero_plan': self.numero_plan,
            'nombre_plan': self.nombre_plan,
            'estado': self.estado,
            'tipo_evento': self.tipo_evento,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'version': self.version,
            'municipio': self.municipio,
            'departamento': self.departamento
        }
    
    def obtener_progreso(self):
        """Calcula el porcentaje de completud del plan"""
        campos = [
            self.introduccion_descripcion,
            self.objetivo_general,
            self.alcance_evento,
            self.marco_normativo,
            self.estructura_organizativa,
            self.amenazas_identificadas,
            self.medidas_seguridad,
            self.procedimiento_general,
            self.rutas_evacuacion
        ]
        completados = sum(1 for campo in campos if campo)
        return (completados / len(campos)) * 100 if campos else 0
