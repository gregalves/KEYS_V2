import pandas as pd
import pymysql

# Configuração do banco de dados MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'klfjud@$5628hrtyh',
    'database': 'keys_db'
}

# Caminho para o arquivo Excel
excel_file_path = '/opt/keys/KEYS/keys/dados_chaves.xlsx'

# Ler o arquivo Excel
df = pd.read_excel(excel_file_path, sheet_name='record_202411281451', engine='openpyxl')

# Substituir valores NaN por None para o MySQL interpretar como NULL
df = df.where(pd.notnull(df), None)

# Conectar ao MySQL
connection = pymysql.connect(**db_config)

try:
    with connection.cursor() as cursor:
        for _, row in df.iterrows():
            # Ajuste o nome das colunas para o seu banco de dados
            sql = """
            INSERT INTO record (tipo_chave, chave, nome, email, cpf, empresa, citrix, gestor_contrato, description_scs, chamado_gestao_x ,inicio_contrato, termino_contrato)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Certifique-se de que o número de colunas aqui corresponda ao número de placeholders acima
            cursor.execute(sql, tuple(row))
        connection.commit()
        print("Dados inseridos com sucesso!")
finally:
    connection.close()

