import os
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# python -m streamlit run app/dashboard.py

load_dotenv()
fake = Faker('pt_BR') 

def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}")

def setup_extra_cities(conn):
    # Expande o universo geográfico para testar filtros de Estado/Cidade
    cidades_extras = [
        (10, 'Uberlândia', 1), (11, 'Juiz de Fora', 1),  
        (12, 'Campinas', 2), (13, 'Santos', 2), (14, 'Ribeirão Preto', 2),
        (15, 'Curitiba', 3), (16, 'Londrina', 3) 
    ]
    # Garante que o estado PR (3) exista
    conn.execute(text("INSERT INTO states (id, name) VALUES (3, 'Paraná') ON CONFLICT (id) DO NOTHING;"))
    
    for city_id, name, state_id in cidades_extras:
        conn.execute(text(f"""
            INSERT INTO cities (id, name, state_id) VALUES ({city_id}, '{name}', {state_id}) 
            ON CONFLICT (id) DO NOTHING;
        """))
    conn.commit()

def generate_chaos(n_records=200):
    engine = get_engine()
    
    with engine.connect() as conn:
        setup_extra_cities(conn)
        print(f"🌪️ Gerando {n_records} registros cobrindo TODOS os cenários do diagrama...")
        
        fornecedores = [fake.cnpj().replace('.', '').replace('/', '').replace('-', '') for _ in range(12)]
        today = datetime.now()
        start_date = today - timedelta(days=90) # 3 meses de histórico
        
        base_id = 10000 # IDs altos para segurança
        
        # DEFINIÇÃO DAS REGRAS DE NEGÓCIO (Conforme Diagrama)
        # Tuplas de (Task_ID, [Status_Possíveis])
        regras_tarefas = {
            10: [100, 101], # Verificação Duplicada -> Duplicada / Não Duplicada
            11: [110, 111], # Verificação Divergência -> Com / Sem Divergência
            12: [120, 121], # Escrituração -> Sucesso / Falha
            13: [130, 131]  # Pagamento -> Paga / Não Paga
        }
        
        tipos_notas = ['MaterialInvoice', 'ServiceInvoice', 'TransportationInvoice']
        
        for i in range(n_records):
            current_id = base_id + i
            
            # --- 1. SELEÇÃO ALEATÓRIA DE CENÁRIO ---
            tipo_nota = random.choice(tipos_notas)
            
            # Escolhe qual etapa do processo vamos simular
            # Damos mais peso para Escrituração (12) pois é o foco do case, mas geramos os outros também
            task_def_id = random.choices([10, 11, 12, 13], weights=[0.1, 0.1, 0.6, 0.2])[0]
            
            # Escolhe um status válido para aquela tarefa
            status_possiveis = regras_tarefas[task_def_id]
            status_id = random.choice(status_possiveis)

            # --- 2. DADOS CADASTRAIS ---
            conn.execute(text(f"INSERT INTO process_instances (id, type) VALUES ({current_id}, 'Inbound')"))
            
            # Garante cidades válidas para não perder dados no Dashboard
            city_ids = [1, 2, 3, 10, 11, 12, 13, 14, 15, 16]
            supplier_city = random.choice(city_ids)
            customer_city = random.choice(city_ids)
            
            # Mapeamento Estado
            state_map = {1:1, 2:1, 10:1, 11:1, 3:2, 12:2, 13:2, 14:2, 15:3, 16:3}
            supplier_state = state_map.get(supplier_city, 1)
            customer_state = state_map.get(customer_city, 1)

            # --- 3. INSERÇÃO ---
            val = round(random.uniform(100.00, 50000.00), 2)
            cnpj = random.choice(fornecedores)
            
            sql_nota = text("""
                INSERT INTO tax_documents (
                    id, number, type, total_value, 
                    supplier_identification_number, customer_identification_number, 
                    supplier_city_id, customer_city_id, 
                    supplier_state_id, customer_state_id,
                    process_instance_id
                ) VALUES (:id, :num, :type, :val, :cnpj, '99999999000199', :sc, :cc, :ss, :cs, :pid)
            """)
            
            conn.execute(sql_nota, {
                "id": current_id, "num": random.randint(1000, 99999),
                "type": tipo_nota, "val": val, "cnpj": cnpj,
                "sc": supplier_city, "cc": customer_city,
                "ss": supplier_state, "cs": customer_state, "pid": current_id
            })
            
            # Datas
            d_created = start_date + timedelta(days=random.randint(0, 89))
            d_completed = d_created + timedelta(hours=random.randint(1, 72))
            
            conn.execute(text("""
                INSERT INTO tasks (id, created_at, completed_at, task_definition_id, status_id, process_instance_id)
                VALUES (:id, :cr, :co, :td, :st, :pid)
            """), {
                "id": current_id, "cr": d_created, "co": d_completed,
                "td": task_def_id, "st": status_id, "pid": current_id
            })
            
        conn.commit()
        print("✅ Dados COMPLETOS gerados! CTe, Serviços, Materiais e todas as tarefas populadas.")

if __name__ == "__main__":
    generate_chaos()