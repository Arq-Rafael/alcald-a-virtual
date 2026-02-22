"""
Modelos para Gestión Arbórea (Gestión del Riesgo)
"""
from app import db
from datetime import datetime, timedelta
import json

class ArbolEspecie(db.Model):
    """Catálogo de especies de árboles con datos automáticos"""
    __tablename__ = 'arbol_especie'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_comun = db.Column(db.String(100), nullable=False, unique=True, index=True)
    nombre_cientifico = db.Column(db.String(150), nullable=False)
    familia = db.Column(db.String(100))
    forma_copa = db.Column(db.String(50))  # Redonda, Piramidal, Llorona, etc.
    edad_promedio_anos = db.Column(db.Integer)  # años de vida
    altura_promedio_m = db.Column(db.Float)  # metros
    dap_promedio_cm = db.Column(db.Float)  # diámetro a la altura del pecho
    copa_promedio_m = db.Column(db.Float)  # diámetro de copa
    categoria = db.Column(db.String(20))  # Nativa, Exótica, Frutales
    coeficiente_compensacion = db.Column(db.Float, default=1.0)  # factor para cálculo
    descripcion = db.Column(db.Text)
    es_nativa = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ArbolEspecie {self.nombre_comun}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre_comun': self.nombre_comun,
            'nombre_cientifico': self.nombre_cientifico,
            'familia': self.familia,
            'forma_copa': self.forma_copa,
            'edad_promedio_anos': self.edad_promedio_anos,
            'altura_promedio_m': self.altura_promedio_m,
            'dap_promedio_cm': self.dap_promedio_cm,
            'copa_promedio_m': self.copa_promedio_m,
            'categoria': self.categoria,
            'coeficiente_compensacion': self.coeficiente_compensacion,
            'es_nativa': self.es_nativa
        }


