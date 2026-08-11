"""Tabelas de frequência e cruzamentos sobre os nomes canônicos."""

import pandas as pd

from survey.loading import resolve
from survey.schemas import CAVEATS, LIKERT_ORDER, RATING_ORDER, SCALES, SCHEMAS

ORDERS = {"likert": LIKERT_ORDER, "rating": RATING_ORDER}


def _labels_for(kind):
    """Devolve o mapa de número para rótulo da escala, na ordem de exibição."""
    scale = SCALES[kind]
    order = ORDERS.get(kind, sorted(scale, key=scale.get))
    pairs = {}
    for label in order:
        pairs.setdefault(scale[label], label)
    return pairs


def freq_table(dataset, name, labels=True):
    """Contagem e percentual de uma variável, na ordem natural da escala."""
    frame = resolve(dataset)
    kind = frame.attrs["kinds"][name]
    series = frame[name]

    if kind == "categorical":
        counts = series.value_counts(dropna=False)
    else:
        counts = series.value_counts(dropna=False).sort_index()
        if labels:
            counts.index = counts.index.map(_labels_for(kind))

    percent = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"count": counts, "percent": percent})


def crosstab_counts(dataset, a, b):
    """Tabela de contagens cruzando duas variáveis.

    Linhas com valor ausente em `a` ou em `b` ficam de fora, então o total
    da tabela pode ser menor que o número de respostas do dataset.
    """
    frame = resolve(dataset)
    return pd.crosstab(frame[a], frame[b])


def crosstab_rowperc(dataset, a, b):
    """Tabela de percentuais por linha, cada linha somando 100.

    Herda de `crosstab_counts` o descarte de linhas com valor ausente em
    `a` ou em `b`.
    """
    table = crosstab_counts(dataset, a, b)
    return (table.div(table.sum(axis=1), axis=0) * 100).round(1)


def common_vars(*names):
    """Variáveis declaradas em todos os datasets informados."""
    declared = [set(SCHEMAS[name]["columns"]) for name in names]
    return sorted(set.intersection(*declared))


def _check_same_kind(items):
    """Recusa quando o tipo declarado diverge entre os itens comparados.

    `items` é uma lista de tuplas `(rotulo_do_dataset, nome_canonico, tipo)`.
    Compartilhada por `compare_freq`, em que o nome é o mesmo em cada item, e
    por `compare_items`, em que ele pode variar.
    """
    if len({kind for _, _, kind in items}) <= 1:
        return
    detail = ", ".join("%s (%s) em %s" % (name, kind, label) for label, name, kind in items)
    if {name for _, name, _ in items} == {"considered_quitting"}:
        hint = (
            "Compare por considered_quitting_bin, restringindo 2026 aos participantes "
            "com frame[frame['participates_lab'] == 1], porque a seção de atividade era "
            "obrigatória e foi respondida também por quem não participa."
        )
    else:
        hint = "Use common_vars() para ver o que dá para comparar."
    raise KeyError("tipo diferente entre os itens comparados: %s. %s" % (detail, hint))


def _ordered_labels(tables, kind, labels):
    """Devolve os rótulos da comparação na ordem certa, ou `None` para deixar o índice como está.

    Sem essa ordenação explícita, `pd.DataFrame` monta a união dos índices das
    tabelas em ordem alfabética sempre que os lados têm rótulos diferentes, o
    que embaralha uma escala Likert. Itens não categóricos com rótulo de texto
    seguem a ordem da escala, lida de `_labels_for`. Itens categóricos não têm
    escala, então a ordem passa a ser por contagem total decrescente somando
    as tabelas comparadas, com empate na ordem em que o rótulo apareceu pela
    primeira vez. Índice numérico (`labels=False` fora de categórica) já sai
    crescente da união do pandas e não precisa de tratamento especial.
    """
    if kind != "categorical" and labels:
        vistos = {rotulo for tabela in tables for rotulo in tabela.index}
        return [rotulo for rotulo in _labels_for(kind).values() if rotulo in vistos]

    if kind != "categorical":
        return None

    totais = {}
    ordem = []
    for tabela in tables:
        for rotulo, contagem in tabela["count"].items():
            if rotulo not in totais:
                ordem.append(rotulo)
                totais[rotulo] = 0
            totais[rotulo] += contagem
    ordem.sort(key=lambda rotulo: totais[rotulo], reverse=True)
    return ordem


