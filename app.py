import altair as alt
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Artistas mais ouvidos — Spotify",
    layout="wide",
)

st.title("Artistas mais ouvidos no Spotify")

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
COLUNA_GENERO = "Primary Genre"
ORDEM_DECADAS = ["<1990", "1990s", "2000s", "2010s", "2020s"]
COR_DESTAQUE = "#1ed760"
CORES_CLASSE = alt.Scale(domain=["Alta", "Baixa"], range=[COR_DESTAQUE, "#8a8f98"])


@st.cache_data
def calcular_correlacao(dados: pd.DataFrame, variaveis: tuple, metodo: str) -> pd.DataFrame:
    """Matriz de correlação em formato longo (uma linha por par), pronta para o heatmap."""
    matriz = dados[list(variaveis)].corr(method=metodo)
    longo = matriz.stack().reset_index()
    longo.columns = ["x", "y", "correlacao"]
    return longo


@st.cache_data
def mediana_por_decada(dados: pd.DataFrame) -> pd.DataFrame:
    """Mediana de streams totais (em bilhões) por década de estreia."""
    agrupado = dados.groupby("faixa_etaria")["Total Streams (in millions)"].agg(["median", "size"])
    agrupado = agrupado.reset_index().rename(columns={"median": "mediana", "size": "artistas"})
    agrupado["mediana"] = agrupado["mediana"] / 1000
    return agrupado


