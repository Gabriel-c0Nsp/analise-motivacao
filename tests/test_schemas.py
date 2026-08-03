from survey.schemas import (
    BINARY,
    LIKERT_5,
    LIKERT_ORDER,
    RATING_5,
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
