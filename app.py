from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_migrate import Migrate
from models import db, User, Record
from utils import send_email
from datetime import datetime, timezone
from app import db
import random
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import os
from fpdf import FPDF
import re
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 1234
app.config.from_object('config.Config')

# Configurações para envio de e-mail usando Flask-Mail
app.config['MAIL_SERVER'] = '10.100.0.12'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = ('GESTAO DE ACESSOS', 'gestaodeacesso@liggatelecom.com.br')

mail = Mail(app)

# Configurando o logger para gravar logs em um arquivo com rotação
log_handler = RotatingFileHandler('system_logs.log', maxBytes=100000, backupCount=3)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# Defina a versão do programa
app_version = "1.0.2"

# Injetar o ano atual e a versão do programa em todos os templates
@app.context_processor
def inject_footer_data():
    return {
        'current_year': datetime.now().year,
        'version': app_version
    }

# Passa 'datetime' para todos os templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

@app.context_processor
def inject_timezone():
    return {'datetime': datetime, 'timezone': timezone}

# Inicializa o banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Cria as tabelas no banco de dados no momento da inicialização da aplicação
with app.app_context():
    db.create_all()

# Função para limpar o CPF (remover pontos e traços)
def clean_cpf(cpf):
    return re.sub(r'[.-]', '', cpf)

# Função para validar o CPF
def validate_cpf(cpf):
    cpf = clean_cpf(cpf)

    if len(cpf) != 11 or cpf in [cpf[0] * 11 for _ in range(10)]:
        return False

    def calculate_digit(cpf, step):
        total = sum([int(cpf[i]) * (step - i) for i in range(step - 1)])
        digit = 11 - (total % 11)
        return digit if digit < 10 else 0

    first_digit = calculate_digit(cpf, 10)
    second_digit = calculate_digit(cpf, 11)

    return cpf[-2:] == f"{first_digit}{second_digit}"

# Função para exportar um registro específico para CSV
def export_record_to_csv(record):
    # Definir o diretório de exportação
    export_directory = 'exports'
    os.makedirs(export_directory, exist_ok=True)  # Cria o diretório se ele não existir

    # Formatar o nome do arquivo com a chave e a data/hora
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"{record.chave}_{timestamp}.csv"
    file_path = os.path.join(export_directory, file_name)

    # Organizar os dados do registro em um dicionário para o DataFrame
    data = {
        "Tipo de Chave": record.tipo_chave,
        "Chave": record.chave,
        "Nome": record.nome,
        "Email": record.email,
        "CPF": record.cpf,
        "Empresa": record.empresa,
        "Citrix": record.citrix,
        "Gestor do Contrato": record.gestor_contrato,
        "Description SCS": record.description_scs,
        "Chamado Gestão X": record.chamado_gestao_x,
        "Início do Contrato": record.inicio_contrato,
        "Término do Contrato": record.termino_contrato,
        "Data de Criação": record.created_at  # Adiciona a data de criação do registro
    }

    # Criar um DataFrame com o dicionário de dados
    df = pd.DataFrame([data])

    # Salvar o DataFrame como CSV
    df.to_csv(file_path, index=False, sep=';')
    print(f"Registro exportado para {file_path}")

# Função para enviar e-mail após o registro
def send_user_email(nome, email, chave):
    primeiro_nome = nome.split()[0]
    
    msg = Message(
        subject='Chave gerada com sucesso!',
        recipients=[email]
    )

    msg.body = f"""
    Prezado {primeiro_nome},

    A CHAVE {chave} foi gerada com sucesso e está sendo processada pelo sistema de gestão de identidades.
    Em breve você receberá um e-mail com as credenciais de acesso à rede LIGGA.

    Atenciosamente,
    GESTÃO DE ACESSOS - LIGGA
    """
    
    mail.send(msg)

