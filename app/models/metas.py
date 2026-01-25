import datetime as dt
from app import db

class MetaPlan(db.Model):
    __tablename__ = 'metas_plan'
    id = db.Column(db.Integer, primary_key=True)
    linea_estrategica = db.Column(db.String(300))
    sector = db.Column(db.String(300))
    programa = db.Column(db.String(300))
    unidad = db.Column(db.String(80))
    meta_cuatrenio = db.Column(db.Float)        
    meta_producto = db.Column(db.String(600))    
    avance_actual = db.Column(db.Float, default=0)   
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow,
                           onupdate=dt.datetime.utcnow)
    
    def porcentaje_cumplimiento(self):
        if not self.meta_cuatrenio or self.meta_cuatrenio == 0:
             return 0
        return min(100.0, (self.avance_actual / self.meta_cuatrenio) * 100)

class InformeProgresoMetas(db.Model):
    __tablename__ = 'informes_progreso_metas'
    id = db.Column(db.Integer, primary_key=True)
    meta_id = db.Column(db.Integer, db.ForeignKey('metas_plan.id'), nullable=False)
    contrato_num = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    fecha_informe = db.Column(db.DateTime, default=dt.datetime.utcnow)
    avance_manual = db.Column(db.Float, nullable=True)  # 0..100
    observaciones = db.Column(db.String(500), nullable=True)

    meta = db.relationship('MetaPlan')
    fotos = db.relationship(
        'InformeProgresoMetasFoto',
        back_populates='informe',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

class InformeProgresoMetasFoto(db.Model):
    __tablename__ = 'informes_progreso_metas_fotos'
    id = db.Column(db.Integer, primary_key=True)
    informe_id = db.Column(db.Integer, db.ForeignKey('informes_progreso_metas.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(250), nullable=True)

    informe = db.relationship('InformeProgresoMetas', back_populates='fotos')
