"""Scores compostos: média de itens que se comportam como uma escala só."""

import pandas as pd

from survey.loading import register_derived, resolve
from survey.stats import cronbach_alpha

# Cada score é a média dos seus itens, o que preserva a faixa de 1 a 5 e deixa o
# valor comparável com o dos itens de origem. `min_alpha` é o piso de
# confiabilidade abaixo do qual o score é construído mas marcado como duvidoso,
# em vez de entrar silenciosamente numa análise.
SCORE_DEFS = {
    "score_belonging": {
        "items": ["welcomed_by_faculty", "welcoming_environment", "teaching_quality"],
        "block": "general",
        "label": "Pertencimento",
        "min_alpha": 0.70,
    },
    "score_prospects": {
        "items": ["job_ready", "career_clarity"],
        "block": "general",
        "label": "Perspectiva profissional",
        "min_alpha": 0.60,
    },
}

# Agrupamentos que a intuição sugere e os dados recusam. Ficam registrados para
# não voltarem por engano, e porque a recusa é resultado da pesquisa.
REJECTED_SCORES = {
    "sobrecarga": (
        "burnout, lacks_time e financial_impact dão alfa de 0,11 sobre as 39 respostas "
        "de 2026. Esgotamento, falta de tempo e aperto financeiro são pressões "
        "independentes nesta amostra, e entram nas análises como três variáveis."
    ),
    "atividade": (
        "good_supervision, recognition_motivates e career_contribution dão alfa de 0,82 "
        "sobre as 39 respostas e de apenas 0,33 sobre os 25 participantes reais. O valor "
        "alto vem da seção obrigatória respondida por quem não tem atividade. Restrito a "
        "quem participa, o bloco não forma escala."
    ),
}


def build_scores(dataset, defs=None):
    """Constrói os scores possíveis, registra cada um e devolve o relatório.

    Um score só é construído quando todos os seus itens existem no quadro. O que
    faltar é anunciado com os itens ausentes, em vez de sair silenciosamente da
    análise. A linha com resposta faltando em qualquer item fica ausente no
    score, para a média nunca ser tirada sobre um subconjunto dos itens.
    """
    frame = resolve(dataset)
    defs = SCORE_DEFS if defs is None else defs

    linhas = []
    for name, definition in defs.items():
        items = definition["items"]
        missing = [item for item in items if item not in frame.columns]
        if missing:
            print(
                "%s não construído em %s: falta %s"
                % (name, frame.attrs.get("label", "o quadro"), ", ".join(missing))
            )
            continue

        values = frame[items].mean(axis=1).where(frame[items].notna().all(axis=1))
        register_derived(frame, name, values, "score", block=definition["block"])

        alpha = cronbach_alpha(frame, items)
        ok = alpha >= definition["min_alpha"]
        if not ok:
            print(
                "%s tem alfa de %.3f, abaixo do mínimo de %.2f declarado"
                % (name, alpha, definition["min_alpha"])
            )
        linhas.append((name, len(items), int(values.notna().sum()), alpha,
                       definition["min_alpha"], ok))

    return pd.DataFrame(
        linhas, columns=["score", "items", "n", "alpha", "min_alpha", "ok"]
    ).set_index("score")


def score_table(dataset):
    """Resumo numérico dos scores já construídos no quadro."""
    frame = resolve(dataset)
    names = [n for n in frame.attrs["derived"] if frame.attrs["kinds"].get(n) == "score"]
    if not names:
        raise KeyError(
            "%s não tem score construído. Chame build_scores() primeiro."
            % frame.attrs.get("label", "o quadro")
        )

    values = frame[names]
    return pd.DataFrame(
        {
            "n": values.notna().sum(),
            "mean": values.mean(),
            "sd": values.std(ddof=1),
            "min": values.min(),
            "max": values.max(),
        }
    )