# Verifica se o usuário logado é administrador
def admin_required(f):
    def wrap(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Acesso negado! Apenas administradores podem acessar esta página.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrap

# Rota para exportar os dados em CSV, XLSX ou PDF
@app.route('/export_data/<string:file_type>')
def export_data(file_type):
    records = Record.query.all()

    data = [{
        "Tipo de Chave": record.tipo_chave,
        "Chave": record.chave,
        "Nome": record.nome,
        "Email": record.email,
        "CPF": record.cpf,
        "Empresa": record.empresa,
        "Citrix": record.citrix,
        "Gestor do Contrato": record.gestor_contrato,
        "Description SCS": record.description_scs,
        "Chamado Gestão X": record.chamado_gestao_x,
        "Início do Contrato": record.inicio_contrato,
        "Término do Contrato": record.termino_contrato
    } for record in records]

    df = pd.DataFrame(data)

    if file_type == 'csv':
        file_path = 'exported_data.csv'
        df.to_csv(file_path, index=False, sep=';')
        return send_file(file_path, as_attachment=True)

    elif file_type == 'xlsx':
        file_path = 'exported_data.xlsx'
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    elif file_type == 'pdf':
        file_path = 'exported_data.pdf'
        generate_pdf(df, file_path)
        return send_file(file_path, as_attachment=True)

    else:
        flash('Formato de arquivo inválido!', 'danger')
        return redirect(url_for('dashboard'))

def generate_pdf(df, file_path):
    pdf = FPDF(orientation='L', unit='mm', format='A4')  # 'L' para paisagem
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Título do relatório
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RELATÓRIO DE CHAVES E/F', 0, 1, 'C')
    pdf.ln(10)  # Linha em branco

    # Definir fontes para a tabela
    pdf.set_font('Arial', 'B', 9)

    # Largura total da página A4 em paisagem considerando margens
    page_width = 297 - 2 * pdf.l_margin  # A4 paisagem tem 297mm de largura

    # Definir a largura das colunas proporcionalmente ao conteúdo e reduzir larguras onde possível
    col_widths = {
        "Tipo de Chave": 15,
        "Chave": 20,
        "Nome": 35,
        "Email": 45,
        "CPF": 20,
        "Empresa": 25,
        "Citrix": 15,
        "Gestor do Contrato": 25,
        "Description SCS": 25,
        "Chamado Gestão X": 20,
        "Início do Contrato": 20,
        "Término do Contrato": 20
    }

    # Cabeçalho da tabela
    for col in df.columns:
        pdf.multi_cell(col_widths[col], 8, col, border=1, align='C')

    pdf.ln()  # Nova linha

    # Adicionar dados da tabela
    pdf.set_font('Arial', '', 8)  # Reduzimos a fonte para ajustar melhor os dados
    for index, row in df.iterrows():
        for col in df.columns:
            text = str(row[col])
            pdf.cell(col_widths[col], 8, text, 1, 0, 'C')  # Sem quebra de linha
        pdf.ln()  # Nova linha para o próximo registro

    # Rodapé com a versão e o ano atual
    pdf.set_y(-15)  # Move para o rodapé
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, f'Versão: {app_version} | Desenvolvido por SUPORTE N1 - N2 | {datetime.now().year}', 0, 0, 'C')

    pdf.output(file_path)

