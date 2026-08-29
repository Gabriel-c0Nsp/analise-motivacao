"""Figuras dos resultados de clusterização e predição.

Nenhuma função aqui calcula estatística. Todas recebem o resultado pronto dos
outros módulos e só desenham, para o número da figura ser o mesmo da tabela.

Nenhuma função escreve título por conta própria. No relatório, cada figura já é
identificada pela legenda numerada abaixo dela, e o título dentro do desenho
seria a mesma frase duas vezes. Quem quiser título na tela passa `title`, nas
funções que aceitam o argumento.
"""

from itertools import groupby

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram, linkage

from survey.ml import feature_matrix
from survey.schemas import LABELS

REPORT_DPI = 300
REPORT_FONT = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]
REPORT_FONT_SIZE = 10

# Largura útil da página do relatório, em polegadas: A4 de 21 cm menos as margens
# de 3 cm e 2 cm. A figura desenhada nessa largura entra no documento sem ser
# reduzida, e só assim o corpo declarado aqui é o corpo que sai impresso.
REPORT_WIDTH = 6.3

# O tamanho precisa ser declarado elemento a elemento, e não só em `font.size`,
# porque os padrões do matplotlib são relativos (`large`, `medium`) e sairiam
# maiores ou menores que o corpo pedido.
SIZED_KEYS = [
    "font.size",
    "axes.titlesize",
    "axes.labelsize",
    "xtick.labelsize",
    "ytick.labelsize",
    "legend.fontsize",
    "legend.title_fontsize",
    "figure.titlesize",
]


def report_rc(size=REPORT_FONT_SIZE):
    """Configuração de desenho do relatório: a fonte do texto, no corpo pedido.

    A figura é lida dentro do documento, então sai na mesma fonte dele. O corpo
    fica como argumento porque o tamanho aparente depende de quanto a figura é
    reduzida para caber na página, e isso só se decide vendo o documento pronto.
    """
    configuracao = {
        "font.family": "serif",
        "font.serif": REPORT_FONT,
        "mathtext.fontset": "stix",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": REPORT_DPI,
        "savefig.bbox": "tight",
    }
    configuracao.update(dict.fromkeys(SIZED_KEYS, size))
    return configuracao


def use_report_style(size=REPORT_FONT_SIZE):
    """Aplica a formatação do relatório a todas as figuras desenhadas em seguida.

    Chamar uma vez por sessão, antes de desenhar. Afeta o estado global do
    matplotlib, que é como a biblioteca expõe configuração de fonte.
    """
    plt.rcParams.update(report_rc(size))
    return plt.rcParams


