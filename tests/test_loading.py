import pandas as pd
import pytest

from survey.loading import LOADED, clean_text, load_all, load_survey, resolve
from survey.schemas import SCHEMAS

TAMANHOS = {
    "students_2025_06": 29,
    "researchers_2025_06": 25,
    "students_researchers_2026_04": 39,
}


@pytest.fixture(scope="module")
def datasets():
    return load_all()


def test_clean_text_remove_espacos_das_pontas():
    assert clean_text("  Sim ") == "Sim"


def test_clean_text_preserva_ausente():
    assert pd.isna(clean_text(float("nan")))


@pytest.mark.parametrize("nome,esperado", TAMANHOS.items())
def test_numero_de_respostas_por_dataset(datasets, nome, esperado):
    assert len(datasets[nome]) == esperado


def test_colunas_canonicas_substituem_o_texto_da_pergunta(datasets):
    frame = datasets["students_2025_06"]
    assert "change_major" in frame.columns
    assert "Considera trocar de curso?" not in frame.columns


def test_likert_vira_numero_e_guarda_o_texto_original(datasets):
    frame = datasets["students_2025_06"]
    assert frame["welcomed_by_faculty"].between(1, 5).all()
    assert frame["welcomed_by_faculty_txt"].str.len().gt(0).all()


def test_binaria_vira_zero_e_um(datasets):
    assert set(datasets["students_2025_06"]["change_major"].unique()) == {0, 1}


def test_categorica_guarda_texto_e_nao_cria_coluna_txt(datasets):
    frame = datasets["students_2025_06"]
    assert frame["age_range"].iloc[0] == "18 - 21 anos"
    assert "age_range_txt" not in frame.columns


def test_term_converte_periodo_para_numero(datasets):
    frame = datasets["students_researchers_2026_04"]
    assert frame["term"].between(1, 11).all()
    assert (frame["term"] == 11).sum() == 6


def test_considered_quitting_bin_derivado_apenas_onde_a_escala_e_likert(datasets):
    novo = datasets["students_researchers_2026_04"]
    antigo = datasets["researchers_2025_06"]
    assert "considered_quitting_bin" in novo.columns
    assert "considered_quitting_bin" not in antigo.columns
    assert novo["considered_quitting_bin"].sum() == 16


def test_attrs_guardam_a_identificacao_do_dataset(datasets):
    frame = datasets["students_researchers_2026_04"]
    assert frame.attrs["dataset"] == "students_researchers_2026_04"
    assert (frame.attrs["year"], frame.attrs["month"]) == (2026, 4)
    assert frame.attrs["kinds"]["term"] == "term"


def test_nenhuma_conversao_ficou_sem_mapeamento(datasets):
    for nome, frame in datasets.items():
        assert frame.attrs["conversion_report"] == [], nome


def test_pergunta_ausente_no_csv_falha_com_mensagem_clara():
    schema = dict(SCHEMAS["students_2025_06"])
    schema["columns"] = dict(schema["columns"])
    schema["columns"]["inexistente"] = ("Pergunta que nao existe no arquivo", "likert")
    with pytest.raises(KeyError, match="Pergunta que nao existe no arquivo"):
        load_survey(schema)


def test_resolve_aceita_nome_ou_dataframe(datasets):
    assert resolve("students_2025_06") is LOADED["students_2025_06"]
    frame = datasets["students_2025_06"]
    assert resolve(frame) is frame


def test_resolve_recusa_nome_desconhecido(datasets):
    with pytest.raises(KeyError, match="students_2025_06"):
        resolve("dataset_que_nao_existe")
