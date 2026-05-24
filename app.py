import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(
    page_title="Dashboard Olist",
    page_icon="🛒",
    layout="wide"
)

# 2. Carregamento dos Dados Otimizado
@st.cache_data
def load_data():
    # Opção A: Se você preferir carregar direto do seu arquivo já tratado:
    # return pd.read_csv("olist_limpo.csv")
    
    # Opção B: Carregando e cruzando as tabelas originais do seu diretório
    orders = pd.read_csv("olist_orders_dataset.csv")
    items = pd.read_csv("olist_order_items_dataset.csv")
    customers = pd.read_csv("olist_customers_dataset.csv")
    products = pd.read_csv("olist_products_dataset.csv")
    translation = pd.read_csv("product_category_name_translation.csv")
    
    # Tratamento de datas
    orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
    orders['ano_mes'] = orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    # Cruzamento das tabelas (Merges com 'left' para evitar perda de dados)
    df = items.merge(orders, on='order_id', how='left')
    df = df.merge(customers, on='customer_id', how='left')
    df = df.merge(products, on='product_id', how='left')
    df = df.merge(translation, on='product_category_name', how='left')
    
    # Se a tradução falhar para alguma categoria, mantém o nome em português
    df['product_category_name_english'] = df['product_category_name_english'].fillna(df['product_category_name'])
    
    # Cálculo do faturamento por item comercializado
    df['faturamento'] = df['price'] + df['freight_value']
    
    return df

# Inicializando o dataframe
df_olist = load_data()

# 3. Barra Lateral de Filtros
st.sidebar.header("Filtros do Painel")

# Filtro 1: Estados (pré-selecionando os principais do e-commerce: SP, RJ, MG)
estados_disponiveis = sorted(df_olist['customer_state'].dropna().unique())
estados_selecionados = st.sidebar.multiselect(
    "Filtrar por Estado do Cliente:",
    options=estados_disponiveis,
    default=[e for e in ['SP', 'RJ', 'MG'] if e in estados_disponiveis]
)

# Filtro 2: Categorias de Produtos
categorias_disponiveis = sorted(df_olist['product_category_name_english'].dropna().unique())
categorias_selecionadas = st.sidebar.multiselect(
    "Filtrar por Categoria de Produto:",
    options=categorias_disponiveis,
    default=categorias_disponiveis[:3] # Seleciona as 3 primeiras por padrão
)

# Aplicando os filtros ao dataset de trabalho
df_filtrado = df_olist[
    (df_olist['customer_state'].isin(estados_selecionados)) & 
    (df_olist['product_category_name_english'].isin(categorias_selecionadas))
]

# 4. Cabeçalho Principal
st.title("🛒 Business Intelligence - Olist E-Commerce")
st.markdown("Análise estratégica de faturamento, categorias e comportamento regional.")
st.divider()

# 5. Métricas Principais (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    faturamento_total = df_filtrado['faturamento'].sum()
    st.metric(label="Faturamento Total", value=f"R$ {faturamento_total:,.2f}")

with col2:
    total_pedidos = df_filtrado['order_id'].nunique()
    st.metric(label="Pedidos Únicos", value=f"{total_pedidos:,}")

with col3:
    ticket_medio = df_filtrado['price'].mean()
    st.metric(label="Ticket Médio do Item", value=f"R$ {ticket_medio:.2f}")

with col4:
    frete_medio = df_filtrado['freight_value'].mean()
    st.metric(label="Custo Médio de Frete", value=f"R$ {frete_medio:.2f}")

st.divider()

# 6. Gráficos e Visualizações Interativas
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
    st.plotly_chart(fig_linha, use_container_width=True)

with graf_col2:
    st.subheader("🏆 Top Categorias por Faturamento")
    vendas_categoria = df_filtrado.groupby('product_category_name_english')['faturamento'].sum().reset_index()
    vendas_categoria = vendas_categoria.sort_values(by='faturamento', ascending=True) # Ascending True para o gráfico de barras horizontais ficar ordenado do maior no topo
    
    fig_barra = px.bar(
        vendas_categoria, 
        y='product_category_name_english', 
        x='faturamento',
        orientation='h',
        labels={'product_category_name_english': 'Categoria', 'faturamento': 'Faturamento (R$)'},
        template="plotly_dark"
    )
    st.plotly_chart(fig_barra, use_container_width=True)
