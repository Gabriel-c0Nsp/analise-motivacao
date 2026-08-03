"""Tabelas de frequência e cruzamentos sobre os nomes canônicos."""

import pandas as pd

from survey.loading import resolve
from survey.schemas import LIKERT_ORDER, RATING_ORDER, SCALES

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
    """Tabela de contagens cruzando duas variáveis."""
    frame = resolve(dataset)
    return pd.crosstab(frame[a], frame[b])


def crosstab_rowperc(dataset, a, b):
    """Tabela de percentuais por linha, cada linha somando 100."""
    table = crosstab_counts(dataset, a, b)
    return (table.div(table.sum(axis=1), axis=0) * 100).round(1)