# Rota para criar novos usuários
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado', 'danger')
            return redirect(url_for('create_user'))

        hashed_password = generate_password_hash(password)  # Hash da senha
        new_user = User(nome=nome, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()

        app.logger.info(f"Usuário criado: {nome} ({email})")

        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_user.html')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.nome
            session['login_time'] = datetime.now(timezone.utc)

            app.logger.info(f"Usuário logado: {user.nome} ({email})")

            flash(f'Bem-vindo, {user.nome}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login ou senha incorretos', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    
    username = session.get('username', 'Usuário desconhecido')
    app.logger.info(f"{username} Deslogado!")
    
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        tipo_chave = request.form['tipo_chave']
        nome = request.form['nome']
        email = request.form['email']
        cpf = clean_cpf(request.form['cpf'])  # Limpa o CPF removendo pontos e traços
        empresa = request.form['empresa']
        citrix = request.form['citrix']
        gestor_contrato = request.form['gestor_contrato']
        chamado_gestao_x = request.form['chamado_gestao_x']
        inicio_contrato = request.form['inicio_contrato']
        termino_contrato = request.form['termino_contrato']
        subcanal_vendas = request.form['subcanal_vendas']  # Novo campo
        
        # Verificação de CPF e e-mail duplicado
        if not validate_cpf(cpf) or Record.query.filter_by(cpf=cpf).first():
            flash('CPF inválido ou já registrado! Verifique e cadastre novamente!', 'danger')
            return redirect(url_for('register'))

        if Record.query.filter_by(email=email).first():
            flash('E-mail já registrado! Verifique e cadastre novamente!', 'danger')
            return redirect(url_for('register'))
        
        while True:
            codigo_unico = random.randint(100000, 999999)
            if tipo_chave == 'F':
                chave = f'F{codigo_unico}'
            else:
                chave = f'E{codigo_unico}'
            
            if not Record.query.filter_by(chave=chave).first():
                break  # Se a chave for única, saia do loop
        
        description_scs = f'|||||||{chave}'
        description_scs_ch = description_scs[:7] + description_scs[7:].replace(description_scs[7], '', 1)
        description_scs = description_scs_ch
        
        novo_registro = Record(
            tipo_chave=tipo_chave,
            chave=chave,
            nome=nome,
            email=email,
            cpf=cpf,
            empresa=empresa,
            citrix=citrix,
            gestor_contrato=gestor_contrato,
            description_scs=description_scs,
            chamado_gestao_x=chamado_gestao_x,
            inicio_contrato=inicio_contrato,
            termino_contrato=termino_contrato,
            created_by=session['user_id'],
            subcanal_vendas=subcanal_vendas  # Novo campo persistido
        )
        
     
        db.session.add(novo_registro)
        db.session.commit()

        # Exportar o registro para CSV
        export_record_to_csv(novo_registro)

        # Enviar e-mail para o usuário após o registro
        send_user_email(nome, email, chave)

        app.logger.info(f"Registro criado: {nome} ({email}) com chave {chave}")

        flash('Registro criado e e-mail enviado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    search_query = request.args.get('search_query', '')

    if search_query:
        cleaned_query = clean_cpf(search_query)
        records = Record.query.filter(
            (Record.nome.ilike(f'%{search_query}%')) |
            (Record.chave.ilike(f'%{search_query}%')) |
            (Record.email.ilike(f'%{search_query}%')) |
            (Record.cpf.ilike(f'%{cleaned_query}%'))
        ).all()
    else:
        records = Record.query.all()

    username = session.get('username', 'Usuário desconhecido')
    app.logger.info(f"{username} acessou o dashboard")

    return render_template('dashboard.html', records=records)
    
@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    record = Record.query.get_or_404(record_id)
    
    if request.method == 'POST':
        record.nome = request.form['nome']
        record.email = request.form['email']
        record.cpf = clean_cpf(request.form['cpf'])  # Limpa o CPF
        record.empresa = request.form['empresa']
        
        try:
            db.session.commit()

            username = session.get('username', 'Usuário desconhecido')
            app.logger.info(f"{username} editou o registro {record_id}: {record.nome} ({record.email})")

            flash('Registro atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except:
            db.session.rollback()
            flash('Erro ao atualizar o registro.', 'danger')
            return redirect(url_for('edit_record', record_id=record_id))

    return render_template('edit_record.html', record=record)

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    
    try:
        db.session.delete(record)
        db.session.commit()

        username = session.get('username', 'Usuário desconhecido')
        app.logger.info(f"{username} excluiu o registro {record_id}: {record.nome} ({record.email})")

        flash('Registro excluído com sucesso!', 'success')
    except:
        db.session.rollback()
        flash('Erro ao excluir o registro.', 'danger')

    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)


