import pandas as pd
import pytest

from survey.descriptive import (
    common_vars,
    compare_freq,
    compare_items,
    crosstab_counts,
    crosstab_rowperc,
    freq_table,
)
from survey.loading import load_all


@pytest.fixture(scope="module")
def datasets():
    return load_all(verbose=False)


def test_freq_table_soma_cem_por_cento(datasets):
    tabela = freq_table("students_2025_06", "change_major")
    assert round(tabela["percent"].sum()) == 100


def test_freq_table_conta_todas_as_respostas(datasets):
    tabela = freq_table("students_2025_06", "change_major")
    assert tabela["count"].sum() == 29


def test_freq_table_reproduz_o_balanceamento_conhecido(datasets):
    tabela = freq_table("students_2025_06", "change_major")
    assert tabela.loc["Não", "count"] == 18
    assert tabela.loc["Sim", "count"] == 11


def test_freq_table_ordena_likert_pela_escala_e_nao_pela_frequencia(datasets):
    tabela = freq_table("students_researchers_2026_04", "burnout")
    assert list(tabela.index) == [
        "Discordo totalmente",
        "Nem concordo nem discordo",
        "Concordo parcialmente",
        "Concordo totalmente",
    ]


def test_freq_table_sem_rotulos_devolve_o_indice_numerico(datasets):
    tabela = freq_table("students_2025_06", "welcomed_by_faculty", labels=False)
    assert list(tabela.index) == [2, 3, 4, 5]


def test_freq_table_categorica_ordena_por_frequencia(datasets):
    tabela = freq_table("students_2025_06", "age_range")
    assert list(tabela.index) == [
        "18 - 21 anos",
        "22 - 25 anos",
        "Menos de 18 anos",
        "Mais de 30 anos",
    ]
    assert round(tabela["percent"].sum()) == 100


def test_crosstab_counts_preserva_o_total(datasets):
    tabela = crosstab_counts("students_2025_06", "participates_lab", "lab_helps")
    assert tabela.values.sum() == 29


def test_crosstab_rowperc_cada_linha_soma_cem(datasets):
    tabela = crosstab_rowperc("students_2025_06", "participates_lab", "lab_helps")
    assert tabela.sum(axis=1).round().eq(100).all()


def test_crosstab_counts_descarta_linha_com_ausente_em_qualquer_variavel():
    frame = pd.DataFrame({
        "a": [1, 2, None, 1, 2],
        "b": [1, None, 2, 1, 2],
    })
    tabela = crosstab_counts(frame, "a", "b")
    assert tabela.values.sum() == 3


def test_funcoes_aceitam_dataframe_alem_do_nome(datasets):
    frame = datasets["students_2025_06"]
    assert freq_table(frame, "change_major").equals(freq_table("students_2025_06", "change_major"))


def test_pacote_survey_reexporta_as_funcoes_publicas():
    import survey

    assert survey.freq_table is freq_table
    assert survey.crosstab_counts is crosstab_counts
    assert survey.crosstab_rowperc is crosstab_rowperc


COMUNS_ENTRE_ESTUDANTES = [
    "age_range",
    "change_major",
    "curriculum_rating",
    "dropped_courses",
    "facilities_rating",
    "financial_impact",
    "job_ready",
    "keeps_up",
    "knows_opportunities",
    "lab_helps",
    "meets_requirements",
    "participates_lab",
    "welcomed_by_faculty",
    "welcoming_environment",
    "works",
]


def test_common_vars_entre_os_dois_formularios_de_estudantes():
    assert common_vars("students_2025_06", "students_researchers_2026_04") == COMUNS_ENTRE_ESTUDANTES


def test_common_vars_nao_inclui_lab_helped_que_so_existe_em_2025():
    assert "lab_helped" not in common_vars("researchers_2025_06", "students_researchers_2026_04")


def test_compare_freq_devolve_uma_coluna_por_dataset(datasets):
    tabela = compare_freq(["students_2025_06", "students_researchers_2026_04"], "change_major")
    assert list(tabela.columns) == ["Alunos 2025", "Pesquisa 2026"]


def test_compare_freq_cada_coluna_soma_cem(datasets):
    tabela = compare_freq(["students_2025_06", "students_researchers_2026_04"], "change_major")
    assert tabela.sum().round().eq(100).all()


def test_compare_freq_imprime_a_ressalva_da_variavel(datasets, capsys):
    compare_freq(["students_2025_06", "students_researchers_2026_04"], "participates_lab")
    assert "Escopo mudou em 2026" in capsys.readouterr().out


