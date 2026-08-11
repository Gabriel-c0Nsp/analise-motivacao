import pandas as pd
import pytest

from survey.schemas import (
    BINARY,
    BLOCKS,
    CAVEATS,
    LIKERT_5,
    LIKERT_ORDER,
    RATING_5,
    RATING_ORDER,
    SCALES,
    SCHEMAS,
    TERM_11,
    WORKLOAD_4,
)


def test_likert_mapeia_os_dois_rotulos_neutros_para_3():
    assert LIKERT_5["Nem concordo nem discordo"] == 3
    assert LIKERT_5["Neutro"] == 3


def test_likert_vai_de_1_a_5():
    assert min(LIKERT_5.values()) == 1
    assert max(LIKERT_5.values()) == 5


def test_likert_order_cobre_todos_os_rotulos_do_mapa():
    assert set(LIKERT_ORDER) == set(LIKERT_5)


def test_binary_usa_nao_zero_e_sim_um():
    assert BINARY == {"Não": 0, "Sim": 1}


def test_rating_vai_de_muito_ruim_a_muito_boa():
    assert RATING_5["Muito ruim"] == 1
    assert RATING_5["Muito boa"] == 5


def test_workload_trata_inadequada_como_o_pior_valor():
    assert WORKLOAD_4["Inadequada"] == 1
    assert WORKLOAD_4["Muito boa"] == max(WORKLOAD_4.values())


def test_term_cobre_do_primeiro_ao_decimo_periodo():
    assert [TERM_11["%dº" % n] for n in range(1, 11)] == list(range(1, 11))


def test_term_coloca_quem_conclui_pendencias_acima_do_decimo():
    rotulo = "Concluindo cadeiras pendentes ou TCC (acima do intervalo de 10 períodos)"
    assert TERM_11[rotulo] == 11


def test_scales_expoe_as_cinco_escalas_numericas():
    assert set(SCALES) == {"likert", "binary", "rating", "workload", "term"}


def test_likert_5_tem_valores_exatos():
    assert LIKERT_5 == {
        "Discordo totalmente": 1,
        "Discordo parcialmente": 2,
        "Nem concordo nem discordo": 3,
        "Neutro": 3,
        "Concordo parcialmente": 4,
        "Concordo totalmente": 5,
    }


def test_rating_5_tem_valores_exatos():
    assert RATING_5 == {
        "Muito ruim": 1,
        "Ruim": 2,
        "Neutro": 3,
        "Boa": 4,
        "Muito boa": 5,
    }


def test_workload_4_tem_valores_exatos():
    assert WORKLOAD_4 == {
        "Inadequada": 1,
        "Adequada": 2,
        "Boa": 3,
        "Muito boa": 4,
    }


def test_term_11_tem_valores_exatos():
    assert TERM_11 == {
        "1º": 1,
        "2º": 2,
        "3º": 3,
        "4º": 4,
        "5º": 5,
        "6º": 6,
        "7º": 7,
        "8º": 8,
        "9º": 9,
        "10º": 10,
        "Concluindo cadeiras pendentes ou TCC (acima do intervalo de 10 períodos)": 11,
    }


def test_rating_order_cobre_todos_os_rotulos_do_mapa():
    assert set(RATING_ORDER) == set(RATING_5)


def test_rating_order_esta_em_ordem_crescente():
    assert RATING_ORDER == ["Muito ruim", "Ruim", "Neutro", "Boa", "Muito boa"]


def test_scales_aponta_para_os_dicionarios_corretos():
    assert SCALES["likert"] is LIKERT_5
    assert SCALES["binary"] is BINARY
    assert SCALES["rating"] is RATING_5
    assert SCALES["workload"] is WORKLOAD_4
    assert SCALES["term"] is TERM_11


NOMES = ["students_2025_06", "researchers_2025_06", "students_researchers_2026_04"]


@pytest.mark.parametrize("nome", NOMES)
def test_toda_pergunta_declarada_existe_no_csv(nome):
    schema = SCHEMAS[nome]
    colunas = pd.read_csv(schema["file"], nrows=0).columns.str.strip()
    faltando = [q for q, _, _ in schema["columns"].values() if q not in colunas]
    assert faltando == []


@pytest.mark.parametrize("nome", NOMES)
def test_todo_tipo_declarado_e_conhecido(nome):
    tipos = {tipo for _, tipo, _ in SCHEMAS[nome]["columns"].values()}
    assert tipos <= {"likert", "binary", "rating", "workload", "term", "categorical"}


