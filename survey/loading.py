"""Carga dos CSVs da pesquisa com renomeação para os nomes canônicos."""

import pandas as pd

from survey.schemas import QUITTING_AGREEMENT_THRESHOLD, SCALES, SCHEMAS

LOADED = {}


def clean_text(value):
    """Remove espaços das pontas e converte para str, preservando ausentes."""
    if pd.isna(value):
        return value
    return str(value).strip()


def load_survey(schema):
    """Lê o CSV do esquema e devolve o DataFrame com os nomes canônicos.

    Coluna de tipo categorical guarda o próprio texto. As demais guardam o valor
    numérico da escala, e o texto original fica em <nome>_txt.
    """
    raw = pd.read_csv(schema["file"])
    raw.columns = raw.columns.str.strip()

    missing = [q for q, _ in schema["columns"].values() if q not in raw.columns]
    if missing:
        raise KeyError(
            "Perguntas declaradas no esquema %s não existem em %s:\n  %s"
            % (schema["label"], schema["file"], "\n  ".join(missing))
        )

    frame = pd.DataFrame(index=raw.index)
    kinds = {}
    report = []

    for name, (question, kind) in schema["columns"].items():
        text = raw[question].map(clean_text)
        kinds[name] = kind

        if kind == "categorical":
            frame[name] = text
            continue

        frame[name] = text.map(SCALES[kind])
        frame[name + "_txt"] = text

        unmapped = sorted(set(text[frame[name].isna() & text.notna()]))
        if unmapped:
            report.append((name, unmapped))

    if kinds.get("considered_quitting") == "likert":
        quitting = frame["considered_quitting"]
        frame["considered_quitting_bin"] = (
            quitting.ge(QUITTING_AGREEMENT_THRESHOLD).astype(float).where(quitting.notna())
        )

    frame.attrs.update(
        label=schema["label"],
        year=schema["year"],
        month=schema["month"],
        block=schema["block"],
        kinds=kinds,
        conversion_report=report,
    )
    return frame


def load_all(verbose=True):
    """Carrega todos os formulários declarados e preenche o registro LOADED."""
    LOADED.clear()
    for name, schema in SCHEMAS.items():
        frame = load_survey(schema)
        frame.attrs["dataset"] = name
        LOADED[name] = frame
        if verbose:
            _print_report(name, frame)
    return dict(LOADED)


def resolve(value):
    """Aceita o nome de um dataset carregado ou o próprio DataFrame."""
    if isinstance(value, pd.DataFrame):
        return value
    if value not in LOADED:
        raise KeyError(
            "Dataset %r não carregado. Chame load_all() primeiro. Disponíveis: %s"
            % (value, ", ".join(sorted(LOADED)) or "nenhum")
        )
    return LOADED[value]


def _print_report(name, frame):
    """Imprime o resumo da carga e os valores que não bateram com a escala."""
    print("%s: %d respostas, %d variáveis" % (name, len(frame), len(frame.attrs["kinds"])))
    for variable, unmapped in frame.attrs["conversion_report"]:
        print("  %s não mapeou %d valor(es): %s" % (variable, len(unmapped), ", ".join(unmapped)))
