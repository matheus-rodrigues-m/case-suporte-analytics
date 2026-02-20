import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime

# python ./app/main.py

load_dotenv()

def get_db_connection():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}")

def extract_data():
    query = """
    SELECT
        td.id AS "ID Nota Fiscal",
        td.number AS "Número da Nota",
        STRING_AGG(DISTINCT i.purchase_order, ', ') AS "Pedidos de Compra",
        td.supplier_identification_number AS "CNPJ Fornecedor",
        city_fornecedor.name AS "Cidade Fornecedor",
        td.customer_identification_number AS "CNPJ Tomador",
        city_tomador.name AS "Cidade Tomador",
        TO_CHAR(t.completed_at, 'DD/MM/YYYY') AS "Data Escrituração"
    FROM tax_documents td
    INNER JOIN tasks t ON td.process_instance_id = t.process_instance_id
    INNER JOIN cities city_fornecedor ON td.supplier_city_id = city_fornecedor.id
    INNER JOIN cities city_tomador ON td.customer_city_id = city_tomador.id
    LEFT JOIN items i ON td.id = i.tax_document_id
    WHERE 
        td.type = 'MaterialInvoice'
        AND t.task_definition_id = 12
        AND t.status_id = 120
        AND t.completed_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND t.completed_at < DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY 
        td.id, td.number, td.supplier_identification_number, 
        city_fornecedor.name, td.customer_identification_number, 
        city_tomador.name, t.completed_at
    ORDER BY 
        t.completed_at DESC;
    """
    
    print("Conectando ao banco e executando a query...")
    engine = get_db_connection()
    
    try:
        df = pd.read_sql(query, engine)
        print(f"Dados extraídos com sucesso!")
        return df
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")
        return None

def save_report(df):
    if df is not None and not df.empty:
        filename = f"relatorio_notas_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Relatório: {os.path.abspath(filename)}")
    else:
        print("Nenhum dado encontrado")

if __name__ == "__main__":
    print("INICIANDO AUTOMAÇÃO DE RELATÓRIOS...")
    dataframe = extract_data()
    save_report(dataframe)
    print("PROCESSO FINALIZADO...")