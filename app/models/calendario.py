import datetime
from app import db

class EventoCalendario(db.Model):
    __tablename__ = 'eventos_calendario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.String(100), nullable=False, index=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False, index=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    
    # Categoría/Tipo de evento
    categoria = db.Column(db.String(50), default='personal', nullable=False)  
    # Opciones: personal, trabajo, recordatorio, tarea, reunion, otro
    
    # Color/Icono para visualización
    color = db.Column(db.String(20), default='primary', nullable=False)
    # Opciones: primary, success, warning, danger, info
    
    # Ubicación (opcional)
    ubicacion = db.Column(db.String(200), nullable=True)
    
    # Notificación
    notificacion_minutos = db.Column(db.Integer, default=15, nullable=False)
    # Minutos antes del evento para mostrar notificación
    
    # Recurrencia
    es_recurrente = db.Column(db.Boolean, default=False, nullable=False)
    frecuencia = db.Column(db.String(20), nullable=True)  # daily, weekly, monthly, yearly
    
    # Estado
    completado = db.Column(db.Boolean, default=False, nullable=False)
    notificacion_enviada = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.datetime.utcnow, 
                                   onupdate=datetime.datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<EventoCalendario {self.id}: {self.titulo}>'
    
    @property
    def dias_restantes(self):
        """Calcula días restantes hasta el evento"""
        ahora = datetime.datetime.utcnow()
        delta = (self.fecha_inicio - ahora).days
        return delta
    
    @property
    def es_proximo(self):
        """Verifica si el evento es próximo (dentro de 7 días)"""
        return 0 <= self.dias_restantes <= 7 and not self.completado
    
    @property
    def es_hoy(self):
        """Verifica si el evento es hoy"""
        ahora = datetime.datetime.utcnow()
        return self.fecha_inicio.date() == ahora.date()
    
    @property
    def es_pasado(self):
        """Verifica si el evento ya pasó"""
        ahora = datetime.datetime.utcnow()
        return self.fecha_inicio < ahora and not self.completado
    
    @property
    def debe_notificar(self):
        """Verifica si debe enviar notificación"""
        if self.notificacion_enviada or self.completado:
            return False
        
        ahora = datetime.datetime.utcnow()
        minutos_para_evento = (self.fecha_inicio - ahora).total_seconds() / 60
        
        # Notificar si estamos dentro del rango de minutos y no ha sido notificado
        return 0 <= minutos_para_evento <= self.notificacion_minutos
    
    def to_dict(self):
        """Convierte el evento a diccionario para JSON"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_inicio_formato': self.fecha_inicio.strftime('%H:%M - %d/%m/%Y'),
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'categoria': self.categoria,
            'color': self.color,
            'ubicacion': self.ubicacion,
            'notificacion_minutos': self.notificacion_minutos,
            'completado': self.completado,
            'dias_restantes': self.dias_restantes,
            'es_proximo': self.es_proximo,
            'es_hoy': self.es_hoy,
            'es_pasado': self.es_pasado,
        }
