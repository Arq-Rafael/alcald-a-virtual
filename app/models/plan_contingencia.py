"""
Modelo de datos para Planes de Contingencia.
Soporta múltiples tipos de eventos (Lluvias, Incendios, Eventos masivos, etc.)
con estructura flexible para campos específicos por tipo.
"""
from app import db
from datetime import datetime, timedelta
import json

class PlanContingencia(db.Model):
    __tablename__ = 'planes_contingencia'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificación del Plan
    nombre_plan = db.Column(db.String(255), nullable=False, index=True)
    tipo_evento = db.Column(db.String(50), nullable=False, index=True)  # Lluvias, Incendios, Eventos_masivos, Deslizamientos, Sequia, Derrames
    version = db.Column(db.String(20), default='1.0')
    numero_plan = db.Column(db.String(50), unique=True, index=True)
    
    # Cobertura y ámbito
    ambito = db.Column(db.String(100))  # Municipio, Vereda, Barrio, etc.
    municipio = db.Column(db.String(100))
    area_cobertura = db.Column(db.Text)  # Descripción del área
    poblacion_objetivo = db.Column(db.Integer)  # Número de personas potencialmente afectadas
    
    # Fechas y vigencia
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vigencia_desde = db.Column(db.Date)
    vigencia_hasta = db.Column(db.Date)
    
    # Responsables
    responsable_principal = db.Column(db.String(255))
    correo_responsable = db.Column(db.String(120))
    telefono_responsable = db.Column(db.String(20))
    
    entidad_responsable = db.Column(db.String(255), default='Alcaldía Municipal')
    
    # Estado del plan
    estado = db.Column(db.String(20), default='Borrador', index=True)  # Borrador, En_revision, Emitido, Vigente, Archivado
    
    # Aprobaciones y resoluciones
    numero_resolucion = db.Column(db.String(50))
    fecha_resolucion = db.Column(db.Date)
    aprobado_por = db.Column(db.String(255))
    
    # ======== CONTENIDO ESTRUCTURADO ==========
    
    # Escenario y análisis de riesgo
    descripcion_peligro = db.Column(db.Text)  # Descripción detallada del peligro/evento
    antecedentes_historicos = db.Column(db.Text)  # Eventos previos, lecciones aprendidas
    poblacion_expuesta = db.Column(db.String(255))  # Resumen de vulnerables
    activos_expuestos = db.Column(db.Text)  # Infraestructura, servicios, bienes
    supuestos_limitaciones = db.Column(db.Text)  # Supuestos y limitaciones del plan
    puntos_criticos = db.Column(db.Text)  # JSON con puntos críticos: [{"nombre": "...", "ubicacion": "...", "riesgo": "..."}]
    
    # Umbrales y alertas (JSON flexible por tipo de evento)
    # Ejemplo: {"lluvia": [{"nivel": "verde", "mm_24h": "0-50"}, ...], "rio": [...]}
    umbrales_alertas = db.Column(db.Text)  # JSON
    
    # Sistema de alerta: cadena de notificación, canales, responsables
    sistema_alerta = db.Column(db.Text)  # JSON {"canales": ["radio", "SMS", ...], "cadena_notificacion": [...]}
    
    # Organización y roles (JSON)
    # {"estructura_comando": "...", "roles": [{"sector": "Salud", "responsable": "...", "contactos": [...]}]}
    estructura_organizativa = db.Column(db.Text)
    
    # Estrategia por fases
    fase_preparacion = db.Column(db.Text)  # JSON con acciones y checklists
    fase_alistamiento = db.Column(db.Text)
    fase_respuesta = db.Column(db.Text)  # Por sectores: Salud, Logística, Seguridad, Tránsito, WASH, Comunicaciones
    fase_rehabilitacion = db.Column(db.Text)
    
    # Logística y recursos (JSON)
    # {"equipos": [...], "vehiculos": [...], "epp": [...], "combustible": "...", "proveedores": [...]}
    inventario_recursos = db.Column(db.Text)
    puntos_acopio = db.Column(db.Text)  # JSON con ubicación, capacidad, responsable
    rutas_abastecimiento = db.Column(db.Text)  # Descripción de rutas
    
    # Albergues (si aplica)
    albergues = db.Column(db.Text)  # JSON [{"nombre": "...", "ubicacion": "...", "capacidad": ..., "servicios": [...]}]
    
    # Comunicaciones
    vocerías = db.Column(db.Text)  # JSON con voceros oficiales
    canales_comunicacion = db.Column(db.Text)  # JSON: radio, SMS, sirenas, redes sociales, perifoneo
    formatos_boletines = db.Column(db.Text)  # Descripción de formatos y frecuencia
    
    # Salud y asistencia humanitaria
    protocolos_salud = db.Column(db.Text)  # Primeros auxilios, vigilancia epidemiológica
    grupos_vulnerables = db.Column(db.Text)  # Protección de niños, adultos mayores, personas con discapacidad
    kits_humanitarios = db.Column(db.Text)  # JSON con contenido y ubicación
    
    # Presupuesto
    presupuesto_total = db.Column(db.Float)  # Estimado en pesos
    presupuesto_por_fase = db.Column(db.Text)  # JSON {"preparacion": ..., "respuesta": ..., ...}
    fuentes_financiamiento = db.Column(db.Text)
    
    # Coordinación interinstitucional
    instituciones_participantes = db.Column(db.Text)  # JSON con enlaces y contactos
    
    # Seguimiento y mejora continua
    indicadores_activacion = db.Column(db.Text)
    cronograma_simulacros = db.Column(db.Text)
    lecciones_aprendidas = db.Column(db.Text)
    
    # ======== MULTIMEDIA Y ANEXOS ==========
    
    # Almacenamiento de rutas de archivos adjuntos (JSON)
    # {"mapas": [...], "imagenes": [...], "formularios": [...], "inventarios": [...]}
    archivos_anexos = db.Column(db.Text)
    
    # Almacenamiento de imágenes/mapas incrustados en el plan (JSON)
    # {"seccion_riesgo": "ruta/imagen.jpg", "mapas_evacuacion": "ruta/mapa.png", ...}
    multimedia_embed = db.Column(db.Text)
    
    # Auditoría
    usuario_creador = db.Column(db.String(120), default='Sistema')
    usuario_modificador = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<PlanContingencia {self.numero_plan} - {self.tipo_evento}>'
    
    def generar_numero_plan(self):
        """Genera número único del plan: PC-2026-00001"""
        anio = datetime.utcnow().year
        contador = db.session.query(db.func.count(PlanContingencia.id)).scalar() + 1
        self.numero_plan = f"PC-{anio}-{contador:05d}"
    
    def to_dict(self):
        """Serializa el plan a diccionario"""
        return {
            'id': self.id,
            'nombre_plan': self.nombre_plan,
            'tipo_evento': self.tipo_evento,
            'numero_plan': self.numero_plan,
            'version': self.version,
            'ambito': self.ambito,
            'municipio': self.municipio,
            'poblacion_objetivo': self.poblacion_objetivo,
            'responsable_principal': self.responsable_principal,
            'estado': self.estado,
            'fecha_emision': self.fecha_emision.isoformat() if self.fecha_emision else None,
            'vigencia_desde': self.vigencia_desde.isoformat() if self.vigencia_desde else None,
            'vigencia_hasta': self.vigencia_hasta.isoformat() if self.vigencia_hasta else None,
            'numero_resolucion': self.numero_resolucion,
            'created_at': self.created_at.isoformat()
        }
    
    def parse_json_fields(self):
        """Parsea los campos JSON para fácil acceso"""
        result = {}
        json_fields = [
            'puntos_criticos', 'umbrales_alertas', 'sistema_alerta', 
            'estructura_organizativa', 'fase_preparacion', 'fase_alistamiento',
            'fase_respuesta', 'fase_rehabilitacion', 'inventario_recursos',
            'puntos_acopio', 'albergues', 'vocerías', 'canales_comunicacion',
            'protocolos_salud', 'grupos_vulnerables', 'kits_humanitarios',
            'presupuesto_por_fase', 'instituciones_participantes', 
            'archivos_anexos', 'multimedia_embed'
        ]
        for field in json_fields:
            try:
                val = getattr(self, field)
                result[field] = json.loads(val) if val else {}
            except:
                result[field] = {}
        return result
