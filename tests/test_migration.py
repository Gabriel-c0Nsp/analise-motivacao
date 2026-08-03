"""Confere que a carga canônica reproduz os números do notebook anterior."""

import pandas as pd
import pytest

from survey.descriptive import crosstab_counts, crosstab_rowperc
from survey.loading import load_all

LIKERT_ANTIGO = {
    "Discordo totalmente": 1,
    "Discordo parcialmente": 2,
    "Nem concordo nem discordo": 3,
    "Neutro": 3,
    "Concordo parcialmente": 4,
    "Concordo totalmente": 5,
}

SIM_NAO_ANTIGO = {"Não": 0, "Sim": 1}

# Cruzamentos do notebook anterior: nome canônico de cada eixo e o texto exato
# da pergunta no CSV de origem.
CRUZAMENTOS = [
    ("participates_lab", "Participa de algum laboratório ou projeto de pesquisa da universidade?", "bin",
     "lab_helps", "A participação em laboratórios ou projetos de pesquisa ajuda (ou ajudaria) a compreender melhor os conteúdos das disciplinas.", "likert"),
    ("change_major", "Considera trocar de curso?", "bin",
     "financial_impact", "As dificuldades financeiras afetam minha vida acadêmica.", "likert"),
    ("financial_hardship", "Atualmente enfrento dificuldades financeiras.", "likert",
     "dropped_courses", "Já trancou cadeiras por não acompanhar o conteúdo?", "bin"),
    ("change_major", "Considera trocar de curso?", "bin",
     "welcomed_by_faculty", "Me sinto acolhido(a) por professores e monitores quando tenho dúvidas.", "likert"),
    ("has_scholarship", "Recebe alguma bolsa/auxilio da faculdade?", "bin",
     "change_major", "Considera trocar de curso?", "bin"),
    ("welcomed_by_faculty", "Me sinto acolhido(a) por professores e monitores quando tenho dúvidas.", "likert",
     "welcoming_environment", "Considero o meio acadêmico do qual faço parte acolhedor.", "likert"),
    ("works", "Trabalha no contraturno das aulas?", "bin",
     "keeps_up", "Consigo acompanhar a maioria dos conteúdos ministrados em sala de aula atualmente.", "likert"),
    ("works", "Trabalha no contraturno das aulas?", "bin",
     "change_major", "Considera trocar de curso?", "bin"),
    ("works", "Trabalha no contraturno das aulas?", "bin",
     "dropped_courses", "Já trancou cadeiras por não acompanhar o conteúdo?", "bin"),
    ("participates_lab", "Participa de algum laboratório ou projeto de pesquisa da universidade?", "bin",
     "change_major", "Considera trocar de curso?", "bin"),
    ("knows_opportunities", "Você conhece as oportunidades de iniciação científica, monitoria ou laboratórios oferecidas pela universidade?", "bin",
     "participates_lab", "Participa de algum laboratório ou projeto de pesquisa da universidade?", "bin"),
    ("meets_requirements", "Você atende aos requisitos necessários para participar de projetos de iniciação científica (CR acima de 7.0 e disciplinas pagas em caso de reprovação)?", "bin",
     "participates_lab", "Participa de algum laboratório ou projeto de pesquisa da universidade?", "bin"),
    ("school_base", "Recebi uma boa base de aprendizado durante os anos escolares.", "likert",
     "keeps_up", "Consigo acompanhar a maioria dos conteúdos ministrados em sala de aula atualmente.", "likert"),
]

CRUZAMENTOS_BOLSISTAS = [
    ("considered_quitting", "Já pensou em desistir da atividade de laboratório ou extensão por excesso de demandas acadêmicas?", "bin",
     "lacks_time", "Sinto que não tenho tempo suficiente para conciliar as disciplinas regulares, a atividade no laboratório/projeto e minha vida pessoal.", "likert"),
    ("recommended_to_peers", "Você já recomendou a colegas a participação no laboratório ou projeto?", "bin",
     "good_supervision", "Recebo orientação adequada do meu professor orientador.", "likert"),
    ("recommended_to_peers", "Você já recomendou a colegas a participação no laboratório ou projeto?", "bin",
     "recognition_motivates", "O reconhecimento (formal ou informal) pelo meu trabalho no laboratório/projeto contribuiu para minha motivação no curso.", "likert"),
    ("activity_role", "Qual a sua participação em relação às atividades citadas acima?", "cat",
     "considered_quitting", "Já pensou em desistir da atividade de laboratório ou extensão por excesso de demandas acadêmicas?", "bin"),
    ("good_supervision", "Recebo orientação adequada do meu professor orientador.", "likert",
     "considered_quitting", "Já pensou em desistir da atividade de laboratório ou extensão por excesso de demandas acadêmicas?", "bin"),
    ("stipend_enough", "A bolsa que recebo é suficiente para cobrir minhas principais despesas acadêmicas.", "likert",
     "considered_quitting", "Já pensou em desistir da atividade de laboratório ou extensão por excesso de demandas acadêmicas?", "bin"),
]


def _antigo(arquivo, pergunta, tipo):
    """Reproduz a conversão do notebook anterior a partir do CSV bruto."""
    frame = pd.read_csv(arquivo)
    frame.columns = frame.columns.str.strip()
    texto = frame[pergunta].map(lambda x: x if pd.isna(x) else str(x).strip())
    if tipo == "cat":
        return texto
    return texto.map(LIKERT_ANTIGO if tipo == "likert" else SIM_NAO_ANTIGO)


@pytest.fixture(scope="module")
def datasets():
    return load_all(verbose=False)


@pytest.mark.parametrize("caso", CRUZAMENTOS)
def test_cruzamentos_de_alunos_batem_com_o_notebook_anterior(datasets, caso):
    nome_a, pergunta_a, tipo_a, nome_b, pergunta_b, tipo_b = caso
    arquivo = "dados/alunos_geral.csv"
    esperado = pd.crosstab(
        _antigo(arquivo, pergunta_a, tipo_a),
        _antigo(arquivo, pergunta_b, tipo_b),
    )
    obtido = crosstab_counts("students_2025_06", nome_a, nome_b)
    assert obtido.values.tolist() == esperado.values.tolist()


@pytest.mark.parametrize("caso", CRUZAMENTOS_BOLSISTAS)
def test_cruzamentos_de_bolsistas_batem_com_o_notebook_anterior(datasets, caso):
    nome_a, pergunta_a, tipo_a, nome_b, pergunta_b, tipo_b = caso
    arquivo = "dados/bolsistas.csv"
    esperado = pd.crosstab(
        _antigo(arquivo, pergunta_a, tipo_a),
        _antigo(arquivo, pergunta_b, tipo_b),
    )
    obtido = crosstab_counts("researchers_2025_06", nome_a, nome_b)
    assert obtido.values.tolist() == esperado.values.tolist()


def test_percentual_por_linha_bate_com_o_notebook_anterior(datasets):
    arquivo = "dados/alunos_geral.csv"
    esperado = pd.crosstab(
        _antigo(arquivo, "Participa de algum laboratório ou projeto de pesquisa da universidade?", "bin"),
        _antigo(arquivo, "A participação em laboratórios ou projetos de pesquisa ajuda (ou ajudaria) a compreender melhor os conteúdos das disciplinas.", "likert"),
    )
    esperado = (esperado.div(esperado.sum(axis=1), axis=0) * 100).round(1)
    obtido = crosstab_rowperc("students_2025_06", "participates_lab", "lab_helps")
    assert obtido.values.tolist() == esperado.values.tolist()