class RadicadoArborea(db.Model):
    """Radicado de solicitud de intervención arbórea (Tala, poda, trasplante)"""
    __tablename__ = 'radicado_arborea'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_radicado = db.Column(db.String(20), unique=True, index=True)  # AR-AAAA-NNNNN
    
    # Solicitante
    solicitante_nombre = db.Column(db.String(150), nullable=False)
    solicitante_documento = db.Column(db.String(20), nullable=False)
    solicitante_contacto = db.Column(db.String(20))
    solicitante_correo = db.Column(db.String(100))
    solicitante_rol = db.Column(db.String(50))  # Propietario, Tercero, Entidad pública
    
    # Ubicación
    ubicacion_vereda_sector = db.Column(db.String(150))
    ubicacion_direccion = db.Column(db.String(200))
    ubicacion_lat = db.Column(db.Float)
    ubicacion_lng = db.Column(db.Float)
    matricula_catastral = db.Column(db.String(50))
    
    # Árbol - Datos iniciales
    arbol_especie_comun = db.Column(db.String(100))
    arbol_especie_cientifico = db.Column(db.String(150))
    arbol_especie_id = db.Column(db.Integer, db.ForeignKey('arbol_especie.id'))
    arbol_dap_cm = db.Column(db.Float)
    arbol_altura_m = db.Column(db.Float)
    arbol_copa_m = db.Column(db.Float)
    arbol_fitosanitario = db.Column(db.String(50))  # Bueno, Regular, Malo
    arbol_inclinacion_raices = db.Column(db.String(100))
    arbol_afectacion = db.Column(db.String(100))
    arbol_riesgo_inicial = db.Column(db.String(20))  # Bajo, Medio, Alto
    
    # Solicitud
    tipo_solicitud = db.Column(db.String(50), nullable=False)  # Poda, Tala, Trasplante, Emergencia
    motivo_solicitud = db.Column(db.Text)
    
    # Visita técnica
    visita_fecha = db.Column(db.DateTime)
    visita_tecnico = db.Column(db.String(150))
    visita_riesgo_final = db.Column(db.String(20))
    visita_observaciones = db.Column(db.Text)
    diagnostico_recomendaciones = db.Column(db.Text)  # NUEVO: Recomendaciones del técnico
    
    # Dictamen y permiso
    dictamen_decision = db.Column(db.String(20))  # Aprobado, Condicionado, Negado
    dictamen_motivo_negacion = db.Column(db.Text)
    permiso_vigencia_dias = db.Column(db.Integer, default=15)
    permiso_fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    permiso_fecha_limite = db.Column(db.DateTime)
    permiso_obligaciones = db.Column(db.Text)
    permiso_firmante1 = db.Column(db.String(150))
    permiso_firmante2 = db.Column(db.String(150))
    
    # Compensación
    compensacion_metodo = db.Column(db.String(50))  # Automático, Manual
    compensacion_coeficiente = db.Column(db.Float)
    compensacion_arboles_plantar = db.Column(db.Integer)
    compensacion_especie_recomendada = db.Column(db.String(100))
    compensacion_sitio = db.Column(db.Text)
    compensacion_plazo = db.Column(db.String(100))
    compensacion_calculo_json = db.Column(db.Text)  # JSON con detalles del cálculo
    
    # Archivos adjuntos (referencias)
    archivos_radicacion = db.Column(db.Text)  # JSON list de rutas
    archivos_visita = db.Column(db.Text)
    archivos_compensacion = db.Column(db.Text)
    
    # PDFs generados
    pdf_permiso = db.Column(db.String(255))  # ruta relativa
    pdf_informe = db.Column(db.String(255))
    pdf_compensacion = db.Column(db.String(255))
    pdf_completo = db.Column(db.String(255))  # informe + fotos + cálculos
    
    # Estado y auditoría
    estado = db.Column(db.String(50), default='Radicada')  # Radicada, En visita, Dictamen, Aprobada, Negada, Cerrada
    usuario_creador = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RadicadoArborea {self.numero_radicado}>'
    
    def generar_numero_radicado(self):
        """Genera número de radicado único: AR-2026-00001"""
        anio = datetime.utcnow().year
        contador = db.session.query(db.func.count(RadicadoArborea.id)).scalar() + 1
        self.numero_radicado = f"AR-{anio}-{contador:05d}"
        return self.numero_radicado
    
    def calcular_fecha_limite(self):
        """Calcula fecha límite sumando vigencia a fecha de emisión"""
        if self.permiso_vigencia_dias:
            self.permiso_fecha_limite = self.permiso_fecha_emision + timedelta(days=self.permiso_vigencia_dias)
    
    def calcular_compensacion_automatica(self):
        """Calcula automáticamente número de árboles a plantar: ceil((DAP/10)*coef)"""
        if self.arbol_dap_cm and self.compensacion_coeficiente:
            import math
            self.compensacion_arboles_plantar = max(1, math.ceil((self.arbol_dap_cm / 10) * self.compensacion_coeficiente))
            
            # Almacenar detalles del cálculo
            calculo = {
                'dap_cm': self.arbol_dap_cm,
                'coeficiente': self.compensacion_coeficiente,
                'formula': 'ceil((DAP/10)*coeficiente)',
                'resultado': self.compensacion_arboles_plantar,
                'fecha_calculo': datetime.utcnow().isoformat()
            }
            self.compensacion_calculo_json = json.dumps(calculo)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_radicado': self.numero_radicado,
            'estado': self.estado,
            # Solicitante
            'solicitante_nombre': self.solicitante_nombre,
            'solicitante_documento': self.solicitante_documento,
            'solicitante_contacto': self.solicitante_contacto,
            'solicitante_correo': self.solicitante_correo,
            'solicitante_rol': self.solicitante_rol,
            # Ubicación
            'ubicacion_direccion': self.ubicacion_direccion,
            'ubicacion_vereda_sector': self.ubicacion_vereda_sector,
            'ubicacion_lat': self.ubicacion_lat,
            'ubicacion_lng': self.ubicacion_lng,
            'matricula_catastral': self.matricula_catastral,
            # Árbol
            'arbol_especie_comun': self.arbol_especie_comun,
            'arbol_especie_cientifico': self.arbol_especie_cientifico,
            'arbol_dap_cm': self.arbol_dap_cm,
            'arbol_altura_m': self.arbol_altura_m,
            'arbol_copa_m': self.arbol_copa_m,
            'arbol_fitosanitario': self.arbol_fitosanitario,
            'arbol_inclinacion_raices': self.arbol_inclinacion_raices,
            'arbol_riesgo_inicial': self.arbol_riesgo_inicial,
            # Solicitud
            'tipo_solicitud': self.tipo_solicitud,
            'motivo_solicitud': self.motivo_solicitud,
            # Visita técnica
            'visita_fecha': self.visita_fecha.isoformat() if self.visita_fecha else None,
            'visita_tecnico': self.visita_tecnico,
            'visita_riesgo_final': self.visita_riesgo_final,
            'visita_observaciones': self.visita_observaciones,
            'diagnostico_recomendaciones': self.diagnostico_recomendaciones,
            # Dictamen y permiso
            'dictamen_decision': self.dictamen_decision,
            'dictamen_motivo_negacion': self.dictamen_motivo_negacion,
            'compensacion_metodo': self.compensacion_metodo,
            'compensacion_coeficiente': self.compensacion_coeficiente,
            'compensacion_arboles_plantar': self.compensacion_arboles_plantar,
            'compensacion_especie_recomendada': self.compensacion_especie_recomendada,
            'compensacion_sitio': self.compensacion_sitio,
            'permiso_fecha_limite': self.permiso_fecha_limite.isoformat() if self.permiso_fecha_limite else None,
            'permiso_obligaciones': self.permiso_obligaciones,
            'permiso_firmante1': self.permiso_firmante1,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
