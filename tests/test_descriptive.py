import pytest

from survey.descriptive import crosstab_counts, crosstab_rowperc, freq_table
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


def test_crosstab_counts_preserva_o_total(datasets):
    tabela = crosstab_counts("students_2025_06", "participates_lab", "lab_helps")
    assert tabela.values.sum() == 29


def test_crosstab_rowperc_cada_linha_soma_cem(datasets):
    tabela = crosstab_rowperc("students_2025_06", "participates_lab", "lab_helps")
    assert tabela.sum(axis=1).round().eq(100).all()


def test_funcoes_aceitam_dataframe_alem_do_nome(datasets):
    frame = datasets["students_2025_06"]
    assert freq_table(frame, "change_major").equals(freq_table("students_2025_06", "change_major"))


def test_pacote_survey_reexporta_as_funcoes_publicas():
    import survey

    assert survey.freq_table is freq_table
    assert survey.crosstab_counts is crosstab_counts
    assert survey.crosstab_rowperc is crosstab_rowperc
