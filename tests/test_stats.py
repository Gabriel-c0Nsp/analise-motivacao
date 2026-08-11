import pandas as pd
import pytest

from survey.loading import activity_frame, load_all, to_agreement
from survey.stats import (
    compare_datasets,
    cronbach_alpha,
    fisher,
    mann_whitney,
    spearman_matrix,
    spearman_pairs,
)

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


def test_spearman_pairs_anuncia_preditor_constante_em_vez_de_avisar_pelo_scipy(datasets, capsys):
    # Dentro do recorte, a própria coluna que define o recorte vale 1 em todas
    # as linhas e não tem correlação com nada.
    recorte = activity_frame(datasets["students_researchers_2026_04"])
    tabela = spearman_pairs(recorte, ["participates_lab"], ["considered_quitting_bin"])

    assert pd.isna(tabela.loc[("participates_lab", "considered_quitting_bin"), "rho"])
    assert tabela.loc[("participates_lab", "considered_quitting_bin"), "n"] == 25
    assert "participates_lab" in capsys.readouterr().out


def test_o_recorte_muda_a_forca_da_relacao_entre_falta_de_tempo_e_desistir(datasets):
    # As 14 respostas de quem não tem atividade atenuam a associação: sobre as
    # 39 o rho é 0,33 e sobre os 25 participantes é 0,51, mais da metade maior.
    frame = datasets["students_researchers_2026_04"]
    solto = pd.DataFrame(frame[["lacks_time", "considered_quitting_bin"]])
    contaminado = spearman_pairs(solto, ["lacks_time"], ["considered_quitting_bin"])
    recortado = spearman_pairs(
        activity_frame(frame), ["lacks_time"], ["considered_quitting_bin"]
    )

    assert round(contaminado.iloc[0]["rho"], 3) == 0.332
    assert round(recortado.iloc[0]["rho"], 3) == 0.513
    assert recortado.iloc[0]["p"] < contaminado.iloc[0]["p"] < 0.05


def test_spearman_pairs_recusa_cruzar_bloco_de_atividade_sem_recorte(datasets):
    with pytest.raises(KeyError, match="activity_frame"):
        spearman_pairs(
            datasets["students_researchers_2026_04"], ["good_supervision"], ["change_major"]
        )


def test_fisher_confirma_a_relacao_entre_trabalhar_e_trancar(datasets):
    resultado = fisher(datasets["students_2025_06"], "works", "dropped_courses")
    assert resultado["n"] == 29
    assert round(resultado["odds_ratio"], 3) == 18.667
    assert round(resultado["p"], 6) == 0.005197


def test_fisher_sobre_item_likert_dicotomizado(datasets):
    frame = datasets["researchers_2025_06"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    frame.attrs["derived"] = []
    derivado = to_agreement(frame, "stipend_enough")
    resultado = fisher(frame, derivado, "considered_quitting")

    assert derivado == "stipend_enough_bin"
    assert resultado["n"] == 25
    assert round(resultado["p"], 6) == 0.041405
    assert resultado["odds_ratio"] < 1


def test_fisher_recusa_variavel_que_nao_e_binaria(datasets):
    with pytest.raises(ValueError, match="to_agreement"):
        fisher(datasets["students_2025_06"], "keeps_up", "works")


def test_fisher_recusa_tabela_que_nao_e_2x2():
    frame = pd.DataFrame({"a": [0.0, 1.0, 1.0], "b": [1.0, 1.0, 1.0]})
    frame.attrs.update(kinds={"a": "binary", "b": "binary"}, blocks={}, activity_scope=None)
    with pytest.raises(ValueError, match="2x1"):
        fisher(frame, "a", "b")


def test_to_agreement_usa_o_limiar_de_concordancia(datasets):
    frame = datasets["students_2025_06"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    frame.attrs["derived"] = []

    to_agreement(frame, "keeps_up")

    esperado = datasets["students_2025_06"]["keeps_up"].ge(4).sum()
    assert frame["keeps_up_bin"].sum() == esperado
    assert frame.attrs["kinds"]["keeps_up_bin"] == "binary"


def test_to_agreement_recusa_tipo_sem_ordem_de_concordancia(datasets):
    with pytest.raises(ValueError, match="Likert ou binário"):
        to_agreement(datasets["students_2025_06"], "curriculum_rating")


def test_mann_whitney_mede_o_avanco_de_sentir_se_preparado(datasets):
    resultado = mann_whitney(
        datasets["students_2025_06"], datasets["students_researchers_2026_04"], "job_ready"
    )
    assert (resultado["n_1"], resultado["n_2"]) == (29, 39)
    assert round(resultado["mean_1"], 2) == 2.17
    assert round(resultado["mean_2"], 2) == 3.23
    assert round(resultado["p"], 4) == 0.0005
    assert resultado["effect"] > 0


def test_o_sinal_do_efeito_aponta_o_dataset_com_valores_mais_altos(datasets):
    alunos, pesquisa = datasets["students_2025_06"], datasets["students_researchers_2026_04"]
    direto = mann_whitney(alunos, pesquisa, "job_ready")
    invertido = mann_whitney(pesquisa, alunos, "job_ready")

    assert direto["effect"] == pytest.approx(-invertido["effect"])
    assert direto["p"] == pytest.approx(invertido["p"])


def test_mann_whitney_recusa_variavel_de_tipo_diferente_entre_os_datasets(datasets):
    with pytest.raises(KeyError, match="considered_quitting"):
        mann_whitney(
            datasets["researchers_2025_06"],
            datasets["students_researchers_2026_04"],
            "considered_quitting",
        )


def test_mann_whitney_recusa_categorica(datasets):
    with pytest.raises(ValueError, match="categórica"):
        mann_whitney(
            datasets["students_2025_06"], datasets["students_researchers_2026_04"], "age_range"
        )


def test_compare_datasets_cobre_as_comparaveis_e_descarta_a_categorica(datasets):
    tabela = compare_datasets(
        datasets["students_2025_06"], datasets["students_researchers_2026_04"]
    )
    assert len(tabela) == 14
    assert "age_range" not in tabela.index
    assert list(tabela.columns) == ["n_1", "n_2", "mean_1", "mean_2", "delta", "U", "p", "effect"]


def test_compare_datasets_ordena_da_menor_para_a_maior_p(datasets):
    tabela = compare_datasets(
        datasets["students_2025_06"], datasets["students_researchers_2026_04"]
    )
    assert tabela["p"].is_monotonic_increasing
    assert tabela.index[0] == "job_ready"
    assert tabela.index[-1] == "dropped_courses"


def test_cinco_variaveis_mudaram_entre_2025_e_2026(datasets):
    tabela = compare_datasets(
        datasets["students_2025_06"], datasets["students_researchers_2026_04"]
    )
    significativas = tabela[tabela["p"] < 0.05]
    assert set(significativas.index) == {
        "job_ready",
        "knows_opportunities",
        "financial_impact",
        "participates_lab",
        "welcomed_by_faculty",
    }
    assert (significativas["effect"] > 0).all()