def save_figure(fig, path, dpi=REPORT_DPI):
    """Grava a figura em 300 dpi, com margem justa e fundo branco."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return path


def _num(valor, casas=2):
    """Formata o número com vírgula decimal, como se escreve em português."""
    return ("%.*f" % (casas, valor)).replace(".", ",")


def plot_silhouette(scan, ax=None):
    """Silhueta dos dois métodos por número de grupos, com a concordância anotada."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))

    ax.plot(scan.index, scan["kmeans"], marker="o", label="K-means")
    ax.plot(scan.index, scan["ward"], marker="s", linestyle="--", label="Hierárquico (Ward)")
    for k, linha in scan.iterrows():
        ax.annotate(
            "%.0f%% iguais" % (linha["agreement"] * 100),
            (k, max(linha["kmeans"], linha["ward"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
        )

    ax.set_xticks(list(scan.index))
    ax.set_xlabel("Número de grupos")
    ax.set_ylabel("Silhueta média")
    ax.legend()
    ax.grid(alpha=0.3)
    return ax.figure


def plot_cluster_profile(profile, ax=None):
    """Mapa de calor do perfil dos grupos, cada variável normalizada na própria linha.

    A normalização por linha existe porque as variáveis têm faixas diferentes.
    A cor mostra onde cada grupo está alto ou baixo em relação aos outros, e o
    número escrito na célula é o valor original.

    A linha é identificada pelo rótulo legível de `LABELS`, e não pelo nome
    canônico da coluna, porque a figura sai do notebook e vai para quem lê o
    texto. Variável sem rótulo declarado aparece pelo nome canônico mesmo.
    """
    rotulos = [LABELS.get(nome, nome) for nome in profile.index]
    if ax is None:
        largura = 1.9 * len(profile.columns) + 0.11 * max(len(rotulo) for rotulo in rotulos) + 1
        _, ax = plt.subplots(figsize=(largura, 0.45 * len(profile) + 2))

    faixa = profile.max(axis=1) - profile.min(axis=1)
    normalizado = profile.sub(profile.min(axis=1), axis=0).div(faixa.replace(0, 1), axis=0)

    ax.imshow(normalizado, aspect="auto", cmap="RdYlBu_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(profile.columns)), profile.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(profile.index)), rotulos)

    for i in range(len(profile.index)):
        for j in range(len(profile.columns)):
            ax.text(j, i, _num(profile.iloc[i, j]), ha="center", va="center")

    return ax.figure


def plot_coefficients(coefficients, ax=None):
    """Coeficientes da logística em barras, do maior módulo ao menor."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.45 * len(coefficients) + 2))

    ordenado = coefficients.iloc[::-1]
    cores = ["#c0392b" if v > 0 else "#2471a3" for v in ordenado]
    ax.barh(ordenado.index, ordenado.to_numpy(), color=cores)

    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Coeficiente sobre a variável padronizada")
    ax.grid(axis="x", alpha=0.3)
    return ax.figure


def plot_model_comparison(comparison, ax=None):
    """Média e desvio de cada modelo, com o acaso marcado em 0,5."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.7 * len(comparison) + 2))

    ordenado = comparison.iloc[::-1]
    cores = ["#7f8c8d" if nome == "baseline" else "#2471a3" for nome in ordenado.index]
    ax.barh(ordenado.index, ordenado["mean"], xerr=ordenado["sd"], color=cores, capsize=4)

    ax.axvline(0.5, color="black", linestyle=":", linewidth=1)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Acurácia balanceada (média e desvio das dobras)")
    return ax.figure


def plot_dendrogram(dataset, features=None, group_names=None, ax=None):
    """Dendrograma de Ward sobre a mesma matriz padronizada da clusterização.

    `group_names` nomeia os blocos coloridos, da esquerda para a direita. O
    nome e o tamanho de cada bloco saem do próprio desenho, e não de uma
    partição calculada à parte, para a legenda não poder discordar da figura.
    Sem os nomes a figura sai sem legenda, e quem a lê não tem como saber qual
    bloco é qual.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    _, values = feature_matrix(dataset, features)
    desenho = dendrogram(
        linkage(values, method="ward"), ax=ax, no_labels=True, color_threshold=None
    )

    if group_names is not None:
        blocos = [(cor, len(list(folhas))) for cor, folhas in groupby(desenho["leaves_color_list"])]
        if len(blocos) != len(group_names):
            raise ValueError(
                "a árvore tem %d bloco(s) colorido(s) e vieram %d nome(s)"
                % (len(blocos), len(group_names))
            )
        # A legenda fica dentro do eixo, e a árvore ocupa o topo à direita. Sem
        # a folga, a caixa cobre as fusões mais altas, que são justamente as
        # que separam os grupos. A altura da caixa cresce com o número de
        # nomes, então a folga acompanha essa contagem.
        ax.set_ylim(top=ax.get_ylim()[1] * (1.2 + 0.12 * len(group_names)))
        ax.legend(
            handles=[
                Patch(color=cor, label="%s (n=%d)" % (nome, tamanho))
                for (cor, tamanho), nome in zip(blocos, group_names)
            ],
            loc="upper right",
        )

    ax.set_xlabel("Respostas")
    ax.set_ylabel("Distância de fusão")
    return ax.figure


def plot_freq(table, title=None, ax=None):
    """Distribuição de uma variável em barras, na ordem em que a tabela chegou.

    Recebe a saída de `freq_table`, que já ordenou pela escala e não pela
    frequência. Reordenar aqui desmancharia uma escala Likert.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(max(6, 0.9 * len(table)), 4))

    ax.bar([str(rotulo) for rotulo in table.index], table["percent"], color="#2471a3")
    for x, (contagem, percentual) in enumerate(zip(table["count"], table["percent"])):
        ax.text(x, percentual, "%d (%s%%)" % (contagem, _num(percentual, 1)), ha="center",
                va="bottom")

    ax.set_ylabel("% das respostas")
    ax.set_ylim(0, max(table["percent"]) * 1.18)
    ax.tick_params(axis="x", rotation=20)
    for rotulo in ax.get_xticklabels():
        rotulo.set_horizontalalignment("right")
    if title:
        ax.set_title(title)
    return ax.figure


def plot_crosstab(table, title=None, ax=None):
    """Percentuais por linha em barras agrupadas, uma cor por coluna da tabela."""
    if ax is None:
        _, ax = plt.subplots(figsize=(max(6, 1.6 * len(table)), 4))

    table.plot.bar(ax=ax, rot=0, width=0.75, colormap="tab10")
    ax.set_ylabel("% da linha")
    ax.set_ylim(0, 100)
    ax.legend(title=table.columns.name)
    if title:
        ax.set_title(title)
    return ax.figure


def plot_compare(table, title=None, ax=None):
    """Comparação entre datasets em barras agrupadas, uma cor por dataset.

    Recebe a saída de `compare_freq` ou `compare_items`, cujo cabeçalho já traz
    o número de respostas que serve de denominador de cada percentual.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(max(7, 1.4 * len(table)), 4))

    table.plot.bar(ax=ax, rot=20, width=0.75, color=["#7f8c8d", "#2471a3", "#c0392b"][: len(table.columns)])
    for rotulo in ax.get_xticklabels():
        rotulo.set_horizontalalignment("right")

    ax.set_ylabel("% das respostas do dataset")
    ax.legend()
    if title:
        ax.set_title(title)
    return ax.figure


def plot_dataset_comparison(comparison, ax=None):
    """Tamanho e sinal da diferença entre dois datasets, variável por variável.

    Recebe a saída de `compare_datasets`. A barra é a correlação bisserial de
    postos, positiva quando o segundo dataset tem valores mais altos, e as
    variáveis com p abaixo de 0,05 saem destacadas.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 0.42 * len(comparison) + 2))

    ordenado = comparison.iloc[::-1]
    cores = ["#c0392b" if p < 0.05 else "#bdc3c7" for p in ordenado["p"]]
    ax.barh(ordenado.index, ordenado["effect"], color=cores)

    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Efeito (positivo: o segundo dataset tem valores mais altos)")
    ax.grid(axis="x", alpha=0.3)
    return ax.figure
