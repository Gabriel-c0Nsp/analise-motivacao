"""Confiabilidade de escala e correlação de postos sobre os nomes canônicos."""

import pandas as pd
from scipy.stats import spearmanr

from survey.loading import resolve


def check_activity_scope(frame, items):
    """Recusa ler o bloco de atividade num quadro que ainda tem quem não participa.

    Em 2026 a seção de atividade era obrigatória, então quem declarou não ter
    atividade também respondeu. Essas respostas não descrevem experiência
    nenhuma e mesmo assim entram na variância: sobre as 39 respostas o alfa do
    bloco dá 0,822 e sobre os 25 participantes dá 0,331. A recusa obriga a
    passar por `activity_frame` antes de qualquer leitura do bloco.
    """
    scope = frame.attrs.get("activity_scope")
    blocks = frame.attrs.get("blocks", {})
    if scope is None or scope not in frame.columns:
        return

    do_bloco = [item for item in items if blocks.get(item) == "activity"]
    if not do_bloco:
        return

    fora = int((frame[scope] != 1).sum())
    if fora:
        raise KeyError(
            "%s pertence(m) ao bloco de atividade e %s tem %d resposta(s) de quem "
            "declarou não participar. Passe o quadro por activity_frame() antes."
            % (", ".join(do_bloco), frame.attrs.get("label", "o quadro"), fora)
        )


def cronbach_alpha(dataset, items):
    """Alfa de Cronbach dos itens, medindo o quanto eles se comportam como uma escala.

    Só considera as linhas com resposta em todos os itens. Supõe os itens
    pontuados no mesmo sentido: um item invertido derruba o alfa e precisa ser
    reescalado antes de entrar.
    """
    frame = resolve(dataset)
    check_activity_scope(frame, items)

    if len(items) < 2:
        raise ValueError("o alfa de Cronbach precisa de pelo menos dois itens")

    values = frame[list(items)].dropna()
    total_var = values.sum(axis=1).var(ddof=1)
    if total_var == 0:
        raise ValueError("a soma dos itens não tem variância, o alfa é indefinido")

    k = len(items)
    return k / (k - 1) * (1 - values.var(ddof=1).sum() / total_var)


def spearman_matrix(dataset, items):
    """Matriz de correlação de postos entre os itens, para ver quais andam juntos."""
    frame = resolve(dataset)
    check_activity_scope(frame, items)
    return frame[list(items)].corr(method="spearman")


def spearman_pairs(dataset, predictors, targets):
    """Correlação de postos de cada preditor contra cada alvo, com p e n.

    Devolve uma linha por par, da correlação mais forte para a mais fraca em
    módulo. Sem correção para comparações múltiplas: com dezenas de pares, um p
    abaixo de 0,05 isolado não sustenta conclusão sozinho.
    """
    frame = resolve(dataset)
    check_activity_scope(frame, list(predictors) + list(targets))

    linhas = []
    for predictor in predictors:
        for target in targets:
            par = frame[[predictor, target]].dropna()
            constante = [c for c in (predictor, target) if par[c].nunique() < 2]
            if constante:
                # Acontece ao cruzar a própria coluna do recorte dentro do recorte.
                print(
                    "%s x %s sem correlação: %s não varia nas %d respostas"
                    % (predictor, target, " e ".join(constante), len(par))
                )
                rho, p = float("nan"), float("nan")
            else:
                rho, p = spearmanr(par[predictor], par[target])
            linhas.append((predictor, target, rho, p, len(par)))

    tabela = pd.DataFrame(linhas, columns=["predictor", "target", "rho", "p", "n"])
    tabela = tabela.reindex(tabela["rho"].abs().sort_values(ascending=False).index)
    return tabela.set_index(["predictor", "target"])
