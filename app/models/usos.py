import datetime as dt
from app import db

class Parcela(db.Model):
    __tablename__ = 'parcelas'
    id                = db.Column(db.Integer, primary_key=True)
    cedula_catastral  = db.Column(db.String(50), unique=True, nullable=True)
    matricula         = db.Column(db.String(50), unique=True, nullable=True)
    propietario       = db.Column(db.String(200), nullable=True)
    lon               = db.Column(db.Float, nullable=True)
    lat               = db.Column(db.Float, nullable=True)
    created_at        = db.Column(db.DateTime, default=dt.datetime.utcnow)

class UsoSuelo(db.Model):
    __tablename__ = 'usos_suelo'
    id                = db.Column(db.Integer, primary_key=True)
    codigo            = db.Column(db.String(20), unique=True, nullable=False)
    nombre            = db.Column(db.String(100), nullable=False)

class InformeUso(db.Model):
    __tablename__ = 'informes_uso'
    id                = db.Column(db.Integer, primary_key=True)
    parcela_id        = db.Column(db.Integer, db.ForeignKey('parcelas.id'))
    uso_id            = db.Column(db.Integer, db.ForeignKey('usos_suelo.id'))
    fecha_generado    = db.Column(db.DateTime, default=dt.datetime.utcnow)
    pdf_path          = db.Column(db.String(200), nullable=False)

    parcela           = db.relationship('Parcela')
    uso               = db.relationship('UsoSuelo')
