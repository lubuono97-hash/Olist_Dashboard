import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página e Tema
st.set_page_config(
    page_title="Olist BI Dashboard",
    page_icon="🛒",
    layout="wide"
)

# Paleta de cores personalizada para o painel (Dark com acentos em tons de vermelho/grafite)
COR_ACENTO = "#E50914"  # Vermelho dinâmico para destacar pontos importantes
COR_BARRAS = "#B71C1C"  # Vermelho escuro para gráficos de barras

# 2. Carregamento Otimizado dos Dados (Apenas o arquivo limpo)
@st.cache_data
def load_data():
    # Carrega o arquivo unificado que você subiu no GitHub
    df = pd.read_csv("olist_limpo.csv")
    
    # Garantindo a tipagem correta para otimizar os filtros temporais
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['ano_mes'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    # Se não houver a coluna calculada de faturamento, descomente a linha abaixo:
    # df['faturamento'] = df['price'] + df['freight_value']
    
    return df

try:
    df_olist = load_data()
except FileNotFoundError:
    st.error("⚠️ O arquivo 'olist_limpo.csv' não foi encontrado no repositório. Certifique-se de que o nome está idêntico e na raiz do projeto.")
    st.stop()

# 3. Barra Lateral (Filtros Avançados)
st.sidebar.header("🎛️ Filtros do Painel")

# Filtro 1: Intervalo de Datas Dinâmico
data_min = df_olist['order_purchase_timestamp'].min().date()
data_max = df_olist['order_purchase_timestamp'].max().date()

data_selecionada = st.sidebar.date_input(
    "Período das Vendas:",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

# Filtro 2: Seleção de Estados (Pré-seleciona os 3 principais mercados)
estados_disponiveis = sorted(df_olist['customer_state'].dropna().unique())
principais_estados = [e for e in ['SP', 'RJ', 'MG'] if e in estados_disponiveis]

estados_selecionados = st.sidebar.multiselect(
    "Estados do Cliente:",
    options=estados_disponiveis,
    default=principais_estados if principais_estados else estados_disponiveis[:3]
)

# Filtro 3: Categorias de Produtos
coluna_categoria = 'product_category_name_english' if 'product_category_name_english' in df_olist.columns else 'product_category_name'
categorias_disponiveis = sorted(df_olist[coluna_categoria].dropna().unique())

categorias_selecionadas = st.sidebar.multiselect(
    "Categorias de Produtos:",
    options=categorias_disponiveis,
    default=categorias_disponiveis[:5]  # Mostra as 5 primeiras por padrão
)

# --- Aplicação dos Filtros no Dataset ---
# Validação do filtro de data (garante que o usuário selecionou início e fim)
if isinstance(data_selecionada, tuple) and len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
else:
    start_date, end_date = data_min, data_max

df_filtrado = df_olist[
    (df_olist['order_purchase_timestamp'].dt.date >= start_date) &
    (df_olist['order_purchase_timestamp'].dt.date <= end_date) &
    (df_olist['customer_state'].isin(estados_selecionados)) &
    (df_olist[coluna_categoria].isin(categorias_selecionadas))
]

# 4. Validação de Segurança: Se os filtros limparem todo o dataset
if df_filtrado.empty:
    st.warning("⚠️ Nenhuma informação encontrada para a combinação de filtros selecionada. Altere os filtros na barra lateral.")
    st.stop()

# 5. Cabeçalho Principal
st.title("🛒 Business Intelligence — Olist Performance")
st.markdown("Análise estratégica de faturamento, volumetria de pedidos e distribuição de mercado.")
st.divider()

# 6. Bloco de Métricas Principais (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    faturamento_total = df_filtrado['faturamento'].sum()
    st.metric(label="📊 Faturamento Total", value=f"R$ {faturamento_total:,.2f}")

with col2:
    total_pedidos = df_filtrado['order_id'].nunique()
    st.metric(label="📦 Pedidos Únicos", value=f"{total_pedidos:,}")

with col3:
    ticket_medio = df_filtrado['price'].mean()
    st.metric(label="💳 Ticket Médio (Item)", value=f"R$ {ticket_medio:.2f}")

with col4:
    frete_medio = df_filtrado['freight_value'].mean()
    st.metric(label="🚚 Custo Médio de Frete", value=f"R$ {frete_medio:.2f}")

st.divider()

# 7. Visualizações Gráficas de Alta Performance
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
    # Customizando a linha para dar uma identidade forte e limpa
    fig_linha.update_traces(line=dict(color=COR_ACENTO, width=3), marker=dict(size=6))
    fig_linha.update_layout(yaxis=dict(gridcolor='#2D3139'), xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_linha, use_container_width=True)

with graf_col2:
    st.subheader("🏆 Top Categorias por Faturamento")
    vendas_categoria = df_filtrado.groupby(coluna_categoria)['faturamento'].sum().reset_index()
    vendas_categoria = vendas_categoria.sort_values(by='faturamento', ascending=True)
    
    fig_barra = px.bar(
        vendas_categoria, 
        y=coluna_categoria, 
        x='faturamento',
        orientation='h',
        labels={coluna_categoria: 'Categoria', 'faturamento': 'Faturamento (R$)'},
        template="plotly_dark"
    )
    # Cor customizada para as barras
    fig_barra.update_traces(marker_color=COR_BARRAS, width=0.6)
    fig_barra.update_layout(xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_barra, use_container_width=True)