def _compare_table(entries, labels):
    """Monta a tabela de percentuais comparando itens, uma coluna por entrada.

    `entries` é uma lista de tuplas `(rotulo_da_coluna, frame, nome_canonico)`,
    todas do mesmo tipo declarado. Reordena o índice pela ordem certa antes de
    devolver, em vez de deixar `pd.DataFrame` decidir a ordem da união.
    """
    tabelas = [freq_table(frame, name, labels=labels) for _, frame, name in entries]
    kind = entries[0][1].attrs["kinds"][entries[0][2]]

    columns = {coluna: tabela["percent"] for (coluna, _, _), tabela in zip(entries, tabelas)}
    tabela_final = pd.DataFrame(columns).fillna(0)

    ordem = _ordered_labels(tabelas, kind, labels)
    if ordem is not None:
        tabela_final = tabela_final.reindex(ordem)
    return tabela_final


def compare_freq(datasets, name, labels=True):
    """Percentual da variável lado a lado, uma coluna por dataset.

    O cabeçalho de cada coluna traz o número de respostas do quadro resumido,
    que é o denominador daquele percentual. Sem ele, uma casa decimal sobre
    amostras destes tamanhos parece mais precisa do que é.
    """
    frames = [resolve(item) for item in datasets]

    absent = [frame.attrs["label"] for frame in frames if name not in frame.columns]
    if absent:
        raise KeyError(
            "%r não existe em: %s. Use common_vars() para ver o que dá para comparar."
            % (name, ", ".join(absent))
        )

    _check_same_kind([(frame.attrs["label"], name, frame.attrs["kinds"][name]) for frame in frames])

    caveat = CAVEATS.get(name)
    if caveat:
        print("Ressalva sobre %s: %s" % (name, caveat))

    entries = [("%s (n=%d)" % (frame.attrs["label"], len(frame)), frame, name) for frame in frames]
    return _compare_table(entries, labels)


def compare_items(pairs, labels=True):
    """Compara itens de perguntas diferentes, declarando o que está sendo comparado.

    Cada item de `pairs` é uma tupla `(dataset, nome_canonico)`. Ao contrário de
    `compare_freq`, os itens não precisam ser a mesma variável: a função existe
    justamente para permitir comparar perguntas distintas entre formulários,
    desde que a comparação seja declarada com o texto completo de cada pergunta,
    lido de `SCHEMAS`, e, quando houver, a ressalva de `CAVEATS` sobre o que
    cada item mede. Como em `compare_freq`, o cabeçalho de cada coluna traz o
    número de respostas que serve de denominador do percentual.
    """
    frames = [resolve(dataset) for dataset, _ in pairs]

    for frame, (_, name) in zip(frames, pairs):
        if name not in frame.columns:
            raise KeyError(
                "%r não existe em %s. Use common_vars() para ver o que dá para comparar."
                % (name, frame.attrs["label"])
            )

    _check_same_kind(
        [(frame.attrs["label"], name, frame.attrs["kinds"][name]) for frame, (_, name) in zip(frames, pairs)]
    )

    print("Comparando itens de perguntas diferentes:")
    for frame, (_, name) in zip(frames, pairs):
        question, _, _ = SCHEMAS[frame.attrs["dataset"]]["columns"][name]
        print("  %s (%s): %s" % (frame.attrs["label"], name, question))

    for _, name in pairs:
        caveat = CAVEATS.get(name)
        if caveat:
            print("Ressalva sobre %s: %s" % (name, caveat))

    entries = [
        ("%s (%s, n=%d)" % (frame.attrs["label"], name, len(frame)), frame, name)
        for frame, (_, name) in zip(frames, pairs)
    ]
    return _compare_table(entries, labels)
