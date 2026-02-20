import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configurações Iniciais
load_dotenv()
fake = Faker('pt_BR') 

# Conexão com o Banco
def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}")

def setup_extra_cities(conn):
    """Insere cidades extras para análise geográfica (Pilar B)"""
    cidades_extras = [
        (10, 'Uberlândia', 1),    
        (11, 'Juiz de Fora', 1),  
        (12, 'Campinas', 2),      
        (13, 'Santos', 2),        
        (14, 'Ribeirão Preto', 2) 
    ]
    
    print("🌍 Expandindo abrangência geográfica...")
    for city_id, name, state_id in cidades_extras:
        conn.execute(text(f"""
            INSERT INTO cities (id, name, state_id) 
            VALUES ({city_id}, '{name}', {state_id}) 
            ON CONFLICT (id) DO NOTHING;
        """))
    conn.commit()

def generate_data(n_records=50):
    engine = get_engine()
    
    with engine.connect() as conn:
        setup_extra_cities(conn)
        
        print(f"🚀 Gerando {n_records} notas fiscais com lógica de Pareto...")
        
        # --- AJUSTE PARA O PILAR DE GASTOS & FORNECEDORES ---
        # Criamos uma lista fixa de 8 fornecedores para garantir recorrência
        # Alguns CNPJs (fictícios gerados) para dar credibilidade
        fornecedores_carteira = [fake.cnpj().replace('.', '').replace('/', '').replace('-', '') for _ in range(8)]
        
        # Pesos: Os primeiros fornecedores da lista terão mais chances de serem escolhidos (Simulando Pareto)
        pesos_fornecedores = [0.30, 0.20, 0.15, 0.10, 0.10, 0.05, 0.05, 0.05]
        # -----------------------------------------------------

        # Datas para análise de Volumetria Temporal
        today = datetime.now()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        base_id = 2000 
        
        for i in range(n_records):
            current_id = base_id + i
            
            # 1. Instância de Processo
            conn.execute(text(f"INSERT INTO process_instances (id, type) VALUES ({current_id}, 'Inbound')"))
            
            # 2. Cidades (Pilar B - Geográfico)
            city_ids = [1, 2, 3, 10, 11, 12, 13, 14]
            supplier_city = random.choice(city_ids)
            customer_city = random.choice(city_ids)
            supplier_state = 1 if supplier_city in [1, 2, 10, 11] else 2
            customer_state = 1 if customer_city in [1, 2, 10, 11] else 2

            # 3. Nota Fiscal 
            # Escolha ponderada do fornecedor (Aplica a lógica 80/20)
            cnpj_fornecedor = random.choices(fornecedores_carteira, weights=pesos_fornecedores, k=1)[0]
            
            valor_nota = round(random.uniform(500.00, 15000.00), 2)
            
            sql_nota = text("""
                INSERT INTO tax_documents (
                    id, number, type, total_value, 
                    supplier_identification_number, customer_identification_number, 
                    supplier_city_id, customer_city_id, 
                    supplier_state_id, customer_state_id,
                    process_instance_id
                ) VALUES (
                    :id, :number, 'MaterialInvoice', :val, 
                    :cnpj_f, '99999999000199', 
                    :city_f, :city_c, 
                    :state_f, :state_c,
                    :proc_id
                )
            """)
            
            conn.execute(sql_nota, {
                "id": current_id,
                "number": random.randint(10000, 99999),
                "val": valor_nota,
                "cnpj_f": cnpj_fornecedor,
                "city_f": supplier_city,
                "city_c": customer_city,
                "state_f": supplier_state,
                "state_c": customer_state,
                "proc_id": current_id
            })
            
            # 4. Itens (Para validação do STRING_AGG da Query Original)
            qtd_itens = random.randint(1, 3)
            for k in range(qtd_itens):
                item_id = (current_id * 10) + k
                conn.execute(text("""
                    INSERT INTO items (id, description, unit_price, total_value, purchase_order, tax_document_id)
                    VALUES (:id, :desc, :price, :total, :po, :doc_id)
                """), {
                    "id": item_id,
                    "desc": random.choice(['Cimento', 'Aço', 'Cabo', 'Disjuntor', 'Notebook', 'Monitor']),
                    "price": round(valor_nota / qtd_itens, 2),
                    "total": round(valor_nota / qtd_itens, 2),
                    "po": f"PO-2026-{random.randint(100, 999)}",
                    "doc_id": current_id
                })
            
            # 5. Tarefas (Pilar C - Eficiência/Lead Time)
            delta_days = (last_day_last_month - first_day_last_month).days
            random_day = random.randint(0, delta_days)
            date_completed = first_day_last_month + timedelta(days=random_day)
            
            # Variação de Lead Time (2h a 72h) para gerar histograma rico
            hours_diff = random.randint(2, 72) 
            date_created = date_completed - timedelta(hours=hours_diff)
            
            conn.execute(text("""
                INSERT INTO tasks (id, created_at, completed_at, task_definition_id, status_id, process_instance_id)
                VALUES (:id, :created, :completed, 12, 120, :proc_id)
            """), {
                "id": current_id,
                "created": date_created,
                "completed": date_completed,
                "proc_id": current_id
            })
        
        conn.commit()
        print("✅ Sucesso! Dados gerados com padrão de análise sênior.")

if __name__ == "__main__":
    generate_data(100) # 100 notas para ficar mais bonito