def grafico_correlacao(dados: pd.DataFrame, variaveis: list, metodo: str) -> alt.Chart:
    longo = calcular_correlacao(dados, tuple(variaveis), metodo)
    ordem = list(variaveis)
    base = alt.Chart(longo).encode(
        x=alt.X("x:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("y:N", sort=ordem, title=None),
    )
    mapa = base.mark_rect().encode(
        color=alt.Color(
            "correlacao:Q",
            scale=alt.Scale(scheme="redblue", domain=[-1, 1]),
            legend=alt.Legend(title=f"Correlação ({metodo})"),
        ),
        tooltip=["x:N", "y:N", alt.Tooltip("correlacao:Q", format=".2f")],
    )
    texto = base.mark_text(fontSize=13).encode(
        text=alt.Text("correlacao:Q", format=".2f"),
        color=alt.condition(
            "abs(datum.correlacao) > 0.6", alt.value("white"), alt.value("black")
        ),
    )
    return (mapa + texto).properties(height=380)


def grafico_histograma(dados: pd.DataFrame, variavel: str, separar: bool) -> alt.Chart:
    grafico = (
        alt.Chart(dados)
        .mark_bar(opacity=0.7 if separar else 1, color=COR_DESTAQUE)
        .encode(
            x=alt.X(variavel, type="quantitative", bin=alt.Bin(maxbins=30), title=variavel),
            y=alt.Y("count()", stack=None, title="Quantidade de artistas"),
            tooltip=[alt.Tooltip("count()", title="Artistas")],
        )
        .properties(title=variavel, height=260)
    )
    if separar:
        grafico = grafico.encode(
            color=alt.Color(COLUNA_CLASSE, type="nominal", scale=CORES_CLASSE, title="Performance")
        )
    return grafico


def dashboard_1(dados: pd.DataFrame) -> None:
    st.caption("Explore como as métricas de streaming e o ano de estreia se relacionam.")

    # Sidebar: filtros (variáveis + intervalo) do Dashboard 1
    with st.sidebar:
        st.header("Filtros — Dashboard 1")

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
            if pd.api.types.is_integer_dtype(dados[var]):
                minimo, maximo, passo = int(dados[var].min()), int(dados[var].max()), 1
            else:
                minimo, maximo, passo = float(dados[var].min()), float(dados[var].max()), 0.1
            if minimo == maximo:
                continue  # o slider exige min < max
            intervalos[var] = st.slider(
                f"Intervalo de {var}",
                min_value=minimo,
                max_value=maximo,
                value=(minimo, maximo),
                step=passo,
                key=f"intervalo_{var}",
            )

    # Mantém só os artistas dentro de todos os intervalos escolhidos
    filtrado = dados
    for var, (inicio, fim) in intervalos.items():
        filtrado = filtrado[filtrado[var].between(inicio, fim)]

    st.caption(f"{len(filtrado)} de {len(dados)} artistas dentro dos intervalos escolhidos.")

    st.subheader("Correlação")
    if len(variaveis) < 2:
        st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
    elif len(filtrado) < 3:
        st.info("Poucos artistas nos intervalos escolhidos para calcular a correlação.")
    else:
        metodo = st.selectbox(
            "Método de correlação",
            options=["spearman", "kendall", "pearson"],
            index=0,
            help="Spearman é o método usado como principal na EDA deste dataset.",
        )
        st.altair_chart(grafico_correlacao(filtrado, variaveis, metodo), width="stretch")

    st.subheader("Distribuição das variáveis selecionadas")
    if not variaveis:
        st.info("Selecione pelo menos uma variável quantitativa na barra lateral.")
    elif filtrado.empty:
        st.info("Nenhum artista corresponde aos intervalos selecionados.")
    else:
        colunas = st.columns(2)
        for indice, variavel in enumerate(variaveis):
            with colunas[indice % 2]:
                st.altair_chart(
                    grafico_histograma(filtrado, variavel, separar_por_classe),
                    width="stretch",
                    key=f"distribuicao_{indice}",
                )


def dashboard_2(dados: pd.DataFrame) -> None:
    st.caption(
        "Visão executiva para quem decide o catálogo: quais gêneros e épocas concentram "
        "audiência e quanto dela vem de colaborações. Clique numa barra de gênero para "
        "filtrar os indicadores e os outros gráficos."
    )

    # Widgets que controlam o dashboard
    col_generos, col_sexo, col_ano = st.columns([2, 1, 2])
    generos = col_generos.multiselect(
        "Gênero principal",
        options=sorted(dados[COLUNA_GENERO].unique()),
        placeholder="Todos os gêneros",
    )
    sexos = col_sexo.multiselect(
        "Tipo de artista",
        options=sorted(dados["sexo_label"].unique()),
        placeholder="Todos",
    )
    ano_min, ano_max = int(dados["Debut Year"].min()), int(dados["Debut Year"].max())
    anos = col_ano.slider("Ano de estreia", ano_min, ano_max, (ano_min, ano_max))

    base = dados[dados["Debut Year"].between(*anos)]
    if generos:
        base = base[base[COLUNA_GENERO].isin(generos)]
    if sexos:
        base = base[base["sexo_label"].isin(sexos)]

    if base.empty:
        st.info("Nenhum artista corresponde aos filtros escolhidos.")
        return

    # Gráfico de gêneros: o clique numa barra filtra o restante (via on_select)
    clique = alt.selection_point(name="genero", fields=[COLUNA_GENERO])
    barras = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            y=alt.Y(f"{COLUNA_GENERO}:N", sort="-x", title=None),
            x=alt.X("count()", title="Quantidade de artistas"),
            color=alt.value(COR_DESTAQUE),
            opacity=alt.condition(clique, alt.value(1), alt.value(0.35)),
            tooltip=[COLUNA_GENERO, alt.Tooltip("count()", title="Artistas")],
        )
        .add_params(clique)
        .properties(title="Artistas por gênero (clique para filtrar)", height=420)
    )

    col_barras, col_kpis = st.columns([2, 3])
    with col_barras:
        evento = st.altair_chart(barras, key="d2_generos", on_select="rerun", width="stretch")

    selecionados = [item[COLUNA_GENERO] for item in evento.selection.get("genero", [])]
    recorte = base[base[COLUNA_GENERO].isin(selecionados)] if selecionados else base

    # KPIs calculados sobre o recorte; delta compara com os filtros sem o clique
    def delta(valor_recorte: float, valor_base: float, formato: str) -> str | None:
        if not selecionados:
            return None
        return format(valor_recorte - valor_base, formato)

    total = recorte["Total Streams (in millions)"].median() / 1000
    total_base = base["Total Streams (in millions)"].median() / 1000
    colab = recorte["% of Collaborative Streams"].mean()
    colab_base = base["% of Collaborative Streams"].mean()
    alta = (recorte[COLUNA_CLASSE] == "Alta").mean() * 100
    alta_base = (base[COLUNA_CLASSE] == "Alta").mean() * 100

    with col_kpis:
        k1, k2 = st.columns(2)
        k3, k4 = st.columns(2)
        k1.metric("Artistas", f"{len(recorte)}", delta(len(recorte), len(base), "+d"),
                  help="Quantos artistas atendem aos filtros e ao clique.")
        k2.metric("Streams totais (mediana)", f"{total:.1f} bi",
                  delta(total, total_base, "+.1f"),
                  help="Mediana de Total Streams, em bilhões. Resiste a superastros.")
        k3.metric("Streams de colaborações (média)", f"{colab:.0f}%",
                  delta(colab, colab_base, "+.0f"),
                  help="Parcela média dos streams que vem de colaborações.")
        k4.metric("Artistas de performance alta", f"{alta:.0f}%",
                  delta(alta, alta_base, "+.0f"),
                  help="Proporção de artistas classificados com performance Alta.")

        decadas = mediana_por_decada(recorte)
        st.altair_chart(
            alt.Chart(decadas)
            .mark_bar(color=COR_DESTAQUE)
            .encode(
                x=alt.X("faixa_etaria:N", sort=ORDEM_DECADAS, title="Década de estreia"),
                y=alt.Y("mediana:Q", title="Mediana de streams (bi)"),
                tooltip=[
                    alt.Tooltip("faixa_etaria:N", title="Década"),
                    alt.Tooltip("mediana:Q", title="Mediana (bi)", format=".1f"),
                    alt.Tooltip("artistas:Q", title="Artistas"),
                ],
            )
            .properties(title="Mediana de streams por década de estreia", height=190),
            width="stretch",
        )

    st.altair_chart(
        alt.Chart(recorte)
        .mark_circle(size=60, opacity=0.7)
        .encode(
            x=alt.X("Solo Streams (in millions):Q", scale=alt.Scale(type="symlog"),
                    title="Streams solo (milhões)"),
            y=alt.Y("Collaborative Streams (in millions):Q", scale=alt.Scale(type="symlog"),
                    title="Streams de colaborações (milhões)"),
            color=alt.Color(f"{COLUNA_CLASSE}:N", scale=CORES_CLASSE, title="Performance"),
            tooltip=[
                "Artist Name",
                COLUNA_GENERO,
                alt.Tooltip("Solo Streams (in millions):Q", format=",.0f"),
                alt.Tooltip("Collaborative Streams (in millions):Q", format=",.0f"),
            ],
        )
        .properties(title="Streams solo x colaborações por artista", height=340),
        width="stretch",
    )


aba_1, aba_2 = st.tabs(["Dashboard 1 — Correlação", "Dashboard 2 — Indicadores"])
with aba_1:
    dashboard_1(df)
with aba_2:
    dashboard_2(df)
