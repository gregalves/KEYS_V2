from flask_sqlalchemy import SQLAlchemy
import pytz
from datetime import datetime


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(400), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    records = db.relationship('Record', backref='user', lazy=True)  # Relacionamento com Record

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_chave = db.Column(db.String(1), nullable=False)
    chave = db.Column(db.String(7), nullable=False, unique=True)  # Novo campo 'chave'
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    empresa = db.Column(db.String(50), nullable=False)
    citrix = db.Column(db.String(3), nullable=False)
    gestor_contrato = db.Column(db.String(50), nullable=False)
    description_scs = db.Column(db.String(20), nullable=False)
    chamado_gestao_x = db.Column(db.String(50), nullable=False)
    inicio_contrato = db.Column(db.Date, nullable=False)
    termino_contrato = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Relacionamento com User
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('America/Sao_Paulo')))