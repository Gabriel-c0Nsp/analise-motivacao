import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from survey.descriptive import compare_freq, crosstab_rowperc, freq_table  # noqa: E402
from survey.loading import load_all  # noqa: E402
from survey.ml import (  # noqa: E402
    build_xy,
    cluster_labels,
    cluster_profile,
    cluster_scan,
    compare_models,
    logistic_coefficients,
)
from survey.plots import (  # noqa: E402
    plot_cluster_profile,
    plot_coefficients,
    plot_compare,
    plot_crosstab,
    plot_dataset_comparison,
    plot_dendrogram,
    plot_freq,
    plot_model_comparison,
    plot_silhouette,
)
from survey.scores import build_scores  # noqa: E402
from survey.stats import compare_datasets  # noqa: E402


@pytest.fixture(scope="module")
def datasets():
    return load_all(verbose=False)


@pytest.fixture(scope="module")
def frame(datasets):
    alvo = datasets["students_researchers_2026_04"]
    build_scores(alvo)
    return alvo


def test_silhueta_desenha_uma_linha_por_metodo(frame):
    figura = plot_silhouette(cluster_scan(frame, k_range=range(2, 6)))
    eixo = figura.axes[0]
    assert len(eixo.lines) == 2
    assert [linha.get_label() for linha in eixo.lines] == ["K-means", "Hierárquico (Ward)"]
    assert [int(t) for t in eixo.get_xticks()] == [2, 3, 4, 5]


def test_silhueta_anota_a_concordancia_de_cada_k(frame):
    figura = plot_silhouette(cluster_scan(frame, k_range=range(2, 6)))
    textos = [t.get_text() for t in figura.axes[0].texts]
    assert "100% iguais" in textos
    assert len(textos) == 4


def test_perfil_escreve_o_valor_original_em_cada_celula(frame):
    labels = cluster_labels(frame, k=3)
    perfil = cluster_profile(frame, labels, extras=["dropped_courses"])
    figura = plot_cluster_profile(perfil)

    textos = [t.get_text() for t in figura.axes[0].texts]
    assert len(textos) == perfil.size
    assert "%.2f" % perfil.loc["works"].iloc[1] in textos


def test_perfil_normaliza_por_linha_e_nao_pela_tabela_inteira():
    perfil = pd.DataFrame(
        {"grupo 0 (n=2)": [1.0, 100.0], "grupo 1 (n=2)": [5.0, 500.0]},
        index=["pequena", "grande"],
    )
    figura = plot_cluster_profile(perfil)
    cores = figura.axes[0].images[0].get_array()

    assert cores[0].tolist() == cores[1].tolist() == [0.0, 1.0]


def test_perfil_aguenta_linha_sem_variacao_entre_grupos():
    perfil = pd.DataFrame(
        {"grupo 0 (n=2)": [3.0, 1.0], "grupo 1 (n=2)": [3.0, 9.0]},
        index=["constante", "varia"],
    )
    figura = plot_cluster_profile(perfil)
    assert figura.axes[0].images[0].get_array()[0].tolist() == [0.0, 0.0]


def test_coeficientes_desenham_uma_barra_por_variavel(frame):
    X, y = build_xy(frame, "dropped_courses")
    coeficientes = logistic_coefficients(X, y)
    figura = plot_coefficients(coeficientes)

    eixo = figura.axes[0]
    assert len(eixo.patches) == len(coeficientes)
    # O eixo vertical é invertido para o maior coeficiente ficar no topo.
    assert [t.get_text() for t in eixo.get_yticklabels()][-1] == coeficientes.index[0]


def test_coeficientes_separam_sinal_por_cor(frame):
    X, y = build_xy(frame, "dropped_courses")
    coeficientes = logistic_coefficients(X, y)
    figura = plot_coefficients(coeficientes)

    cores = {barra.get_facecolor() for barra in figura.axes[0].patches}
    assert len(cores) == 2


def test_comparacao_marca_o_acaso_e_destaca_o_baseline(frame):
    X, y = build_xy(frame, "dropped_courses")
    figura = plot_model_comparison(compare_models(X, y))
    eixo = figura.axes[0]

    assert [linha.get_xdata()[0] for linha in eixo.lines if linha.get_linestyle() == ":"] == [0.5]
    assert [t.get_text() for t in eixo.get_yticklabels()][-1] == "logistica"


def test_dendrograma_usa_uma_folha_por_resposta(frame):
    figura = plot_dendrogram(frame)
    eixo = figura.axes[0]
    assert eixo.get_ylabel() == "Distância de fusão"
    # Ward funde 39 folhas em 38 junções. O scipy agrupa os traços em coleções
    # por cor, então a contagem sai dos segmentos e não das coleções.
    segmentos = sum(len(colecao.get_segments()) for colecao in eixo.collections)
    assert segmentos == 38


def test_dendrograma_recusa_feature_do_bloco_de_atividade(frame):
    with pytest.raises(KeyError, match="activity_frame"):
        plot_dendrogram(frame, features=["burnout", "good_supervision"])


def test_freq_mantem_a_ordem_da_escala_e_nao_a_frequencia(datasets):
    tabela = freq_table(datasets["students_2025_06"], "keeps_up")
    figura = plot_freq(tabela, title="Acompanha o conteúdo")

    eixo = figura.axes[0]
    assert [t.get_text() for t in eixo.get_xticklabels()] == [str(i) for i in tabela.index]
    assert eixo.get_title() == "Acompanha o conteúdo"


def test_freq_escreve_contagem_e_percentual_em_cada_barra(datasets):
    tabela = freq_table(datasets["students_2025_06"], "works")
    figura = plot_freq(tabela)

    textos = [t.get_text() for t in figura.axes[0].texts]
    assert len(textos) == len(tabela)
    assert "9 (31.0%)" in textos


def test_crosstab_desenha_uma_barra_por_casa_da_tabela(datasets):
    tabela = crosstab_rowperc(datasets["students_2025_06"], "works", "dropped_courses")
    figura = plot_crosstab(tabela)

    assert len(figura.axes[0].patches) == tabela.size
    assert figura.axes[0].get_ylim() == (0.0, 100.0)


def test_compare_desenha_uma_serie_por_dataset(datasets):
    tabela = compare_freq(
        [datasets["students_2025_06"], datasets["students_researchers_2026_04"]], "keeps_up"
    )
    figura = plot_compare(tabela)

    assert len(figura.axes[0].patches) == tabela.size
    rotulos = [t.get_text() for t in figura.axes[0].get_legend().get_texts()]
    assert rotulos == ["Alunos 2025 (n=29)", "Pesquisa 2026 (n=39)"]


def test_comparacao_entre_datasets_destaca_o_que_tem_p_baixo(datasets):
    tabela = compare_datasets(
        datasets["students_2025_06"], datasets["students_researchers_2026_04"]
    )
    figura = plot_dataset_comparison(tabela)

    barras = figura.axes[0].patches
    assert len(barras) == len(tabela)
    # O destaque é vermelho e o resto é cinza, então o que separa os dois é a
    # distância entre os canais e não o vermelho sozinho.
    vermelhas = [b for b in barras if b.get_facecolor()[0] - b.get_facecolor()[1] > 0.3]
    assert len(vermelhas) == int((tabela["p"] < 0.05).sum()) == 5
