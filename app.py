import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Avaliação de Correlação entre Variáveis Quantitativas do Heart Disease Dataset",
    layout="wide",
)

st.title("Avaliação de Correlação entre Variáveis Quantitativas do Heart Disease Dataset")

df = load_data()

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA)
VARS_QUANT = ["age", "trestbps", "chol", "thalach", "oldpeak"]

# Sidebar: filtros (variáveis + intervalo)
with st.sidebar:
    st.header("Filtros")

    variaveis = st.multiselect(
        "Variáveis Quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        help="Selecione as variáveis quantitativas que deseja analisar no dashboard.",
    )

    separar_por_classe = st.toggle(
        "Distinguir por Classe",
        value=False,
        help="Colore a distribuição pela classe (doenca_cardiaca: Normal ou Cardíaco).",
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

# Mantém só os pacientes dentro de todos os intervalos escolhidos
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

st.caption(f"{len(df_filtrado)} de {len(df)} pacientes dentro dos intervalos escolhidos.")

# Dashboard 1: correlação (heatmap) à esquerda, distribuição (histograma) à direita
col_correlacao, col_distribuicao = st.columns([1, 1.5])

with col_correlacao:
    st.subheader("Correlação")

    if len(variaveis) < 2:
        st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
    else:
        # TODO: matriz de correlação das variáveis selecionadas (df_filtrado[variaveis].corr())
        # TODO: heatmap (plotly px.imshow) e exibir com st.plotly_chart
        pass

with col_distribuicao:
    st.subheader("Distribuição")

    # TODO: st.selectbox para escolher a variável do histograma
    # TODO: histograma (plotly px.histogram) e exibir com st.plotly_chart
    #       se separar_por_classe: color="doenca_cardiaca"

# TODO: Dashboard 2 — KPIs (Aula 22)
