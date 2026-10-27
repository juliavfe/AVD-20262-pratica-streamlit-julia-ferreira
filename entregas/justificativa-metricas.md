# Justificativa das métricas — Dashboard 2

**Público-alvo geral:** equipe de curadoria/A&R de uma gravadora ou plataforma, que precisa decidir onde investir catálogo e promoção e não precisa captar as nuances estatísticas das variáveis.

**Widgets que controlam o dashboard:** gênero principal (multiselect), tipo de artista (multiselect), ano de estreia (slider) e clique numa barra de gênero (crossfilter via `on_select`).

## Métrica 1: Quantidade de artistas
- **Variável:** `Artist Name` (contagem de linhas após os filtros).
- **O que mede:** quantos artistas do ranking atendem aos filtros e ao gênero clicado.
- **Por que foi escolhida:** dá a base de comparação de todas as outras métricas; sem ela, uma mediana de 7 artistas parece tão sólida quanto a de 500.
- **Público-alvo:** equipe de curadoria/A&R.
- **Qual decisão pode ser apoiada por essa métrica?** Avaliar se um recorte (ex.: gênero + época) tem volume suficiente para tirar conclusões ou se é nicho.
- **O que comunica ao público-alvo:** o tamanho do recorte que está sendo analisado ("há 102 artistas de Pop no ranking").

## Métrica 2: Mediana de streams totais
- **Variável:** `Total Streams (in millions)`, exibida em bilhões.
- **O que mede:** o valor central de audiência do recorte: metade dos artistas tem mais streams que isso, metade menos.
- **Por que foi escolhida:** a distribuição de streams é muito assimétrica (poucos superastros com mais de 100 bi), então a média seria puxada por eles; a mediana representa o artista "típico" (Teoria de Métricas Básicas: medidas de tendência central e robustez a outliers).
- **Público-alvo:** equipe de curadoria/A&R.
- **Qual decisão pode ser apoiada por essa métrica?** Comparar o patamar de audiência entre gêneros e saber qual é a expectativa realista de um artista de cada segmento.
- **O que comunica ao público-alvo:** "o artista típico deste gênero tem cerca de X bilhões de streams", sem exigir leitura de histograma. O delta mostra se o gênero clicado está acima ou abaixo do conjunto filtrado.

## Métrica 3: Percentual médio de streams vindos de colaborações
- **Variável:** `% of Collaborative Streams`.
- **O que mede:** que parcela dos streams de um artista, em média, vem de faixas em colaboração (participações e feats) e não de faixas solo.
- **Por que foi escolhida:** já é uma proporção (0–100%), fácil de ler e comparável entre artistas de tamanhos muito diferentes; resume a relação solo × colaboração que o gráfico de dispersão detalha.
- **Público-alvo:** equipe de curadoria/A&R.
- **Qual decisão pode ser apoiada por essa métrica?** Decidir se vale priorizar parcerias e feats em um gênero ou apostar em lançamentos solo.
- **O que comunica ao público-alvo:** "em Reggaeton, cerca de X% da audiência vem de colaborações", mostrando o quanto o gênero depende de parcerias.

## Métrica 4: Percentual de artistas com performance alta
- **Variável:** `performance` (Alta/Baixa, derivada de `Total Streams (in millions)` na EDA).
- **O que mede:** a proporção de artistas do recorte classificados como performance Alta.
- **Por que foi escolhida:** resume em um único número se o recorte é dominado por artistas de topo ou de base, e usa a variável-alvo da análise do Dashboard 1.
- **Público-alvo:** equipe de curadoria/A&R.
- **Qual decisão pode ser apoiada por essa métrica?** Identificar gêneros e épocas em que a chance de um artista alcançar performance alta é maior.
- **O que comunica ao público-alvo:** "de cada 100 artistas deste recorte, X estão entre os de maior audiência". Como a classe foi definida pela divisão da amostra, o valor geral fica próximo de 50%; o que importa é o desvio em relação a isso.
