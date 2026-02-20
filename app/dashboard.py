import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import io
from datetime import datetime

# python -m streamlit run app/dashboard.py

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Analytics de Escrituração", layout="wide")
load_dotenv()

def format_cnpj(value):
    # Aplica a máscara de CNPJ
    if pd.isna(value): return ""
    v = str(value).zfill(14) 
    return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"

# Função para converter o DataFrame em um arquivo Excel em memória
@st.cache_data
def to_excel(df):
    output = io.BytesIO()
    # Usando engine openpyxl para gerar o arquivo .xlsx
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados Filtrados')
    processed_data = output.getvalue()
    return processed_data

@st.cache_data
def get_data():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}")
    
    query = """
    SELECT
        td.id,
        td.total_value,
        td.type AS tipo_nota,               
        td_def.name AS nome_tarefa,         
        st.name AS status_tarefa,           
        td.supplier_identification_number AS cnpj_fornecedor,
        c.name AS cidade_fornecedor,
        s.name AS estado_fornecedor,
        t.created_at,
        t.completed_at
    FROM tax_documents td
    INNER JOIN tasks t ON td.process_instance_id = t.process_instance_id
    LEFT JOIN cities c ON td.supplier_city_id = c.id
    LEFT JOIN states s ON c.state_id = s.id
    INNER JOIN task_definitions td_def ON t.task_definition_id = td_def.id
    INNER JOIN status st ON t.status_id = st.id
    ORDER BY t.completed_at;
    """
    
    df = pd.read_sql(query, engine)
    
    # Engenharia de Atributos
    df['lead_time_horas'] = (df['completed_at'] - df['created_at']).dt.total_seconds() / 3600
    df['data_escrituracao'] = df['completed_at'].dt.date
    
    # Tratamento de CNPJ
    df['cnpj_fornecedor'] = df['cnpj_fornecedor'].astype(str)
    df['cnpj_formatado'] = df['cnpj_fornecedor'].apply(format_cnpj)
    
    return df

# INTERFACE
try:
    df = get_data()
    
    # Título
    st.title("Monitoramento de Performance Fiscal")
    st.markdown("Painel de controle com filtros dinâmicos para auditoria de processos")
    st.markdown("---")

    # BARRA LATERAL (FILTROS)
    st.sidebar.header("Filtros de Análise")
    
    # 1. Filtro de Data
    min_date = df['data_escrituracao'].min()
    max_date = df['data_escrituracao'].max()
    date_range = st.sidebar.date_input("Período", [min_date, max_date])

    # 2. Filtros de Negócio (Multiselect)
    tipos_disponiveis = df['tipo_nota'].unique()
    filtro_tipo = st.sidebar.multiselect("Tipo de Nota", options=tipos_disponiveis, default=tipos_disponiveis)
    
    tarefas_disponiveis = df['nome_tarefa'].unique()
    filtro_tarefa = st.sidebar.multiselect("Tarefa Analisada", options=tarefas_disponiveis, default=tarefas_disponiveis)
    
    status_disponiveis = df['status_tarefa'].unique()
    filtro_status = st.sidebar.multiselect("Status do Processo", options=status_disponiveis, default=status_disponiveis)

    estados_disponiveis = df['estado_fornecedor'].dropna().unique()
    filtro_estado = st.sidebar.multiselect("Estado do Fornecedor", options=estados_disponiveis, default=estados_disponiveis)
    
    # APLICAÇÃO DOS FILTROS (PANDAS)
    mask = (
        (df['data_escrituracao'] >= date_range[0]) & 
        (df['data_escrituracao'] <= date_range[1]) &
        (df['tipo_nota'].isin(filtro_tipo)) &
        (df['nome_tarefa'].isin(filtro_tarefa)) &
        (df['status_tarefa'].isin(filtro_status)) &
        (df['estado_fornecedor'].isin(filtro_estado))
    )
    
    df_filtered = df.loc[mask]

    # BOTÃO DE EXPORTAÇÃO
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Exportação")
    
    if not df_filtered.empty:
        # Gera o arquivo Excel em memória
        excel_data = to_excel(df_filtered)
        
        # Gera um nome de arquivo dinâmico com a data/hora atual
        nome_arquivo = f"relatorio_fiscal_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        st.sidebar.download_button(
            label="Baixar Planilha (Excel)",
            data=excel_data,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.sidebar.warning("Sem dados para exportar")

    # VERIFICAÇÃO DE DADOS VAZIOS PARA OS GRÁFICOS
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados")
    else:
        # LINHA 1: KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        total_gasto = df_filtered['total_value'].sum()
        qtd_notas = df_filtered['id'].count()
        lead_time_medio = df_filtered['lead_time_horas'].mean()
        qtd_fornecedores = df_filtered['cnpj_fornecedor'].nunique()
        
        col1.metric("Spend", f"R$ {total_gasto:,.2f}")
        col2.metric("Notas", qtd_notas)
        col3.metric("Lead Time Médio", f"{lead_time_medio:.1f} h")
        col4.metric("Fornecedores", qtd_fornecedores)
        
        st.markdown("---")

        # LINHA 2: Spend por Forcenedor e Distribuição Geográfica
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("A. Spend por Fornecedor (Pareto)")
            df_pareto = df_filtered.groupby('cnpj_formatado')['total_value'].sum().reset_index()
            df_pareto = df_pareto.sort_values(by='total_value', ascending=False).head(10)
            
            fig_pareto = px.bar(
                df_pareto, x='total_value', y='cnpj_formatado', orientation='h',
                title="Top 10 Fornecedores (No Filtro Atual)",
                color='total_value', color_continuous_scale='Bluyl'
            )
            fig_pareto.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_pareto, use_container_width=True)

        with c2:
            st.subheader("B. Origem (Estado / Cidade)")
            df_geo = df_filtered.groupby(['estado_fornecedor', 'cidade_fornecedor']).size().reset_index(name='volume_notas')
            
            fig_geo = px.sunburst(
                df_geo, path=['estado_fornecedor', 'cidade_fornecedor'], values='volume_notas',
                title="Distribuição Geográfica",
                color='estado_fornecedor', color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_geo.update_traces(textinfo="label+percent entry")
            st.plotly_chart(fig_geo, use_container_width=True)

        # LINHA 3: OPERACIONAL E TEMPORAL
        c3, c4 = st.columns(2)
        
        with c3:
            st.subheader("C. Lead Time")
            fig_hist = px.histogram(
                df_filtered, x="lead_time_horas", nbins=20,
                title="Histograma de Tempo de Processamento", color_discrete_sequence=['#00CC96']
            )
            fig_hist.add_vline(x=lead_time_medio, line_dash="dash", annotation_text="Média")
            st.plotly_chart(fig_hist, use_container_width=True)

        with c4:
            st.subheader("D. Evolução Diária")
            df_time = df_filtered.groupby('data_escrituracao')['id'].count().reset_index()
            
            fig_line = px.area(
                df_time, x='data_escrituracao', y='id',
                title="Volume de Notas por Dia", markers=True
            )
            st.plotly_chart(fig_line, use_container_width=True)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
    st.info("Verifique a conexão com o banco de dados")