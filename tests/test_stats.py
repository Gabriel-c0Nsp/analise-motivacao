import pandas as pd
import pytest

from survey.loading import activity_frame, load_all
from survey.stats import cronbach_alpha, spearman_matrix, spearman_pairs

BELONGING = ["welcomed_by_faculty", "welcoming_environment", "teaching_quality"]
ACTIVITY = ["good_supervision", "recognition_motivates", "career_contribution"]


@pytest.fixture(scope="module")
def datasets():
    return load_all(verbose=False)


def test_alfa_de_itens_identicos_e_um():
    frame = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 2, 3, 4], "c": [1, 2, 3, 4]})
    assert cronbach_alpha(frame, ["a", "b", "c"]) == pytest.approx(1.0)


def test_alfa_de_itens_que_se_anulam_fica_negativo():
    frame = pd.DataFrame({"a": [1, 2, 3, 4], "b": [4, 3, 2, 2]})
    assert cronbach_alpha(frame, ["a", "b"]) < 0


def test_alfa_exige_pelo_menos_dois_itens():
    frame = pd.DataFrame({"a": [1, 2, 3, 4]})
    with pytest.raises(ValueError, match="dois itens"):
        cronbach_alpha(frame, ["a"])


def test_alfa_recusa_soma_sem_variancia():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1]})
    with pytest.raises(ValueError, match="variância"):
        cronbach_alpha(frame, ["a", "b"])


def test_alfa_do_pertencimento_em_2026(datasets):
    valor = cronbach_alpha(datasets["students_researchers_2026_04"], BELONGING)
    assert round(valor, 3) == 0.791


def test_alfa_do_bloco_de_atividade_e_recusado_sobre_o_quadro_inteiro(datasets):
    with pytest.raises(KeyError, match="activity_frame"):
        cronbach_alpha(datasets["students_researchers_2026_04"], ACTIVITY)


def test_alfa_do_bloco_de_atividade_sai_no_recorte(datasets):
    valor = cronbach_alpha(activity_frame(datasets["students_researchers_2026_04"]), ACTIVITY)
    assert round(valor, 3) == 0.331


def test_a_recusa_evita_um_alfa_inflado_pelos_nao_participantes(datasets):
    # Sem o recorte, as 14 respostas de quem não tem atividade entram no cálculo
    # e mais que dobram a confiabilidade aparente do bloco. O quadro sem metadado
    # escapa da recusa e mostra o número que a recusa existe para impedir.
    frame = datasets["students_researchers_2026_04"]
    contaminado = cronbach_alpha(pd.DataFrame(frame[ACTIVITY]), ACTIVITY)
    recortado = cronbach_alpha(activity_frame(frame), ACTIVITY)
    assert round(contaminado, 3) == 0.822
    assert contaminado > 2 * recortado


def test_alfa_do_bloco_de_atividade_passa_direto_em_2025(datasets):
    # O formulário de bolsistas só foi respondido por participantes, então não
    # há recorte a fazer e o cálculo não é recusado.
    valor = cronbach_alpha(datasets["researchers_2025_06"], ACTIVITY)
    assert round(valor, 3) == 0.650


def test_spearman_de_ordem_perfeita_e_um():
    frame = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
    matriz = spearman_matrix(frame, ["a", "b"])
    assert matriz.loc["a", "b"] == pytest.approx(1.0)


def test_spearman_de_ordem_invertida_e_menos_um():
    frame = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [50, 40, 30, 20, 10]})
    assert spearman_matrix(frame, ["a", "b"]).loc["a", "b"] == pytest.approx(-1.0)


def test_spearman_matrix_e_simetrica_com_diagonal_um(datasets):
    matriz = spearman_matrix(datasets["students_researchers_2026_04"], BELONGING)
    assert list(matriz.index) == BELONGING
    assert list(matriz.columns) == BELONGING
    for item in BELONGING:
        assert matriz.loc[item, item] == pytest.approx(1.0)
    for a in BELONGING:
        for b in BELONGING:
            assert matriz.loc[a, b] == pytest.approx(matriz.loc[b, a])


def test_spearman_matrix_recusa_bloco_de_atividade_sem_recorte(datasets):
    with pytest.raises(KeyError, match="activity_frame"):
        spearman_matrix(datasets["students_researchers_2026_04"], ACTIVITY)


def test_spearman_pairs_traz_rho_p_e_n(datasets):
    tabela = spearman_pairs(
        datasets["students_researchers_2026_04"],
        ["teaching_quality", "career_clarity"],
        ["change_major"],
    )
    assert list(tabela.columns) == ["rho", "p", "n"]
    linha = tabela.loc[("teaching_quality", "change_major")]
    assert round(linha["rho"], 2) == -0.45
    assert linha["n"] == 39
    assert linha["p"] < 0.05


def test_spearman_pairs_ordena_pelo_rho_mais_forte(datasets):
    # Ordem de entrada propositalmente crescente em módulo, para que a tabela
    # só saia ordenada se a função ordenar de fato.
    tabela = spearman_pairs(
        datasets["students_researchers_2026_04"],
        ["burnout", "career_clarity", "teaching_quality"],
        ["change_major"],
    )
    assert tabela.index[0] == ("teaching_quality", "change_major")
    assert tabela.index[-1] == ("burnout", "change_major")
    assert tabela["rho"].abs().is_monotonic_decreasing


def test_spearman_pairs_recusa_cruzar_bloco_de_atividade_sem_recorte(datasets):
    with pytest.raises(KeyError, match="activity_frame"):
        spearman_pairs(
            datasets["students_researchers_2026_04"], ["good_supervision"], ["change_major"]
        )
