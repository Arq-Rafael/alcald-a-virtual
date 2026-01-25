from datetime import datetime, timedelta
import json
from app import db

class Radicado(db.Model):
    __tablename__ = 'radicados'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_radicado = db.Column(db.String(50), unique=True, nullable=False)
    fecha_radicacion = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50))  # Petición, Queja, Reclamo, Sugerencia, Derecho de petición
    
    # Remitente info
    remitente_nombre = db.Column(db.String(200))
    remitente_entidad = db.Column(db.String(200))
    
    asunto = db.Column(db.String(500))
    descripcion = db.Column(db.Text)
    
    # Store paths as JSON string list
    adjuntos_paths = db.Column(db.Text) 
    
    # Destino y plazo - NUEVOS CAMPOS
    oficina_destino = db.Column(db.String(100))  # Código de oficina
    plazo_dias = db.Column(db.Integer, default=5)  # Plazo en días para responder
    fecha_vencimiento = db.Column(db.DateTime)  # Se calcula automáticamente
    
    # Assignment
    asignado_a = db.Column(db.String(100))  # Username or Role
    
    # Status
    # PENDIENTE: Recibido, no respondido
    # EN_TRAMITE: Asignado, en proceso
    # RESPONDIDO: Respuesta enviada
    estado = db.Column(db.String(20), default='PENDIENTE') 
    
    creado_por = db.Column(db.String(100))
    
    # Relationship
    respuestas = db.relationship('RespuestaRadicado', backref='radicado', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.plazo_dias:
            self.fecha_vencimiento = datetime.utcnow() + timedelta(days=self.plazo_dias)

    def set_adjuntos(self, paths):
        self.adjuntos_paths = json.dumps(paths)
        
    def get_adjuntos(self):
        if not self.adjuntos_paths: return []
        try:
            return json.loads(self.adjuntos_paths)
        except:
            return []
    
    @property
    def dias_restantes(self):
        """Calcula días restantes para responder"""
        if self.estado == 'RESPONDIDO':
            return None
        hoy = datetime.utcnow()
        if self.fecha_vencimiento:
            delta = (self.fecha_vencimiento - hoy).days
            return max(0, delta)
        return None
    
    @property
    def semaforo(self):
        """Retorna el estado del semáforo (verde/amarillo/rojo)"""
        if self.estado == 'RESPONDIDO':
            return 'verde'
        dias = self.dias_restantes
        if dias is None:
            return 'verde'
        if dias > 3:
            return 'verde'
        elif dias > 0:
            return 'amarillo'
        else:
            return 'rojo'
    
    @property
    def semaforo_color(self):
        """Retorna el color CSS para el semáforo"""
        colors = {
            'verde': '#16a34a',
            'amarillo': '#f59e0b',
            'rojo': '#ef4444'
        }
        return colors.get(self.semaforo, '#6b7280')

class RespuestaRadicado(db.Model):
    __tablename__ = 'radicados_respuestas'
    
    id = db.Column(db.Integer, primary_key=True)
    radicado_id = db.Column(db.Integer, db.ForeignKey('radicados.id'), nullable=False)
    
    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow)
    respuesta_texto = db.Column(db.Text)
    
    # Files
    adjuntos_respuesta_paths = db.Column(db.Text) # JSON list
    pdf_generado_path = db.Column(db.String(500))
    
    respondido_por = db.Column(db.String(100))

    def set_adjuntos(self, paths):
        self.adjuntos_respuesta_paths = json.dumps(paths)
        
    def get_adjuntos(self):
        if not self.adjuntos_respuesta_paths: return []
        try:
            return json.loads(self.adjuntos_respuesta_paths)
        except:
            return []
