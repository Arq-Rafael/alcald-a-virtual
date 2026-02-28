"""
Modelos para el Submódulo 2: Actas CMGR
Incluye: Actas, Damnificados, Registro de Daños
"""
from app import db
from datetime import datetime
import json


class ActaCMGR(db.Model):
    """Acta del Comité Municipal de Gestión del Riesgo"""
    __tablename__ = 'acta_cmgr'

    id             = db.Column(db.Integer, primary_key=True)
    numero_acta    = db.Column(db.String(30), unique=True, index=True)   # ACTA-2026-001
    fecha          = db.Column(db.Date, nullable=False, index=True)
    tema_principal = db.Column(db.String(200))
    asistentes     = db.Column(db.Text)   # JSON list of names
    acuerdos       = db.Column(db.Text)   # Free text
    compromisos    = db.Column(db.Text)   # JSON: [{responsable,tarea,fecha_limite,estado}]
    archivo_pdf    = db.Column(db.String(255))   # ruta a PDF/DOC subido
    resumen        = db.Column(db.Text)          # resumen manual
    observaciones  = db.Column(db.Text)
    usuario_creador = db.Column(db.String(150))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def generar_numero(self):
        anio = datetime.utcnow().year
        contador = db.session.query(db.func.count(ActaCMGR.id)).scalar() + 1
        self.numero_acta = f"ACTA-{anio}-{contador:03d}"
        return self.numero_acta

    def to_dict(self):
        return {
            'id':            self.id,
            'numero_acta':   self.numero_acta,
            'fecha':         self.fecha.isoformat() if self.fecha else None,
            'tema_principal': self.tema_principal,
            'asistentes':    json.loads(self.asistentes)   if self.asistentes   else [],
            'acuerdos':      self.acuerdos,
            'compromisos':   json.loads(self.compromisos)  if self.compromisos  else [],
            'archivo_pdf':   self.archivo_pdf,
            'resumen':       self.resumen,
            'observaciones': self.observaciones,
            'usuario_creador': self.usuario_creador,
            'created_at':    self.created_at.isoformat(),
        }


class Damnificado(db.Model):
    """Registro de damnificados (ola invernal, desastre, etc.)"""
    __tablename__ = 'riesgo_damnificado'

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(150), nullable=False)
    documento       = db.Column(db.String(20))     # opcional
    contacto        = db.Column(db.String(30))
    vereda          = db.Column(db.String(100))
    tipo_afectacion = db.Column(db.String(100))    # vivienda, cultivos, salud, etc.
    descripcion     = db.Column(db.Text)
    evidencia       = db.Column(db.Text)           # JSON list of file paths
    estado_ayuda    = db.Column(db.String(50), default='Pendiente')  # Pendiente, En proceso, Atendido
    observaciones   = db.Column(db.Text)
    usuario_creador = db.Column(db.String(150))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':              self.id,
            'nombre':          self.nombre,
            'documento':       self.documento,
            'contacto':        self.contacto,
            'vereda':          self.vereda,
            'tipo_afectacion': self.tipo_afectacion,
            'descripcion':     self.descripcion,
            'estado_ayuda':    self.estado_ayuda,
            'observaciones':   self.observaciones,
            'evidencia':       json.loads(self.evidencia) if self.evidencia else [],
            'usuario_creador': self.usuario_creador,
            'created_at':      self.created_at.isoformat(),
        }


class RegistroDano(db.Model):
    """Registro de daños en infraestructura, viviendas, vías, etc."""
    __tablename__ = 'riesgo_dano'

    id              = db.Column(db.Integer, primary_key=True)
    tipo            = db.Column(db.String(50))    # Vivienda, Vía, Puente, Acueducto, Cultivos, Otro
    descripcion     = db.Column(db.Text)
    vereda          = db.Column(db.String(100))
    direccion       = db.Column(db.String(200))
    lat             = db.Column(db.Float)
    lng             = db.Column(db.Float)
    criticidad      = db.Column(db.String(20), default='Media')  # Baja, Media, Alta, Crítica
    costo_estimado  = db.Column(db.Float)
    prioridad       = db.Column(db.Integer, default=3)   # 1=alta … 5=baja
    estado          = db.Column(db.String(50), default='Reportado')  # Reportado, En atención, Resuelto
    evidencia       = db.Column(db.Text)           # JSON list of file paths
    usuario_creador = db.Column(db.String(150))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':              self.id,
            'tipo':            self.tipo,
            'descripcion':     self.descripcion,
            'vereda':          self.vereda,
            'direccion':       self.direccion,
            'lat':             self.lat,
            'lng':             self.lng,
            'criticidad':      self.criticidad,
            'costo_estimado':  self.costo_estimado,
            'prioridad':       self.prioridad,
            'estado':          self.estado,
            'evidencia':       json.loads(self.evidencia) if self.evidencia else [],
            'usuario_creador': self.usuario_creador,
            'created_at':      self.created_at.isoformat(),
        }
