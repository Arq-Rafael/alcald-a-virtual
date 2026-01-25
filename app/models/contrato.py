"""
Modelo de datos para Contratos importados desde SECOP I y SECOP II
Soporta sincronización automática con datos abiertos de Colombia
"""
from app import db
from datetime import datetime
import json

class Contrato(db.Model):
    __tablename__ = 'contratos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificación del proceso
    numero_proceso = db.Column(db.String(100), unique=True, nullable=False, index=True)
    url_secop = db.Column(db.String(500))
    plataforma = db.Column(db.String(20))  # 'SECOP_I' o 'SECOP_II'
    tipo_proceso = db.Column(db.String(100))  # Licitación Pública, Concurso de Méritos, Selección Abreviada, etc.
    estado = db.Column(db.String(50), index=True)  # Publicado, Adjudicado, Celebrado, Ejecución, Liquidado, Desierto
    modalidad = db.Column(db.String(100))  # Contratación Directa, Mínima Cuantía, etc.
    
    # Entidad contratante
    entidad_nombre = db.Column(db.String(300))
    entidad_nit = db.Column(db.String(20))
    entidad_departamento = db.Column(db.String(100))
    entidad_municipio = db.Column(db.String(100))
    
    # Objeto contractual
    objeto_contrato = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    cuantia = db.Column(db.Float)
    cuantia_minima = db.Column(db.Float)  # Para SECOP II
    cuantia_maxima = db.Column(db.Float)  # Para SECOP II
    moneda = db.Column(db.String(10), default='COP')
    
    # Clasificación
    codigo_unspsc = db.Column(db.String(20))  # Código de clasificación de bienes y servicios
    familia_unspsc = db.Column(db.String(255))
    clase_unspsc = db.Column(db.String(255))
    
    # Plazos
    plazo_dias = db.Column(db.Integer)
    plazo_meses = db.Column(db.Integer)
    duracion_estimada = db.Column(db.String(100))
    
    # Fechas importantes
    fecha_publicacion = db.Column(db.DateTime)
    fecha_cierre = db.Column(db.DateTime)
    fecha_apertura_ofertas = db.Column(db.DateTime)
    fecha_adjudicacion = db.Column(db.DateTime)
    fecha_firma_contrato = db.Column(db.DateTime)
    fecha_inicio_ejecucion = db.Column(db.DateTime)
    fecha_fin_ejecucion = db.Column(db.DateTime)
    fecha_liquidacion = db.Column(db.DateTime)
    
    # Contratista (cuando está adjudicado)
    contratista_nombre = db.Column(db.String(300))
    contratista_nit = db.Column(db.String(20))
    contratista_tipo = db.Column(db.String(50))  # Persona Natural, Persona Jurídica, Consorcio, Unión Temporal
    valor_adjudicado = db.Column(db.Float)
    
    # Proponentes (JSON array)
    numero_proponentes = db.Column(db.Integer)
    proponentes_json = db.Column(db.Text)  # [{"nombre": "...", "nit": "...", "valor_propuesta": ...}]
    
    # Documentos del proceso
    tiene_pliegos = db.Column(db.Boolean, default=False)
    tiene_estudios_previos = db.Column(db.Boolean, default=False)
    tiene_acta_adjudicacion = db.Column(db.Boolean, default=False)
    documentos_json = db.Column(db.Text)  # [{"nombre": "...", "url": "...", "tipo": "..."}]
    
    # Supervisión/Interventoría
    supervisor_nombre = db.Column(db.String(255))
    interventor_nombre = db.Column(db.String(255))
    
    # Garantías
    garantia_cumplimiento = db.Column(db.String(100))
    garantia_anticipo = db.Column(db.String(100))
    garantia_calidad = db.Column(db.String(100))
    
    # Modificaciones contractuales
    numero_adiciones = db.Column(db.Integer, default=0)
    valor_total_adiciones = db.Column(db.Float, default=0)
    numero_prorrogas = db.Column(db.Integer, default=0)
    modificaciones_json = db.Column(db.Text)  # [{"tipo": "Adición", "valor": ..., "fecha": "..."}]
    
    # Pagos y ejecución presupuestal
    valor_total_pagado = db.Column(db.Float, default=0)
    porcentaje_ejecucion = db.Column(db.Float, default=0)
    ultimo_pago_fecha = db.Column(db.DateTime)
    
    # Datos completos de SECOP (backup JSON)
    datos_completos_json = db.Column(db.Text)  # JSON con toda la información extraída
    
    # Sincronización
    fecha_importacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_sincronizacion = db.Column(db.DateTime, default=datetime.utcnow)
    sincronizacion_exitosa = db.Column(db.Boolean, default=True)
    mensaje_error = db.Column(db.Text)
    
    # Seguimiento interno
    observaciones = db.Column(db.Text)  # Notas de seguimiento de la alcaldía
    responsable_seguimiento = db.Column(db.String(100))
    alerta_vencimiento = db.Column(db.Boolean, default=False)
    dias_para_vencimiento = db.Column(db.Integer)
    
    # Auditoría
    usuario_importacion = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contrato {self.numero_proceso} - {self.entidad_nombre}>'
    
    def to_dict(self):
        """Serializa el contrato a diccionario"""
        return {
            'id': str(self.id) if self.id else None,
            'numero_proceso': self.numero_proceso,
            'url_secop': self.url_secop,
            'plataforma': self.plataforma,
            'tipo_proceso': self.tipo_proceso,
            'estado': self.estado,
            'modalidad': self.modalidad,
            'entidad_nombre': self.entidad_nombre,
            'entidad_nit': self.entidad_nit,
            'entidad_municipio': self.entidad_municipio,
            'objeto_contrato': self.objeto_contrato,
            'cuantia': self.cuantia,
            'valor_adjudicado': self.valor_adjudicado,
            'moneda': self.moneda,
            'plazo_dias': self.plazo_dias,
            'fecha_publicacion': self.fecha_publicacion.isoformat() if self.fecha_publicacion else None,
            'fecha_cierre': self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            'fecha_adjudicacion': self.fecha_adjudicacion.isoformat() if self.fecha_adjudicacion else None,
            'contratista_nombre': self.contratista_nombre,
            'contratista_nit': self.contratista_nit,
            'porcentaje_ejecucion': self.porcentaje_ejecucion,
            'numero_adiciones': self.numero_adiciones,
            'valor_total_adiciones': self.valor_total_adiciones,
            'ultima_sincronizacion': self.ultima_sincronizacion.isoformat() if self.ultima_sincronizacion else None,
            'created_at': self.created_at.isoformat()
        }
    
    def parse_json_fields(self):
        """Parsea los campos JSON para fácil acceso"""
        result = {}
        try:
            result['proponentes'] = json.loads(self.proponentes_json) if self.proponentes_json else []
        except:
            result['proponentes'] = []
        
        try:
            result['documentos'] = json.loads(self.documentos_json) if self.documentos_json else []
        except:
            result['documentos'] = []
        
        try:
            result['modificaciones'] = json.loads(self.modificaciones_json) if self.modificaciones_json else []
        except:
            result['modificaciones'] = []
        
        try:
            result['datos_completos'] = json.loads(self.datos_completos_json) if self.datos_completos_json else {}
        except:
            result['datos_completos'] = {}
        
        return result
    
    @staticmethod
    def detectar_plataforma(url):
        """Detecta si la URL es de SECOP I o SECOP II"""
        if 'contratos.gov.co' in url:
            return 'SECOP_I'
        elif 'community.secop.gov.co' in url or 'colombiacompra.gov.co' in url:
            return 'SECOP_II'
        return None
    
    @staticmethod
    def extraer_id_proceso(url):
        """Extrae el ID del proceso de la URL"""
        import re
        
        # SECOP I: numConstancia=XX-XXXXXX
        if 'numConstancia=' in url:
            match = re.search(r'numConstancia=([^&]+)', url)
            if match:
                return match.group(1)
        
        # SECOP II: noticeUID=CO1.NTC.XXXXXX o CO1.NTC.XXXXXX-X
        if 'noticeUID=' in url:
            match = re.search(r'noticeUID=([^&]+)', url)
            if match:
                return match.group(1)
        
        # Si es solo el ID sin URL completa
        if url.startswith('CO1.'):
            return url
        
        return None
    
    def calcular_dias_vencimiento(self):
        """Calcula los días restantes para el vencimiento del contrato"""
        if self.fecha_fin_ejecucion:
            delta = self.fecha_fin_ejecucion - datetime.now()
            self.dias_para_vencimiento = delta.days
            self.alerta_vencimiento = delta.days <= 30 and delta.days >= 0
            return delta.days
        return None
    
    def actualizar_estado_segun_fechas(self):
        """Actualiza el estado del contrato según las fechas"""
        hoy = datetime.now()
        
        if self.fecha_liquidacion:
            self.estado = 'Liquidado'
        elif self.fecha_fin_ejecucion and hoy > self.fecha_fin_ejecucion:
            self.estado = 'Terminado'
        elif self.fecha_inicio_ejecucion and hoy >= self.fecha_inicio_ejecucion:
            self.estado = 'Ejecución'
        elif self.fecha_adjudicacion:
            self.estado = 'Adjudicado'
        elif self.fecha_cierre and hoy > self.fecha_cierre:
            self.estado = 'Cerrado'
        else:
            self.estado = 'Publicado'
