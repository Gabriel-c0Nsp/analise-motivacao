"""Carga dos CSVs da pesquisa com renomeação para os nomes canônicos."""

import pandas as pd

from survey.schemas import (
    BLOCKS,
    QUITTING_AGREEMENT_THRESHOLD,
    SCALES,
    SCHEMAS,
    STIPEND_ROLE,
)

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

    missing = [q for q, _, _ in schema["columns"].values() if q not in raw.columns]
    if missing:
        raise KeyError(
            "Perguntas declaradas no esquema %s não existem em %s:\n  %s"
            % (schema["label"], schema["file"], "\n  ".join(missing))
        )

    frame = pd.DataFrame(index=raw.index)
    kinds = {}
    blocks = {}
    report = []

    for name, (question, kind, block) in schema["columns"].items():
        text = raw[question].map(clean_text)
        kinds[name] = kind
        blocks[name] = block

        if kind == "categorical":
            frame[name] = text
            continue

        frame[name] = text.map(SCALES[kind])
        frame[name + "_txt"] = text

        unmapped = sorted(set(text[frame[name].isna() & text.notna()]))
        if unmapped:
            report.append((name, unmapped))

    frame.attrs.update(
        label=schema["label"],
        year=schema["year"],
        month=schema["month"],
        scopes=dict(schema["scopes"]),
        kinds=kinds,
        blocks=blocks,
        derived=[],
        declared_columns=len(schema["columns"]),
        conversion_report=report,
    )

    if "activity_role" in kinds:
        to_stipend_flag(frame)
    if "considered_quitting" in kinds:
        to_agreement(frame, "considered_quitting")

    return frame


def to_stipend_flag(dataset, role=STIPEND_ROLE, name="has_stipend"):
    """Marca quem de fato recebe bolsa, a partir do papel declarado na atividade.

    Existe porque o bloco de bolsa precisa de uma binária para recortar e o
    formulário não pergunta direto se a pessoa recebe bolsa: quem responde
    escolhe entre bolsista, voluntário e o papel não se aplicar. Fica no bloco
    de atividade, e não no de bolsa, porque descreve o papel de quem tem
    atividade, e não a bolsa em si.
    """
    frame = resolve(dataset)
    papel = frame["activity_role"]
    register_derived(
        frame, name, papel.eq(role).astype(float).where(papel.notna()), "binary", block="activity"
    )
    return name


def to_agreement(dataset, name, threshold=QUITTING_AGREEMENT_THRESHOLD, suffix="_bin"):
    """Reduz um item Likert a concorda contra não concorda, em `<nome><sufixo>`.

    Existe para comparar um item que virou Likert com a versão binária do mesmo
    item em outro formulário, e para alimentar o teste de Fisher, que precisa de
    duas classes. Item já binário é apenas copiado, sem limiar. Resposta ausente
    continua ausente, em vez de virar zero.
    """
    frame = resolve(dataset)
    kind = frame.attrs["kinds"][name]
    derived = name + suffix

    if kind == "binary":
        values = frame[name].astype(float)
    elif kind == "likert":
        values = frame[name].ge(threshold).astype(float).where(frame[name].notna())
    else:
        raise ValueError(
            "%r é do tipo %r. Só faz sentido dicotomizar item Likert ou binário." % (name, kind)
        )

    register_derived(frame, derived, values, "binary")
    return derived


def register_derived(frame, name, values, kind, block=None):
    """Acrescenta uma coluna calculada e a declara nos metadados do quadro.

    Sem o registro, a coluna existe mas é invisível para quem lê `kinds`, e
    `freq_table` levanta `KeyError` ao encontrá-la. O bloco padrão é o do item
    de origem quando ele existe, e o bloco geral caso contrário.
    """
    if block is None:
        block = frame.attrs["blocks"].get(name.rsplit("_", 1)[0], "general")
    if block not in BLOCKS:
        raise KeyError("bloco %r desconhecido. Conhecidos: %s" % (block, ", ".join(BLOCKS)))

    frame[name] = values
    frame.attrs["kinds"][name] = kind
    frame.attrs["blocks"][name] = block
    if name not in frame.attrs["derived"]:
        frame.attrs["derived"].append(name)
    return frame[name]


def block_frame(dataset, block):
    """Recorta o quadro para quem o bloco de fato descreve, e renomeia o rótulo.

    Toda leitura de um bloco com recorte declarado passa por aqui. Sem o
    recorte, a média, o percentual e o alfa de Cronbach do bloco descrevem em
    parte quem respondeu uma pergunta que não vale para ele. Quando o dataset
    não declara recorte para o bloco, devolve o quadro sem mudança: é o caso de
    um formulário que já foi respondido só por quem o bloco descreve.
    """
    frame = resolve(dataset)
    if block not in BLOCKS:
        raise KeyError("bloco %r desconhecido. Conhecidos: %s" % (block, ", ".join(BLOCKS)))

    scope = frame.attrs["scopes"].get(block)
    if scope is None:
        return frame

    recorte = frame[frame[scope] == 1].copy()
    recorte.attrs = dict(frame.attrs)
    recorte.attrs["kinds"] = dict(frame.attrs["kinds"])
    recorte.attrs["blocks"] = dict(frame.attrs["blocks"])
    recorte.attrs["derived"] = list(frame.attrs["derived"])
    recorte.attrs["scopes"] = dict(frame.attrs["scopes"])
    recorte.attrs["label"] = "%s (%s)" % (frame.attrs["label"], BLOCKS[block]["scope_label"])
    return recorte


def activity_frame(dataset):
    """Atalho para o recorte do bloco de atividade, o mais usado dos dois."""
    return block_frame(dataset, "activity")


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
    # A contagem sai de declared_columns, e não de kinds, porque kinds também
    # cobre as colunas derivadas na carga, como considered_quitting_bin.
    print("%s: %d respostas, %d variáveis" % (name, len(frame), frame.attrs["declared_columns"]))
    for variable, unmapped in frame.attrs["conversion_report"]:
        print("  %s não mapeou %d valor(es): %s" % (variable, len(unmapped), ", ".join(unmapped)))
