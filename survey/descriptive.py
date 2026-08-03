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
        hint = "Use considered_quitting_bin, presente nos dois datasets com o mesmo tipo, para comparar."
    else:
        hint = "Use common_vars() para ver o que dá para comparar."
    raise KeyError("tipo diferente entre os itens comparados: %s. %s" % (detail, hint))


def compare_freq(datasets, name, labels=True):
    """Percentual da variável lado a lado, uma coluna por dataset."""
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

    columns = {
        frame.attrs["label"]: freq_table(frame, name, labels=labels)["percent"] for frame in frames
    }
    return pd.DataFrame(columns).fillna(0)


def compare_items(pairs, labels=True):
    """Compara itens de perguntas diferentes, declarando o que está sendo comparado.

    Cada item de `pairs` é uma tupla `(dataset, nome_canonico)`. Ao contrário de
    `compare_freq`, os itens não precisam ser a mesma variável: a função existe
    justamente para permitir comparar perguntas distintas entre formulários,
    desde que a comparação seja declarada com o texto completo de cada pergunta,
    lido de `SCHEMAS`, e, quando houver, a ressalva de `CAVEATS` sobre o que
    cada item mede.
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
        question, _ = SCHEMAS[frame.attrs["dataset"]]["columns"][name]
        print("  %s (%s): %s" % (frame.attrs["label"], name, question))

    for _, name in pairs:
        caveat = CAVEATS.get(name)
        if caveat:
            print("Ressalva sobre %s: %s" % (name, caveat))

    columns = {
        "%s (%s)" % (frame.attrs["label"], name): freq_table(frame, name, labels=labels)["percent"]
        for frame, (_, name) in zip(frames, pairs)
    }
    return pd.DataFrame(columns).fillna(0)
