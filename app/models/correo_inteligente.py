"""
Modelos de Correo Inteligente Institucional.
"""

from datetime import datetime
import json
from app import db


class CorreoInstitucionalCuenta(db.Model):
    __tablename__ = 'correo_institucional_cuentas'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    email_institucional = db.Column(db.String(180), nullable=False, index=True)
    proveedor = db.Column(db.String(30), default='gmail', nullable=False)

    # Se almacena cifrado (JSON del token OAuth)
    token_encriptado = db.Column(db.Text, nullable=True)
    scopes = db.Column(db.Text, nullable=True)

    conectada = db.Column(db.Boolean, default=False, nullable=False)
    ultima_sincronizacion = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(30), default='desconectada', nullable=False)
    mensaje_estado = db.Column(db.String(250), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    mensajes = db.relationship(
        'CorreoInstitucionalMensaje',
        backref='cuenta',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def get_scopes(self):
        if not self.scopes:
            return []
        try:
            return json.loads(self.scopes)
        except Exception:
            return []

    def set_scopes(self, scopes_list):
        self.scopes = json.dumps(scopes_list or [])


class CorreoInstitucionalMensaje(db.Model):
    __tablename__ = 'correo_institucional_mensajes'

    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('correo_institucional_cuentas.id'), nullable=False, index=True)

    gmail_message_id = db.Column(db.String(140), unique=True, nullable=False, index=True)
    gmail_thread_id = db.Column(db.String(140), nullable=True, index=True)

    remitente = db.Column(db.String(255), nullable=True)
    remitente_email = db.Column(db.String(180), nullable=True, index=True)
    destinatarios = db.Column(db.Text, nullable=True)
    cc = db.Column(db.Text, nullable=True)

    asunto = db.Column(db.String(500), nullable=True, index=True)
    snippet = db.Column(db.Text, nullable=True)
    cuerpo_texto = db.Column(db.Text, nullable=True)

    fecha_recepcion = db.Column(db.DateTime, nullable=False, index=True)
    tiene_adjuntos = db.Column(db.Boolean, default=False, nullable=False)
    adjuntos_json = db.Column(db.Text, nullable=True)

    estado = db.Column(db.String(30), default='nuevo', nullable=False, index=True)
    categoria = db.Column(db.String(60), default='otro', nullable=False, index=True)
    prioridad = db.Column(db.String(20), default='media', nullable=False, index=True)
    requiere_respuesta = db.Column(db.Boolean, default=True, nullable=False, index=True)

    urgencia = db.Column(db.String(20), default='media', nullable=False)
    tema_principal = db.Column(db.String(200), nullable=True)
    resumen_ejecutivo = db.Column(db.Text, nullable=True)
    recomendacion_gestion = db.Column(db.Text, nullable=True)

    semaforo = db.Column(db.String(20), default='gris', nullable=False, index=True)
    dias_transcurridos = db.Column(db.Integer, default=0, nullable=False)
    riesgo_vencimiento = db.Column(db.String(30), default='bajo', nullable=False)

    analizado_at = db.Column(db.DateTime, nullable=True)
    respondido_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    borradores = db.relationship(
        'CorreoInstitucionalBorrador',
        backref='mensaje',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def set_adjuntos(self, adjuntos):
        self.adjuntos_json = json.dumps(adjuntos or [], ensure_ascii=False)

    def get_adjuntos(self):
        if not self.adjuntos_json:
            return []
        try:
            return json.loads(self.adjuntos_json)
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'gmail_message_id': self.gmail_message_id,
            'thread_id': self.gmail_thread_id,
            'remitente': self.remitente,
            'remitente_email': self.remitente_email,
            'asunto': self.asunto,
            'snippet': self.snippet,
            'fecha_recepcion': self.fecha_recepcion.isoformat() if self.fecha_recepcion else None,
            'estado': self.estado,
            'categoria': self.categoria,
            'prioridad': self.prioridad,
            'requiere_respuesta': self.requiere_respuesta,
            'urgencia': self.urgencia,
            'tema_principal': self.tema_principal,
            'resumen_ejecutivo': self.resumen_ejecutivo,
            'recomendacion_gestion': self.recomendacion_gestion,
            'semaforo': self.semaforo,
            'dias_transcurridos': self.dias_transcurridos,
            'riesgo_vencimiento': self.riesgo_vencimiento,
            'tiene_adjuntos': self.tiene_adjuntos,
            'adjuntos': self.get_adjuntos(),
            'cuerpo_texto': self.cuerpo_texto,
        }


class CorreoInstitucionalBorrador(db.Model):
    __tablename__ = 'correo_institucional_borradores'

    id = db.Column(db.Integer, primary_key=True)
    mensaje_id = db.Column(db.Integer, db.ForeignKey('correo_institucional_mensajes.id'), nullable=False, index=True)

    tono = db.Column(db.String(40), default='formal_institucional', nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    contenido = db.Column(db.Text, nullable=False)

    generado_por_ia = db.Column(db.Boolean, default=True, nullable=False)
    generado_por = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'mensaje_id': self.mensaje_id,
            'tono': self.tono,
            'version': self.version,
            'contenido': self.contenido,
            'generado_por_ia': self.generado_por_ia,
            'generado_por': self.generado_por,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
