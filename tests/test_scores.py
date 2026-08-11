import pandas as pd
import pytest

from survey.descriptive import freq_table
from survey.loading import load_all
from survey.scores import REJECTED_SCORES, SCORE_DEFS, build_scores, score_table


@pytest.fixture(scope="module")
def datasets():
    return load_all(verbose=False)


@pytest.fixture
def frame_2026(datasets):
    frame = datasets["students_researchers_2026_04"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    frame.attrs["derived"] = list(datasets["students_researchers_2026_04"].attrs["derived"])
    return frame


def test_todo_score_declara_itens_bloco_rotulo_e_alfa_minimo():
    for nome, definicao in SCORE_DEFS.items():
        assert set(definicao) == {"items", "block", "label", "min_alpha"}, nome
        assert len(definicao["items"]) >= 2, nome


def test_score_usa_o_prefixo_score_e_nunca_escore():
    for nome in SCORE_DEFS:
        assert nome.startswith("score_")
        assert "escore" not in nome


def test_itens_de_um_score_ficam_todos_no_bloco_declarado(datasets):
    blocos = datasets["students_researchers_2026_04"].attrs["blocks"]
    for nome, definicao in SCORE_DEFS.items():
        for item in definicao["items"]:
            if item in blocos:
                assert blocos[item] == definicao["block"], "%s.%s" % (nome, item)


def test_scores_rejeitados_registram_o_motivo_e_o_alfa_medido():
    assert set(REJECTED_SCORES) == {"sobrecarga", "atividade"}
    for nome, motivo in REJECTED_SCORES.items():
        assert "alfa" in motivo, nome


def test_build_scores_cria_os_dois_scores_em_2026(frame_2026):
    relatorio = build_scores(frame_2026)
    assert set(relatorio.index) == {"score_belonging", "score_prospects"}
    assert "score_belonging" in frame_2026.columns
    assert "score_prospects" in frame_2026.columns


def test_build_scores_calcula_a_media_dos_itens(frame_2026):
    build_scores(frame_2026)
    itens = SCORE_DEFS["score_belonging"]["items"]
    esperado = frame_2026[itens].mean(axis=1)
    pd.testing.assert_series_equal(frame_2026["score_belonging"], esperado, check_names=False)


def test_build_scores_registra_os_scores_nos_metadados(frame_2026):
    build_scores(frame_2026)
    assert frame_2026.attrs["kinds"]["score_belonging"] == "score"
    assert frame_2026.attrs["blocks"]["score_belonging"] == "general"
    assert "score_belonging" in frame_2026.attrs["derived"]


def test_relatorio_traz_o_alfa_e_o_n_de_cada_score(frame_2026):
    relatorio = build_scores(frame_2026)
    assert list(relatorio.columns) == ["items", "n", "alpha", "min_alpha", "ok"]
    assert round(relatorio.loc["score_belonging", "alpha"], 4) == 0.7908
    assert round(relatorio.loc["score_prospects", "alpha"], 4) == 0.6608
    assert relatorio.loc["score_belonging", "n"] == 39
    assert relatorio.loc["score_belonging", "items"] == 3


def test_relatorio_marca_quando_o_alfa_fica_abaixo_do_minimo(frame_2026, capsys):
    definicao = dict(SCORE_DEFS["score_prospects"])
    definicao["min_alpha"] = 0.9
    relatorio = build_scores(frame_2026, defs={"score_prospects": definicao})
    assert not relatorio.loc["score_prospects", "ok"]
    assert "score_prospects" in capsys.readouterr().out


def test_build_scores_pula_o_que_falta_item_e_avisa(datasets, capsys):
    frame = datasets["students_2025_06"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    frame.attrs["derived"] = []

    relatorio = build_scores(frame)

    assert relatorio.empty
    assert "score_belonging" not in frame.columns
    saida = capsys.readouterr().out
    assert "teaching_quality" in saida
    assert "career_clarity" in saida


def test_score_com_item_ausente_na_linha_fica_ausente_e_nao_vira_media_parcial():
    frame = pd.DataFrame({"a": [4.0, 5.0], "b": [2.0, None]})
    frame.attrs.update(kinds={"a": "likert", "b": "likert"}, blocks={"a": "general", "b": "general"},
                       derived=[], label="sintetico", activity_scope=None)
    definicao = {"items": ["a", "b"], "block": "general", "label": "Teste", "min_alpha": 0.0}

    build_scores(frame, defs={"score_teste": definicao})

    assert frame["score_teste"].iloc[0] == 3.0
    assert pd.isna(frame["score_teste"].iloc[1])


def test_freq_table_recusa_score_e_aponta_para_score_table(frame_2026):
    build_scores(frame_2026)
    with pytest.raises(KeyError, match="score_table"):
        freq_table(frame_2026, "score_belonging")


def test_score_table_resume_os_scores_construidos(frame_2026):
    build_scores(frame_2026)
    tabela = score_table(frame_2026)
    assert list(tabela.columns) == ["n", "mean", "sd", "min", "max"]
    assert round(tabela.loc["score_belonging", "mean"], 4) == 3.7094
    assert round(tabela.loc["score_belonging", "sd"], 4) == 0.8624
    assert tabela.loc["score_belonging", "n"] == 39


def test_score_table_sem_score_construido_avisa_em_vez_de_devolver_vazio(datasets):
    frame = datasets["students_2025_06"]
    with pytest.raises(KeyError, match="build_scores"):
        score_table(frame)
