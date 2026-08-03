from survey.schemas import (
    BINARY,
    LIKERT_5,
    LIKERT_ORDER,
    RATING_5,
    RATING_ORDER,
    SCALES,
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