@pytest.mark.parametrize("nome", NOMES)
def test_todo_bloco_declarado_e_conhecido(nome):
    blocos = {bloco for _, _, bloco in SCHEMAS[nome]["columns"].values()}
    assert blocos <= set(BLOCKS)


def test_apenas_o_bloco_de_atividade_tem_recorte():
    assert BLOCKS["general"]["scope"] is None
    assert BLOCKS["activity"]["scope"] == "participates_lab"


def test_alunos_2025_nao_tem_bloco_de_atividade():
    blocos = {bloco for _, _, bloco in SCHEMAS["students_2025_06"]["columns"].values()}
    assert blocos == {"general"}


def test_bolsistas_2025_traz_o_bloco_de_atividade_menos_a_faixa_etaria():
    colunas = SCHEMAS["researchers_2025_06"]["columns"]
    gerais = {nome for nome, (_, _, bloco) in colunas.items() if bloco == "general"}
    assert gerais == {"age_range"}


def test_pesquisa_2026_declara_o_bloco_de_atividade():
    colunas = SCHEMAS["students_researchers_2026_04"]["columns"]
    atividade = {nome for nome, (_, _, bloco) in colunas.items() if bloco == "activity"}
    assert atividade == {
        "activity_type",
        "activity_role",
        "career_contribution",
        "good_supervision",
        "lacks_time",
        "recognition_motivates",
        "academic_output",
        "considered_quitting",
    }


def test_lab_helps_fica_no_bloco_geral_por_ser_respondida_por_todos():
    for nome in ["students_2025_06", "students_researchers_2026_04"]:
        assert SCHEMAS[nome]["columns"]["lab_helps"][2] == "general"


def test_so_a_pesquisa_de_2026_precisa_recortar_o_bloco_de_atividade():
    # Em 2025 o formulário de bolsistas já era respondido só por participantes,
    # então o bloco cobre a amostra inteira e não há o que recortar.
    assert SCHEMAS["students_researchers_2026_04"]["activity_scope"] == "participates_lab"
    assert SCHEMAS["researchers_2025_06"]["activity_scope"] is None
    assert SCHEMAS["students_2025_06"]["activity_scope"] is None


def test_recorte_declarado_aponta_para_uma_binaria_do_bloco_geral():
    for nome, schema in SCHEMAS.items():
        alvo = schema["activity_scope"]
        if alvo is None:
            continue
        pergunta, tipo, bloco = schema["columns"][alvo]
        assert (tipo, bloco) == ("binary", "general"), nome


@pytest.mark.parametrize(
    "nome,esperado",
    [("students_2025_06", 19), ("researchers_2025_06", 16), ("students_researchers_2026_04", 27)],
)
def test_quantidade_de_variaveis_declaradas(nome, esperado):
    assert len(SCHEMAS[nome]["columns"]) == esperado


def test_identificacao_por_ano_e_mes_bate_com_o_primeiro_respondente():
    for nome, schema in SCHEMAS.items():
        bruto = pd.read_csv(schema["file"])["Timestamp"].str.replace(" GMT-3", "", regex=False)
        primeiro = pd.to_datetime(bruto, format="%Y/%m/%d %I:%M:%S %p").min()
        assert (primeiro.year, primeiro.month) == (schema["year"], schema["month"]), nome
        assert nome.endswith("%d_%02d" % (schema["year"], schema["month"]))


def test_considered_quitting_muda_de_escala_entre_os_formularios():
    assert SCHEMAS["researchers_2025_06"]["columns"]["considered_quitting"][1] == "binary"
    assert SCHEMAS["students_researchers_2026_04"]["columns"]["considered_quitting"][1] == "likert"


def test_toda_coluna_declara_pergunta_tipo_e_bloco():
    for nome, schema in SCHEMAS.items():
        for coluna, declaracao in schema["columns"].items():
            assert len(declaracao) == 3, "%s.%s" % (nome, coluna)


def test_lab_helps_e_lab_helped_nao_compartilham_nome_canonico():
    assert "lab_helped" in SCHEMAS["researchers_2025_06"]["columns"]
    assert "lab_helps" not in SCHEMAS["researchers_2025_06"]["columns"]
    assert "lab_helps" in SCHEMAS["students_2025_06"]["columns"]
    assert "lab_helps" in SCHEMAS["students_researchers_2026_04"]["columns"]


def test_ressalvas_apontam_para_variaveis_existentes():
    declaradas = set()
    for schema in SCHEMAS.values():
        declaradas |= set(schema["columns"])
    assert set(CAVEATS) <= declaradas
