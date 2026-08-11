import pandas as pd
import pytest

from survey.descriptive import freq_table
from survey.loading import (
    LOADED,
    _print_report,
    activity_frame,
    clean_text,
    load_all,
    load_survey,
    register_derived,
    resolve,
)
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


def test_considered_quitting_bin_existe_nos_dois_datasets_como_binaria(datasets):
    novo = datasets["students_researchers_2026_04"]
    antigo = datasets["researchers_2025_06"]
    assert "considered_quitting_bin" in novo.columns
    assert "considered_quitting_bin" in antigo.columns
    assert novo.attrs["kinds"]["considered_quitting_bin"] == "binary"
    assert antigo.attrs["kinds"]["considered_quitting_bin"] == "binary"
    assert novo["considered_quitting_bin"].sum() == 16
    assert freq_table(antigo, "considered_quitting_bin")["count"].sum() == len(antigo)


def test_attrs_guardam_a_identificacao_do_dataset(datasets):
    frame = datasets["students_researchers_2026_04"]
    assert frame.attrs["dataset"] == "students_researchers_2026_04"
    assert (frame.attrs["year"], frame.attrs["month"]) == (2026, 4)
    assert frame.attrs["kinds"]["term"] == "term"


def test_nenhuma_conversao_ficou_sem_mapeamento(datasets):
    for nome, frame in datasets.items():
        assert frame.attrs["conversion_report"] == [], nome


def test_conversion_report_registra_valor_fora_da_escala(tmp_path):
    question = SCHEMAS["students_2025_06"]["columns"]["school_base"][0]
    path = tmp_path / "sintetico.csv"
    pd.DataFrame({question: ["Concordo totalmente", "Talvez"]}).to_csv(path, index=False)

    schema = dict(SCHEMAS["students_2025_06"])
    schema["file"] = str(path)
    schema["columns"] = {"school_base": (question, "likert", "general")}

    frame = load_survey(schema)

    assert frame.attrs["conversion_report"] == [("school_base", ["Talvez"])]


def test_print_report_mostra_o_valor_que_nao_bateu(tmp_path, capsys):
    question = SCHEMAS["students_2025_06"]["columns"]["school_base"][0]
    path = tmp_path / "sintetico.csv"
    pd.DataFrame({question: ["Concordo totalmente", "Talvez"]}).to_csv(path, index=False)

    schema = dict(SCHEMAS["students_2025_06"])
    schema["file"] = str(path)
    schema["columns"] = {"school_base": (question, "likert", "general")}

    frame = load_survey(schema)
    _print_report("sintetico", frame)

    saida = capsys.readouterr().out
    assert "Talvez" in saida


def test_considered_quitting_bin_preserva_ausente_em_vez_de_zero(tmp_path):
    question = SCHEMAS["students_researchers_2026_04"]["columns"]["considered_quitting"][0]
    path = tmp_path / "sintetico.csv"
    pd.DataFrame(
        {question: ["Concordo totalmente", "Discordo totalmente", None]}
    ).to_csv(path, index=False)

    schema = dict(SCHEMAS["students_researchers_2026_04"])
    schema["file"] = str(path)
    schema["columns"] = {"considered_quitting": (question, "likert", "activity")}

    frame = load_survey(schema)

    assert frame["considered_quitting_bin"].iloc[0] == 1.0
    assert frame["considered_quitting_bin"].iloc[1] == 0.0
    assert pd.isna(frame["considered_quitting_bin"].iloc[2])


def test_pergunta_ausente_no_csv_falha_com_mensagem_clara():
    schema = dict(SCHEMAS["students_2025_06"])
    schema["columns"] = dict(schema["columns"])
    schema["columns"]["inexistente"] = ("Pergunta que nao existe no arquivo", "likert", "general")
    with pytest.raises(KeyError, match="Pergunta que nao existe no arquivo"):
        load_survey(schema)


def test_blocos_ficam_nos_attrs_de_cada_dataset(datasets):
    blocos = datasets["students_researchers_2026_04"].attrs["blocks"]
    assert blocos["welcomed_by_faculty"] == "general"
    assert blocos["good_supervision"] == "activity"
    assert set(datasets["students_2025_06"].attrs["blocks"].values()) == {"general"}


def test_coluna_derivada_na_carga_herda_o_bloco_do_item_de_origem(datasets):
    novo = datasets["students_researchers_2026_04"]
    assert novo.attrs["blocks"]["considered_quitting_bin"] == "activity"
    assert novo.attrs["derived"] == ["considered_quitting_bin"]


def test_register_derived_torna_a_coluna_visivel_para_freq_table(datasets):
    frame = datasets["students_2025_06"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    frame.attrs["derived"] = []

    register_derived(frame, "works_num", frame["works"].astype(float), "binary")

    assert frame.attrs["kinds"]["works_num"] == "binary"
    assert frame.attrs["blocks"]["works_num"] == "general"
    assert frame.attrs["derived"] == ["works_num"]
    assert freq_table(frame, "works_num")["count"].sum() == len(frame)


def test_register_derived_recusa_bloco_desconhecido(datasets):
    frame = datasets["students_2025_06"].copy()
    frame.attrs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in frame.attrs.items()}
    with pytest.raises(KeyError, match="inventado"):
        register_derived(frame, "qualquer", frame["works"], "binary", block="inventado")


def test_activity_frame_recorta_2026_para_quem_participa(datasets):
    frame = datasets["students_researchers_2026_04"]
    recorte = activity_frame(frame)
    assert len(frame) == 39
    assert len(recorte) == 25
    assert (recorte["participates_lab"] == 1).all()


def test_activity_frame_renomeia_o_rotulo_do_recorte(datasets):
    recorte = activity_frame(datasets["students_researchers_2026_04"])
    assert recorte.attrs["label"] == "Pesquisa 2026 (participantes)"


def test_activity_frame_devolve_intacto_quem_ja_era_so_participante(datasets):
    frame = datasets["researchers_2025_06"]
    assert activity_frame(frame) is frame
    assert activity_frame("students_2025_06") is datasets["students_2025_06"]


def test_activity_frame_nao_altera_os_metadados_do_quadro_original(datasets):
    frame = datasets["students_researchers_2026_04"]
    recorte = activity_frame(frame)
    register_derived(recorte, "so_no_recorte", recorte["works"].astype(float), "binary")
    assert "so_no_recorte" not in frame.attrs["kinds"]
    assert "so_no_recorte" not in frame.attrs["blocks"]
    assert frame.attrs["label"] == "Pesquisa 2026"


def test_recorte_muda_o_percentual_de_quem_pensou_em_desistir(datasets):
    frame = datasets["students_researchers_2026_04"]
    inteiro = frame["considered_quitting_bin"].mean()
    recortado = activity_frame(frame)["considered_quitting_bin"].mean()
    assert round(inteiro * 100, 1) == 41.0
    assert round(recortado * 100, 1) == 52.0


def test_resolve_aceita_nome_ou_dataframe(datasets):
    assert resolve("students_2025_06") is LOADED["students_2025_06"]
    frame = datasets["students_2025_06"]
    assert resolve(frame) is frame


def test_resolve_recusa_nome_desconhecido(datasets):
    with pytest.raises(KeyError, match="students_2025_06"):
        resolve("dataset_que_nao_existe")
