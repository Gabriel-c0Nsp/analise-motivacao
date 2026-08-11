"""Figuras dos resultados de clusterização e predição.

Nenhuma função aqui calcula estatística. Todas recebem o resultado pronto dos
outros módulos e só desenham, para o número da figura ser o mesmo da tabela.
"""

import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage

from survey.ml import feature_matrix


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
            fontsize=8,
        )

    ax.set_xticks(list(scan.index))
    ax.set_xlabel("Número de grupos")
    ax.set_ylabel("Silhueta média")
    ax.set_title("Separação dos grupos e concordância entre os dois métodos")
    ax.legend()
    ax.grid(alpha=0.3)
    return ax.figure


def plot_cluster_profile(profile, ax=None):
    """Mapa de calor do perfil dos grupos, cada variável normalizada na própria linha.

    A normalização por linha existe porque as variáveis têm faixas diferentes.
    A cor mostra onde cada grupo está alto ou baixo em relação aos outros, e o
    número escrito na célula é o valor original.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(1.9 * len(profile.columns) + 3, 0.45 * len(profile) + 2))

    faixa = profile.max(axis=1) - profile.min(axis=1)
    normalizado = profile.sub(profile.min(axis=1), axis=0).div(faixa.replace(0, 1), axis=0)

    ax.imshow(normalizado, aspect="auto", cmap="RdYlBu_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(profile.columns)), profile.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(profile.index)), profile.index)

    for i in range(len(profile.index)):
        for j in range(len(profile.columns)):
            ax.text(
                j, i, "%.2f" % profile.iloc[i, j], ha="center", va="center", fontsize=9
            )

    ax.set_title("Perfil médio de cada grupo")
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
    ax.set_title("Peso de cada variável na predição")
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
    ax.set_title("Cada modelo contra o baseline")
    return ax.figure


def plot_dendrogram(dataset, features=None, ax=None):
    """Dendrograma de Ward sobre a mesma matriz padronizada da clusterização."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    _, values = feature_matrix(dataset, features)
    dendrogram(linkage(values, method="ward"), ax=ax, no_labels=True, color_threshold=None)

    ax.set_xlabel("Respostas")
    ax.set_ylabel("Distância de fusão")
    ax.set_title("Agrupamento hierárquico (Ward)")
    return ax.figure