def test_compare_freq_recusa_variavel_ausente_em_um_dos_datasets(datasets):
    with pytest.raises(KeyError, match="common_vars"):
        compare_freq(["students_2025_06", "students_researchers_2026_04"], "burnout")


def test_compare_freq_recusa_considered_quitting_por_mudanca_de_escala(datasets):
    with pytest.raises(KeyError, match="considered_quitting_bin"):
        compare_freq(["researchers_2025_06", "students_researchers_2026_04"], "considered_quitting")


def test_compare_freq_considered_quitting_bin_compara_desistencia_entre_2025_e_2026(datasets):
    tabela = compare_freq(
        ["researchers_2025_06", "students_researchers_2026_04"], "considered_quitting_bin"
    )
    assert list(tabela.index) == ["Não", "Sim"]
    assert tabela.loc["Não", "Bolsistas 2025"] == 52.0
    assert tabela.loc["Sim", "Bolsistas 2025"] == 48.0
    assert tabela.loc["Não", "Pesquisa 2026"] == 59.0
    assert tabela.loc["Sim", "Pesquisa 2026"] == 41.0


PONTE = [("students_2025_06", "lab_helps"), ("researchers_2025_06", "lab_helped")]


def test_compare_items_nomeia_a_coluna_com_dataset_e_item(datasets):
    tabela = compare_items(PONTE)
    assert list(tabela.columns) == ["Alunos 2025 (lab_helps)", "Bolsistas 2025 (lab_helped)"]


def test_compare_items_cada_coluna_soma_cem(datasets):
    assert compare_items(PONTE).sum().round().eq(100).all()


def test_compare_items_reproduz_as_distribuicoes_conhecidas(datasets):
    tabela = compare_items(PONTE)
    alunos = tabela["Alunos 2025 (lab_helps)"]
    bolsistas = tabela["Bolsistas 2025 (lab_helped)"]
    assert alunos["Concordo totalmente"] == 44.8
    assert alunos["Concordo parcialmente"] == 41.4
    assert alunos["Discordo totalmente"] == 3.4
    assert bolsistas["Concordo totalmente"] == 44.0
    assert bolsistas["Concordo parcialmente"] == 36.0
    assert bolsistas["Discordo totalmente"] == 0.0


def test_compare_items_declara_o_texto_de_cada_pergunta(datasets, capsys):
    compare_items(PONTE)
    saida = capsys.readouterr().out
    assert "ajuda (ou ajudaria)" in saida
    assert "ajudou" in saida
    assert "Alunos 2025" in saida
    assert "Bolsistas 2025" in saida


def test_compare_items_imprime_a_ressalva_do_item(datasets, capsys):
    compare_items(PONTE)
    assert "expectativa" in capsys.readouterr().out


def test_compare_items_recusa_item_ausente_no_dataset(datasets):
    with pytest.raises(KeyError, match="lab_helped"):
        compare_items([("students_2025_06", "lab_helped")])


def test_compare_items_recusa_tipos_divergentes(datasets):
    par = [
        ("researchers_2025_06", "considered_quitting"),
        ("students_researchers_2026_04", "considered_quitting"),
    ]
    with pytest.raises(KeyError, match="tipo"):
        compare_items(par)


def test_compare_freq_mantem_a_ordem_da_escala_mesmo_com_rotulos_diferentes(datasets):
    tabela = compare_freq(["students_2025_06", "students_researchers_2026_04"], "welcomed_by_faculty")
    assert list(tabela.index) == [
        "Discordo totalmente",
        "Discordo parcialmente",
        "Nem concordo nem discordo",
        "Concordo parcialmente",
        "Concordo totalmente",
    ]


def test_compare_items_mantem_a_ordem_da_escala(datasets):
    tabela = compare_items(PONTE)
    assert list(tabela.index) == [
        "Discordo totalmente",
        "Discordo parcialmente",
        "Nem concordo nem discordo",
        "Concordo parcialmente",
        "Concordo totalmente",
    ]


def test_compare_freq_categorica_ordena_por_contagem_total_decrescente(datasets):
    tabela = compare_freq(["students_2025_06", "researchers_2025_06"], "age_range")
    assert list(tabela.index) == [
        "18 - 21 anos",
        "22 - 25 anos",
        "Menos de 18 anos",
        "Mais de 30 anos",
        "26 - 30 anos",
    ]


def test_compare_freq_sem_rotulos_mantem_indice_numerico_crescente(datasets):
    tabela = compare_freq(
        ["students_2025_06", "students_researchers_2026_04"], "welcomed_by_faculty", labels=False
    )
    assert list(tabela.index) == [1, 2, 3, 4, 5]
