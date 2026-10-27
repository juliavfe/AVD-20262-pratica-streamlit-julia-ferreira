import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Correlação e distribuição — Spotify",
    layout="wide",
)

st.title("Correlação e distribuição das variáveis de streaming")
st.caption("Explore como as métricas de streaming e o ano de estreia se relacionam.")

df = load_data()

# Variáveis quantitativas analisadas no notebook Atividade_EDA.ipynb.
VARS_QUANT = [
    "Debut Year",
    "Total Streams (in millions)",
    "Lead Streams (in millions)",
    "Feature Streams (in millions)",
    "Solo Streams (in millions)",
]
COLUNA_CLASSE = "performance"

# Sidebar: filtros (variáveis + intervalo)
with st.sidebar:
    st.header("Filtros")

    variaveis = st.multiselect(
        "Variáveis quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        help="Selecione as variáveis usadas na análise de correlação.",
    )

    separar_por_classe = st.toggle(
        "Separar por performance",
        value=False,
        help="Exibe as distribuições separadas por performance baixa ou alta.",
    )

    # Um slider de intervalo para cada variável selecionada
    intervalos = {}
    for var in variaveis:
        if pd.api.types.is_integer_dtype(df[var]):
            minimo, maximo, passo = int(df[var].min()), int(df[var].max()), 1
        else:
            minimo, maximo, passo = float(df[var].min()), float(df[var].max()), 0.1
        intervalos[var] = st.slider(
            f"Intervalo de {var}",
            min_value=minimo,
            max_value=maximo,
            value=(minimo, maximo),
            step=passo,
            key=f"intervalo_{var}",
        )

# Mantém só os artistas dentro de todos os intervalos escolhidos
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

st.caption(f"{len(df_filtrado)} de {len(df)} artistas dentro dos intervalos escolhidos.")

# Dashboard 1: correlação e distribuições das variáveis selecionadas.
st.subheader("Correlação")

if len(variaveis) < 2:
    st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
else:
    metodo = st.selectbox(
        "Método de correlação",
        options=["spearman", "kendall", "pearson"],
        index=0,
        help="Spearman é o método usado como principal na EDA deste dataset.",
    )
    # TODO: calcular df_filtrado[variaveis].corr(method=metodo), montar heatmap e exibir.

st.subheader("Distribuição das variáveis selecionadas")

if not variaveis:
    st.info("Selecione pelo menos uma variável quantitativa na barra lateral.")
elif df_filtrado.empty:
    st.info("Nenhum artista corresponde aos intervalos selecionados.")
else:
    colunas_graficos = st.columns(2)
    for indice, variavel in enumerate(variaveis):
        fig = px.histogram(
            df_filtrado,
            x=variavel,
            color=COLUNA_CLASSE if separar_por_classe else None,
            nbins=30,
            barmode="overlay" if separar_por_classe else "relative",
            opacity=0.65 if separar_por_classe else 1,
            title=variavel,
            labels={
                variavel: variavel,
                COLUNA_CLASSE: "Performance",
                "count": "Quantidade de artistas",
            },
        )
        fig.update_layout(showlegend=separar_por_classe, margin=dict(t=50, r=15, b=35, l=45))
        with colunas_graficos[indice % len(colunas_graficos)]:
            st.plotly_chart(
                fig,
                width="stretch",
                key=f"distribuicao_{indice}",
                alt=f"Distribuição de {variavel} entre os artistas",
            )

# TODO: Dashboard 2 — KPIs (Aula 22)
