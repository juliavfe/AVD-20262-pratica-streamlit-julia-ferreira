import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Artistas mais ouvidos — Spotify",
    layout="wide",
)

st.title("Artistas mais ouvidos no Spotify")

df = load_data()

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
    triangulo = np.tril(np.ones(matriz.shape, dtype=bool))
    longo = matriz.where(triangulo).stack().reset_index()
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
            scale=alt.Scale(domain=[-1, 0, 1], range=["#191414", "#dfe5e1", COR_DESTAQUE]),
            legend=alt.Legend(title=f"Correlação ({metodo})"),
        ),
        tooltip=["x:N", "y:N", alt.Tooltip("correlacao:Q", format=".2f")],
    )
    texto = base.mark_text(fontSize=13).encode(
        text=alt.Text("correlacao:Q", format=".2f"),
        color=alt.condition("datum.correlacao < -0.45", alt.value("white"), alt.value("black")),
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
            color=alt.Color(COLUNA_CLASSE, type="nominal", scale=CORES_CLASSE, legend=None)
        )
    return grafico


def dashboard_1(dados: pd.DataFrame) -> None:
    st.caption("Explore como as métricas de streaming e o ano de estreia se relacionam.")

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

        intervalos = {}
        for var in variaveis:
            if pd.api.types.is_integer_dtype(dados[var]):
                minimo, maximo, passo = int(dados[var].min()), int(dados[var].max()), 1
            else:
                minimo, maximo, passo = float(dados[var].min()), float(dados[var].max()), 0.1
            if minimo == maximo:
                continue 
            intervalos[var] = st.slider(
                f"Intervalo de {var}",
                min_value=minimo,
                max_value=maximo,
                value=(minimo, maximo),
                step=passo,
                key=f"intervalo_{var}",
            )

    filtrado = dados
    for var, (inicio, fim) in intervalos.items():
        filtrado = filtrado[filtrado[var].between(inicio, fim)]

    st.caption(f"{len(filtrado)} de {len(dados)} artistas dentro dos intervalos escolhidos.")

    st.subheader("Matriz de correlacao")
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
        st.altair_chart(
            grafico_correlacao(filtrado, variaveis, metodo),
            width="stretch",
            alt=f"Mapa de correlação pelo método {metodo} para as variáveis quantitativas selecionadas.",
        )

    st.subheader("Distribuição das variáveis selecionadas")
    if not variaveis:
        st.info("Selecione pelo menos uma variável quantitativa na barra lateral.")
    elif filtrado.empty:
        st.info("Nenhum artista corresponde aos intervalos selecionados.")
    else:
        if separar_por_classe:
            st.markdown(
                f"**Performance:** <span style='color:{COR_DESTAQUE}'>●</span> Alta &nbsp; "
                "<span style='color:#8a8f98'>●</span> Baixa",
                unsafe_allow_html=True,
            )
        colunas = st.columns(2)
        for indice, variavel in enumerate(variaveis):
            with colunas[indice % 2]:
                st.altair_chart(
                    grafico_histograma(filtrado, variavel, separar_por_classe),
                    width="stretch",
                    key=f"distribuicao_{indice}",
                    alt=f"Distribuição de {variavel} entre os artistas selecionados.",
                )


def dashboard_2(dados: pd.DataFrame) -> None:
    st.caption(
        "Visão executiva para quem decide o catálogo: quais gêneros e épocas concentram "
        "audiência e quanto dela vem de colaborações. Clique numa barra de gênero para "
        "filtrar os indicadores e os outros gráficos."
    )

    with st.sidebar:
        st.header("Filtros — Dashboard 2")
        generos = st.multiselect(
            "Gênero principal",
            options=sorted(dados[COLUNA_GENERO].unique()),
            placeholder="Todos os gêneros",
            key="d2_filtro_generos",
        )
        sexos = st.multiselect(
            "Tipo de artista",
            options=sorted(dados["sexo_label"].unique()),
            placeholder="Todos",
            key="d2_filtro_sexos",
        )
        ano_min, ano_max = int(dados["Debut Year"].min()), int(dados["Debut Year"].max())
        anos = st.slider(
            "Ano de estreia", ano_min, ano_max, (ano_min, ano_max), key="d2_filtro_anos"
        )

    base = dados[dados["Debut Year"].between(*anos)]
    if generos:
        base = base[base[COLUNA_GENERO].isin(generos)]
    if sexos:
        base = base[base["sexo_label"].isin(sexos)]

    if base.empty:
        st.info("Nenhum artista corresponde aos filtros escolhidos.")
        return

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
        evento = st.altair_chart(
            barras,
            key="d2_generos",
            on_select="rerun",
            width="stretch",
            alt="Contagem de artistas por gênero principal; clique em um gênero para filtrar o painel.",
        )

    selecionados = [item[COLUNA_GENERO] for item in evento.selection.get("genero", [])]
    recorte = base[base[COLUNA_GENERO].isin(selecionados)] if selecionados else base

    def delta(valor_recorte: float, valor_base: float, formato: str) -> str | None:
        if not selecionados:
            return None
        return format(valor_recorte - valor_base, formato)

    total = recorte["Total Streams (in millions)"].median() / 1000
    total_base = base["Total Streams (in millions)"].median() / 1000
    ano = recorte["Debut Year"].median()
    ano_base = base["Debut Year"].median()
    n_generos = recorte["Primary Genre"].nunique()
    n_generos_base = base["Primary Genre"].nunique()
    TIPO_ALVO = "Feminino"
    tipo = (recorte["sexo_label"] == TIPO_ALVO).mean() * 100
    tipo_base = (base["sexo_label"] == TIPO_ALVO).mean() * 100


    with col_kpis:
        k1, k2 = st.columns(2)
        k1.metric("Artistas", f"{len(recorte)}", delta(len(recorte), len(base), "+d"),
                  help="Quantos artistas atendem aos filtros e ao clique.")
        k2.metric("Streams totais (mediana)", f"{total:.1f} bi",
                  delta(total, total_base, "+.1f"),
                  help="Mediana de Total Streams, em bilhões. Resiste a superastros.")
        k3, k4 = st.columns(2)
        k3.metric("Ano de estreia (mediana)", f"{ano:.0f}",
                  delta(ano, ano_base, "+.0f"),
                  help="Ano mediano de estreia dos artistas no recorte.")
        k4.metric("Gêneros", f"{n_generos}",
                  delta(n_generos, n_generos_base, "+d"),
                  help="Quantos gêneros aparecem no recorte.")
        k5, _ = st.columns(2)
        k5.metric(f"Artistas {TIPO_ALVO.lower()}s (%)", f"{tipo:.0f}%",
                  delta(tipo, tipo_base, "+.0f"),
                  help=f"Percentual de artistas do tipo {TIPO_ALVO} no recorte.")



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
            alt="Mediana de streams totais por década de estreia dos artistas filtrados.",
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
        alt="Relação entre streams solo e colaborativos para cada artista, com cor indicando a performance.",
    )


DASHBOARDS = {
    "Dashboard 1 — Correlação": dashboard_1,
    "Dashboard 2 — Indicadores": dashboard_2,
}
escolhido = st.radio("Dashboard", list(DASHBOARDS), horizontal=True, label_visibility="collapsed")
DASHBOARDS[escolhido](df)
