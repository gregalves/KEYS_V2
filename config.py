import os

class Config:
    SECRET_KEY = 'your_secret_key'
#    SQLALCHEMY_DATABASE_URI = 'sqlite:///keys.db'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://toorkeys:toor@localhost/keys_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
# Configurações de e-mail (por exemplo, usando Gmail)
#    MAIL_SERVER = 'smtp.gmail.com'
#    MAIL_PORT = 587
#    MAIL_USE_TLS = True
#    MAIL_USERNAME = 'celso.gregorio@gmail.com'
#    MAIL_PASSWORD = 'wbun wucw eqzw zhlt'  # Ou use variáveis de ambiente para segurança
#    MAIL_DEFAULT_SENDER = ('Suporte N1 - N2', 'your_email@gmail.com')
    MAIL_SERVER = '10.100.0.12'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None  # Ou use variáveis de ambiente para segurança
    MAIL_DEFAULT_SENDER = ('GESTAO DE ACESSOS', 'gestaodeacesso@liggatelecom.com.br')