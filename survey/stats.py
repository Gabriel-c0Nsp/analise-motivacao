"""Confiabilidade de escala e correlação de postos sobre os nomes canônicos."""

import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu, spearmanr

from survey.loading import resolve
from survey.schemas import SCHEMAS


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


def fisher(dataset, a, b):
    """Teste exato de Fisher sobre a tabela 2x2 das duas variáveis binárias.

    Exato em vez de qui-quadrado porque as amostras são pequenas e as casas da
    tabela chegam a ter uma única resposta, faixa em que a aproximação do
    qui-quadrado não vale. Item Likert precisa passar antes por `to_agreement`.
    """
    frame = resolve(dataset)
    check_activity_scope(frame, [a, b])

    for name in (a, b):
        if frame.attrs["kinds"][name] != "binary":
            raise ValueError(
                "%r é do tipo %r. Fisher precisa de duas classes: use to_agreement()."
                % (name, frame.attrs["kinds"][name])
            )

    table = pd.crosstab(frame[a], frame[b])
    if table.shape != (2, 2):
        raise ValueError(
            "a tabela de %s por %s é %dx%d, e o teste exige 2x2"
            % (a, b, table.shape[0], table.shape[1])
        )

    odds, p = fisher_exact(table.to_numpy())
    return pd.Series(
        {"n": int(table.to_numpy().sum()), "odds_ratio": odds, "p": p},
        name="%s x %s" % (a, b),
    )


def mann_whitney(first, second, variable):
    """Compara a distribuição da variável entre dois datasets, por postos.

    Devolve as médias, a diferença, o U, o p e a correlação bisserial de
    postos, positiva quando o segundo dataset tem os valores mais altos. Trata
    as duas coletas como amostras independentes, o que não é estritamente
    verdade: são anônimas e provavelmente têm respondentes em comum, então o p
    é otimista e a comparação vale como descrição.
    """
    frames = [resolve(first), resolve(second)]
    for frame in frames:
        check_activity_scope(frame, [variable])

    kinds = {frame.attrs["kinds"].get(variable) for frame in frames}
    if len(kinds) != 1 or kinds == {None}:
        raise KeyError(
            "%r não tem o mesmo tipo nos dois datasets: %s"
            % (variable, ", ".join(sorted(str(k) for k in kinds)))
        )
    if kinds == {"categorical"}:
        raise ValueError("%r é categórica e não tem ordem para comparar por postos" % variable)

    x, y = (frame[variable].dropna() for frame in frames)
    u, p = mannwhitneyu(x, y, alternative="two-sided")
    return pd.Series(
        {
            "n_1": len(x),
            "n_2": len(y),
            "mean_1": x.mean(),
            "mean_2": y.mean(),
            "delta": y.mean() - x.mean(),
            "U": u,
            "p": p,
            "effect": 1 - 2 * u / (len(x) * len(y)),
        },
        name=variable,
    )


def compare_datasets(first, second, variables=None):
    """Uma linha de Mann-Whitney por variável comparável, da menor para a maior p.

    Sem variáveis informadas, compara tudo que os dois esquemas declaram com o
    mesmo nome e o mesmo tipo. Categóricas ficam de fora, por não terem ordem.
    Sem correção para comparações múltiplas: com uma dezena e meia de testes,
    espera-se um p abaixo de 0,05 por acaso.
    """
    frames = [resolve(first), resolve(second)]
    if variables is None:
        declared = [set(SCHEMAS[frame.attrs["dataset"]]["columns"]) for frame in frames]
        variables = sorted(set.intersection(*declared))

    linhas = []
    for variable in variables:
        kinds = {frame.attrs["kinds"].get(variable) for frame in frames}
        if len(kinds) != 1 or kinds & {None, "categorical"}:
            continue
        linhas.append(mann_whitney(frames[0], frames[1], variable))

    tabela = pd.DataFrame(linhas)
    tabela.index.name = "variable"
    return tabela.sort_values("p")
