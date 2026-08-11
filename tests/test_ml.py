import pandas as pd
import pytest

from survey.loading import activity_frame, load_all
from survey.ml import (
    DEFAULT_FEATURES,
    RANDOM_STATE,
    build_xy,
    cluster_labels,
    cluster_profile,
    cluster_scan,
    compare_models,
    logistic_coefficients,
    permutation_p,
)
from survey.scores import build_scores


@pytest.fixture(scope="module")
def frame():
    datasets = load_all(verbose=False)
    alvo = datasets["students_researchers_2026_04"]
    build_scores(alvo)
    return alvo


def test_features_padrao_sao_todas_do_bloco_geral(frame):
    blocos = frame.attrs["blocks"]
    for feature in DEFAULT_FEATURES:
        assert blocos[feature] == "general", feature


def test_build_xy_devolve_matriz_e_alvo_alinhados(frame):
    X, y = build_xy(frame, "dropped_courses")
    assert len(X) == len(y) == 39
    assert list(X.index) == list(y.index)
    assert X.notna().all().all()


def test_build_xy_tira_o_alvo_das_features(frame):
    # `participates_lab` está no conjunto padrão, então sem a exclusão o modelo
    # preveria a coluna a partir dela mesma e acertaria tudo.
    assert "participates_lab" in DEFAULT_FEATURES
    X, y = build_xy(frame, "participates_lab")
    assert "participates_lab" not in X.columns
    assert list(X.columns) == [f for f in DEFAULT_FEATURES if f != "participates_lab"]
    assert len(X.columns) == len(DEFAULT_FEATURES) - 1
    assert y.sum() == 25


def test_alvo_fora_do_conjunto_padrao_mantem_todas_as_features(frame):
    X, _ = build_xy(frame, "dropped_courses")
    assert list(X.columns) == list(DEFAULT_FEATURES)


def test_build_xy_recusa_feature_do_bloco_de_atividade_sem_recorte(frame):
    with pytest.raises(KeyError, match="activity_frame"):
        build_xy(frame, "dropped_courses", features=["burnout", "good_supervision"])


def test_build_xy_aceita_o_bloco_de_atividade_no_recorte(frame):
    recorte = activity_frame(frame)
    build_scores(recorte)
    X, y = build_xy(recorte, "considered_quitting_bin", features=["burnout", "lacks_time"])
    assert len(X) == 25
    assert list(X.columns) == ["burnout", "lacks_time"]


def test_build_xy_avisa_que_o_score_ainda_nao_foi_construido():
    cru = load_all(verbose=False)["students_researchers_2026_04"]
    with pytest.raises(KeyError, match="build_scores"):
        build_xy(cru, "dropped_courses")


def test_build_xy_recusa_alvo_que_nao_e_binario(frame):
    with pytest.raises(ValueError, match="binário"):
        build_xy(frame, "term")


def test_cluster_scan_compara_os_dois_metodos_por_k(frame):
    tabela = cluster_scan(frame, k_range=range(2, 6))
    assert list(tabela.index) == [2, 3, 4, 5]
    assert list(tabela.columns) == ["kmeans", "ward", "agreement"]
    assert round(tabela.loc[3, "kmeans"], 3) == 0.234
    assert round(tabela.loc[3, "ward"], 3) == 0.234


def test_os_dois_metodos_concordam_totalmente_em_tres_grupos(frame):
    tabela = cluster_scan(frame, k_range=range(2, 6))
    assert tabela.loc[3, "agreement"] == 1.0
    # Nos demais k a discordância nunca passa de duas respostas em 39.
    assert tabela["agreement"].min() * 39 >= 37


def test_a_silhueta_indica_separacao_fraca_em_todo_k(frame):
    # Registrado como resultado: nenhum k passa de 0,25, então os grupos existem
    # mas são pouco separados, e o texto precisa dizer isso.
    tabela = cluster_scan(frame, k_range=range(2, 6))
    assert tabela[["kmeans", "ward"]].to_numpy().max() < 0.25


def test_cluster_labels_e_deterministico(frame):
    a = cluster_labels(frame, k=3)
    b = cluster_labels(frame, k=3)
    pd.testing.assert_series_equal(a, b)
    assert sorted(a.value_counts().tolist()) == [10, 11, 18]


def test_cluster_labels_aceita_ward_e_bate_com_kmeans_em_tres_grupos(frame):
    kmeans = cluster_labels(frame, k=3, method="kmeans")
    ward = cluster_labels(frame, k=3, method="ward")
    assert pd.crosstab(kmeans, ward).max(axis=1).sum() == 39


def test_cluster_labels_recusa_metodo_desconhecido(frame):
    with pytest.raises(ValueError, match="floresta"):
        cluster_labels(frame, k=3, method="floresta")


def test_cluster_profile_traz_a_media_por_grupo_e_o_n_no_cabecalho(frame):
    labels = cluster_labels(frame, k=3)
    perfil = cluster_profile(frame, labels)
    assert list(perfil.index) == list(DEFAULT_FEATURES)
    assert [c.split("n=")[1].rstrip(")") for c in perfil.columns] == ["10", "11", "18"]


def test_cluster_profile_aceita_desfechos_extras(frame):
    labels = cluster_labels(frame, k=3)
    perfil = cluster_profile(frame, labels, extras=["change_major", "dropped_courses"])
    assert "dropped_courses" in perfil.index
    assert perfil.loc["works"].round(2).tolist() == [0.10, 1.00, 0.11]


def test_compare_models_poe_o_baseline_na_tabela(frame):
    X, y = build_xy(frame, "dropped_courses")
    tabela = compare_models(X, y)
    assert "baseline" in tabela.index
    assert list(tabela.columns) == ["mean", "sd"]
    assert round(tabela.loc["baseline", "mean"], 3) == 0.459


def test_a_logistica_supera_o_baseline_em_trancar_cadeiras(frame):
    X, y = build_xy(frame, "dropped_courses")
    tabela = compare_models(X, y)
    assert round(tabela.loc["logistica", "mean"], 3) == 0.690
    assert tabela.loc["logistica", "mean"] > tabela.loc["baseline", "mean"]
    assert tabela.index[0] == "logistica"


def test_permutation_p_confirma_que_o_modelo_aprendeu(frame):
    X, y = build_xy(frame, "dropped_courses")
    score, p = permutation_p(X, y, n_permutations=100)
    assert round(score, 3) == 0.690
    assert p < 0.05


def test_logistic_coefficients_sai_ordenado_pelo_modulo(frame):
    X, y = build_xy(frame, "dropped_courses")
    coeficientes = logistic_coefficients(X, y)
    assert coeficientes.abs().is_monotonic_decreasing
    assert coeficientes.index[0] == "participates_lab"
    assert round(coeficientes["keeps_up"], 3) == -0.512


def test_random_state_e_o_mesmo_em_todo_o_modulo():
    assert RANDOM_STATE == 42
