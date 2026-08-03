"""Escalas de conversao e esquemas dos formularios da pesquisa."""

LIKERT_5 = {
    "Discordo totalmente": 1,
    "Discordo parcialmente": 2,
    "Nem concordo nem discordo": 3,
    "Neutro": 3,
    "Concordo parcialmente": 4,
    "Concordo totalmente": 5,
}

LIKERT_ORDER = [
    "Discordo totalmente",
    "Discordo parcialmente",
    "Nem concordo nem discordo",
    "Neutro",
    "Concordo parcialmente",
    "Concordo totalmente",
]

BINARY = {"Não": 0, "Sim": 1}

RATING_5 = {
    "Muito ruim": 1,
    "Ruim": 2,
    "Neutro": 3,
    "Boa": 4,
    "Muito boa": 5,
}

RATING_ORDER = ["Muito ruim", "Ruim", "Neutro", "Boa", "Muito boa"]

# "Adequada" e "Boa" medem coisas diferentes (adequacao e qualidade). A ordem
# adotada esta registrada nas limitacoes da pesquisa.
WORKLOAD_4 = {
    "Inadequada": 1,
    "Adequada": 2,
    "Boa": 3,
    "Muito boa": 4,
}

TERM_11 = {
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

SCALES = {
    "likert": LIKERT_5,
    "binary": BINARY,
    "rating": RATING_5,
    "workload": WORKLOAD_4,
    "term": TERM_11,
}

# Resposta Likert a partir da qual "ja pensei em desistir" equivale ao "Sim"
# da versao binaria de 2025.
QUITTING_AGREEMENT_THRESHOLD = 4
