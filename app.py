import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(
    page_title="Olist BI Dashboard",
    page_icon="🛒",
    layout="wide"
)

# Paleta de cores (Dark com vermelho)
COR_ACENTO = "#E50914"
COR_BARRAS = "#B71C1C"

# 2. Carregamento dos Dados
@st.cache_data
def load_data():
    # Puxa o arquivo limpo que está no diretório
    df = pd.read_csv("olist_limpo.csv")
    
    # Converte a coluna de data para o formato correto de tempo
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    
    # Cria uma coluna de faturamento (preço + frete) se não existir
    if 'faturamento' not in df.columns:
        df['faturamento'] = df['price'] + df['freight_value']
        
    # Cria uma coluna de Ano/Mês para facilitar o gráfico de linha
    df['ano_mes'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    return df

try:
    df_olist = load_data()
except FileNotFoundError:
    st.error("⚠️ Arquivo 'olist_limpo.csv' não encontrado. Verifique se ele está no GitHub.")
    st.stop()

# 3. Barra Lateral (Filtros)
st.sidebar.header("🎛️ Filtros do Painel")

# Filtro de Data
data_min = df_olist['order_purchase_timestamp'].dt.date.min()
data_max = df_olist['order_purchase_timestamp'].dt.date.max()

data_selecionada = st.sidebar.date_input(
    "Período das Vendas:", 
    value=(data_min, data_max), 
    min_value=data_min, 
    max_value=data_max
)

# Filtro de Estados
estados_disponiveis = sorted(df_olist['customer_state'].dropna().unique())
principais_estados = [e for e in ['SP', 'RJ', 'MG'] if e in estados_disponiveis]

estados_selecionados = st.sidebar.multiselect(
    "Estados do Cliente:", 
    options=estados_disponiveis, 
    default=principais_estados if principais_estados else estados_disponiveis[:3]
)

# 4. Aplicação dos Filtros
if isinstance(data_selecionada, tuple) and len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
else:
    start_date, end_date = data_min, data_max

df_filtrado = df_olist[
    (df_olist['order_purchase_timestamp'].dt.date >= start_date) &
    (df_olist['order_purchase_timestamp'].dt.date <= end_date) &
    (df_olist['customer_state'].isin(estados_selecionados))
]

if df_filtrado.empty:
    st.warning("⚠️ Nenhuma informação encontrada para a combinação de filtros selecionada.")
    st.stop()

# 5. Painel Principal (KPIs)
st.title("🛒 Business Intelligence — Olist Performance")
st.markdown("Análise de faturamento e distribuição regional.")
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="📊 Faturamento Total", value=f"R$ {df_filtrado['faturamento'].sum():,.2f}")
with col2:
    st.metric(label="📦 Pedidos Únicos", value=f"{df_filtrado['order_id'].nunique():,}")
with col3:
    st.metric(label="💳 Ticket Médio (Item)", value=f"R$ {df_filtrado['price'].mean():.2f}")
with col4:
    st.metric(label="🚚 Custo Médio de Frete", value=f"R$ {df_filtrado['freight_value'].mean():.2f}")

st.divider()

# 6. Gráficos
graf_col1, graf_col2 = st.columns(2)

with graf_col1:
    st.subheader("📈 Evolução Mensal do Faturamento")
    vendas_mensais = df_filtrado.groupby('ano_mes')['faturamento'].sum().reset_index().sort_values('ano_mes')
    
    fig_linha = px.line(
        vendas_mensais, 
        x='ano_mes', 
        y='faturamento', 
        labels={'ano_mes': 'Período', 'faturamento': 'Faturamento (R$)'}, 
        markers=True, 
        template="plotly_dark"
    )
    fig_linha.update_traces(line=dict(color=COR_ACENTO, width=3), marker=dict(size=6))
    fig_linha.update_layout(yaxis=dict(gridcolor='#2D3139'), xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_linha, use_container_width=True)

with graf_col2:
    st.subheader("📍 Top 5 Estados por Faturamento")
    vendas_estado = df_filtrado.groupby('customer_state')['faturamento'].sum().reset_index()
    # Pega os 5 maiores e ordena do menor pro maior para o gráfico horizontal ficar bonito
    vendas_estado = vendas_estado.nlargest(5, 'faturamento').sort_values(by='faturamento', ascending=True)
    
    fig_barra = px.bar(
        vendas_estado, 
        y='customer_state', 
        x='faturamento', 
        orientation='h', 
        labels={'customer_state': 'Estado', 'faturamento': 'Faturamento (R$)'}, 
        template="plotly_dark",
        text_auto='.2s' # Adiciona o valor resumido direto na barra
    )
    fig_barra.update_traces(marker_color=COR_BARRAS, width=0.6, textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig_barra.update_layout(xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_barra, use_container_width=True)
