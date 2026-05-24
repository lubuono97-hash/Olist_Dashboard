import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(
    page_title="Olist BI Dashboard",
    page_icon="🛒",
    layout="wide"
)

# Paleta de cores (Dark com detalhes em vermelho)
COR_ACENTO = "#E50914"
COR_BARRAS = "#B71C1C"

# 2. Carregamento e Mapeamento Dinâmico de Colunas
@st.cache_data
def load_data():
    df = pd.read_csv("olist_limpo.csv")
    return df

try:
    df_olist = load_data()
except FileNotFoundError:
    st.error("⚠️ O arquivo 'olist_limpo.csv' não foi encontrado na raiz do repositório.")
    st.stop()

# Função para mapear colunas por similaridade de nome
def encontrar_coluna(df, termos_chave, nome_padrao):
    for termo in termos_chave:
        for col in df.columns:
            if termo in col.lower():
                return col
    return nome_padrao

# Identificação automática das colunas presentes no seu olist_limpo.csv
coluna_categoria = encontrar_coluna(df_olist, ['english', 'categ'], 'product_category_name')
coluna_estado = encontrar_coluna(df_olist, ['state', 'estado', 'uf'], 'customer_state')
coluna_data = encontrar_coluna(df_olist, ['timestamp', 'data', 'date'], 'order_purchase_timestamp')
coluna_preco = encontrar_coluna(df_olist, ['price', 'preco', 'valor'], 'price')
coluna_frete = encontrar_coluna(df_olist, ['freight', 'frete'], 'freight_value')
coluna_pedido = encontrar_coluna(df_olist, ['order_id', 'pedido'], 'order_id')

# Validação crítica das colunas necessárias
colunas_necessarias = [coluna_categoria, coluna_estado, coluna_data, coluna_preco, coluna_frete, coluna_pedido]
colunas_faltantes = [c for c in colunas_necessarias if c not in df_olist.columns]

if colunas_faltantes:
    st.error("❌ **Conflito na estrutura do arquivo `olist_limpo.csv`**")
    st.markdown("As colunas esperadas não foram encontradas de forma automática.")
    st.markdown("### 📋 Colunas atualmente disponíveis no seu arquivo:")
    st.write(list(df_olist.columns))
    st.markdown("Compare a lista acima com o seu script de limpeza para ajustar os nomes.")
    st.stop()

# Tratamento de dados após validação
df_olist[coluna_data] = pd.to_datetime(df_olist[coluna_data])
df_olist['ano_mes'] = df_olist[coluna_data].dt.to_period('M').astype(str)

# Garante a existência da coluna de faturamento
if 'faturamento' not in df_olist.columns:
    df_olist['faturamento'] = df_olist[coluna_preco] + df_olist[coluna_frete]

# 3. Barra Lateral (Filtros)
st.sidebar.header("🎛️ Filtros do Painel")

# Filtro de Data
data_min = df_olist[coluna_data].dt.date.min()
data_max = df_olist[coluna_data].dt.date.max()
data_selecionada = st.sidebar.date_input("Período das Vendas:", value=(data_min, data_max), min_value=data_min, max_value=data_max)

# Filtro de Estados
estados_disponiveis = sorted(df_olist[coluna_estado].dropna().unique())
principais_estados = [e for e in ['SP', 'RJ', 'MG'] if e in estados_disponiveis]
estados_selecionados = st.sidebar.multiselect("Estados do Cliente:", options=estados_disponiveis, default=principais_estados if principais_estados else estados_disponiveis[:3])

# Filtro de Categorias
categorias_disponiveis = sorted(df_olist[coluna_categoria].dropna().unique())
categorias_selecionadas = st.sidebar.multiselect("Categorias de Produtos:", options=categorias_disponiveis, default=categorias_disponiveis[:5])

# Aplicação dos Filtros
if isinstance(data_selecionada, tuple) and len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
else:
    start_date, end_date = data_min, data_max

df_filtrado = df_olist[
    (df_olist[coluna_data].dt.date >= start_date) &
    (df_olist[coluna_data].dt.date <= end_date) &
    (df_filtrado := df_olist[df_olist[coluna_estado].isin(estados_selecionados)]) &
    (df_olist[coluna_categoria].isin(categorias_selecionadas))
]

# Recorte final preciso
df_filtrado = df_olist[
    (df_olist[coluna_data].dt.date >= start_date) &
    (df_olist[coluna_data].dt.date <= end_date) &
    (df_olist[coluna_estado].isin(estados_selecionados)) &
    (df_olist[coluna_categoria].isin(categorias_selecionadas))
]

if df_filtrado.empty:
    st.warning("⚠️ Nenhuma informação encontrada para a combinação de filtros selecionada.")
    st.stop()

# 4. Painel Principal (KPIs)
st.title("🛒 Business Intelligence — Olist Performance")
st.markdown("Análise estratégica de faturamento, volumetria de pedidos e distribuição de mercado.")
st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📊 Faturamento Total", value=f"R$ {df_filtrado['faturamento'].sum():,.2f}")
with col2:
    st.metric(label="📦 Pedidos Únicos", value=f"{df_filtrado[coluna_pedido].nunique():,}")
with col3:
    st.metric(label="💳 Ticket Médio (Item)", value=f"R$ {df_filtrado[coluna_preco].mean():.2f}")
with col4:
    st.metric(label="🚚 Custo Médio de Frete", value=f"R$ {df_filtrado[coluna_frete].mean():.2f}")

st.divider()

# 5. Gráficos
graf_col1, graf_col2 = st.columns(2)

with graf_col1:
    st.subheader("📈 Evolução Mensal do Faturamento")
    vendas_mensais = df_filtrado.groupby('ano_mes')['faturamento'].sum().reset_index().sort_values('ano_mes')
    fig_linha = px.line(vendas_mensais, x='ano_mes', y='faturamento', labels={'ano_mes': 'Período', 'faturamento': 'Faturamento (R$)'}, markers=True, template="plotly_dark")
    fig_linha.update_traces(line=dict(color=COR_ACENTO, width=3), marker=dict(size=6))
    fig_linha.update_layout(yaxis=dict(gridcolor='#2D3139'), xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_linha, use_container_width=True)

with graf_col2:
    st.subheader("🏆 Top Categorias por Faturamento")
    vendas_categoria = df_filtrado.groupby(coluna_categoria)['faturamento'].sum().reset_index().sort_values(by='faturamento', ascending=True)
    fig_barra = px.bar(vendas_categoria, y=coluna_categoria, x='faturamento', orientation='h', labels={coluna_categoria: 'Categoria', 'faturamento': 'Faturamento (R$)'}, template="plotly_dark")
    fig_barra.update_traces(marker_color=COR_BARRAS, width=0.6)
    fig_barra.update_layout(xaxis=dict(gridcolor='#2D3139'))
    st.plotly_chart(fig_barra, use_container_width=True)
