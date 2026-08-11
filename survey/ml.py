"""Clusterização e predição sobre os scores e as variáveis do bloco geral."""

import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import silhouette_score
from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    cross_val_score,
    permutation_test_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from survey.loading import resolve
from survey.stats import check_activity_scope

RANDOM_STATE = 42

# Oito variáveis para 39 respostas. O limite é a amostra: cada item que entra
# aproxima o número de colunas do número de linhas, e a partir daí o modelo
# decora em vez de aprender. Os dois scores substituem os cinco itens que os
# compõem, e é isso que mantém a conta viável. Todas do bloco geral, porque o
# bloco de atividade só descreve os 25 participantes.
DEFAULT_FEATURES = [
    "score_belonging",
    "score_prospects",
    "burnout",
    "financial_impact",
    "keeps_up",
    "works",
    "term",
    "participates_lab",
]

# Métrica que trata as duas classes igualmente, porque os alvos são
# desbalanceados e a acurácia simples premiaria chutar sempre a classe maior.
SCORING = "balanced_accuracy"


def _cv():
    """Validação cruzada repetida, estratificada e com semente fixa.

    Cinco dobras sobre 39 respostas deixam cerca de 8 por dobra, poucas demais
    para uma única passada dizer alguma coisa. As dez repetições variam o corte
    e o desvio entre elas é parte do resultado, não ruído a esconder.
    """
    return RepeatedStratifiedKFold(n_splits=5, n_repeats=10, random_state=RANDOM_STATE)


def _models():
    """Baseline mais os dois classificadores, todos com semente fixa.

    A regularização da logística e a profundidade da árvore são baixas de
    propósito: com 39 linhas, qualquer folga vira memorização.
    """
    return {
        "baseline": DummyClassifier(strategy="stratified", random_state=RANDOM_STATE),
        "logistica": make_pipeline(
            StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)
        ),
        "arvore": DecisionTreeClassifier(
            max_depth=3, min_samples_leaf=5, random_state=RANDOM_STATE
        ),
    }


def _features(frame, features):
    """Resolve a lista de variáveis e recusa o que não pode ser lido no quadro."""
    features = list(DEFAULT_FEATURES if features is None else features)

    faltando = [f for f in features if f not in frame.columns]
    scores = [f for f in faltando if f.startswith("score_")]
    if scores:
        raise KeyError(
            "%s ainda não existe(m) em %s. Chame build_scores() antes."
            % (", ".join(scores), frame.attrs.get("label", "o quadro"))
        )
    if faltando:
        raise KeyError("%s não existe(m) no quadro" % ", ".join(faltando))

    check_activity_scope(frame, features)
    return features


def build_xy(dataset, target, features=None):
    """Monta a matriz de variáveis e o vetor do alvo, descartando linhas incompletas.

    O alvo sai das variáveis quando aparece nas duas listas, para o modelo não
    prever a coluna a partir dela mesma.
    """
    frame = resolve(dataset)
    features = [f for f in _features(frame, features) if f != target]
    check_activity_scope(frame, [target])

    if frame.attrs["kinds"].get(target) != "binary":
        raise ValueError(
            "%r não é binário. A predição aqui é de classificação em duas classes." % target
        )

    completo = frame[features + [target]].dropna()
    return completo[features], completo[target].astype(int)


def _matrix(frame, features):
    """Matriz padronizada, sem a qual a distância seria dominada pela escala de `term`."""
    values = frame[features].dropna()
    return values.index, StandardScaler().fit_transform(values.to_numpy(float))


def cluster_scan(dataset, features=None, k_range=range(2, 6)):
    """Silhueta de cada k pelos dois métodos, e o quanto as duas partições coincidem.

    A coluna `agreement` é a fração de respostas que caem no mesmo grupo pelos
    dois métodos, depois de casar cada grupo de um lado com o mais parecido do
    outro. Vale mais que a silhueta sozinha: dois algoritmos diferentes
    chegando à mesma partição é evidência de que os grupos não são artefato de
    um deles.
    """
    frame = resolve(dataset)
    features = _features(frame, features)
    _, values = _matrix(frame, features)

    linhas = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE).fit_predict(values)
        ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(values)
        cruzamento = pd.crosstab(kmeans, ward)
        linhas.append(
            (
                k,
                silhouette_score(values, kmeans),
                silhouette_score(values, ward),
                cruzamento.max(axis=1).sum() / len(values),
            )
        )

    return pd.DataFrame(linhas, columns=["k", "kmeans", "ward", "agreement"]).set_index("k")


def cluster_labels(dataset, k, method="kmeans", features=None):
    """Grupo de cada resposta, indexado como o quadro de origem."""
    frame = resolve(dataset)
    features = _features(frame, features)
    index, values = _matrix(frame, features)

    if method == "kmeans":
        labels = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE).fit_predict(values)
    elif method == "ward":
        labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(values)
    else:
        raise ValueError("método %r desconhecido. Use 'kmeans' ou 'ward'." % method)

    return pd.Series(labels, index=index, name="cluster")


def cluster_profile(dataset, labels, features=None, extras=()):
    """Média de cada variável por grupo, com o tamanho do grupo no cabeçalho.

    `extras` acrescenta variáveis que ficaram fora da clusterização, para ver
    como os desfechos se distribuem entre grupos formados sem olhar para eles.
    """
    frame = resolve(dataset)
    linhas = _features(frame, features) + list(extras)

    perfil = frame.loc[labels.index, linhas].groupby(labels).mean().T
    perfil.columns = [
        "grupo %s (n=%d)" % (grupo, (labels == grupo).sum()) for grupo in perfil.columns
    ]
    return perfil


def compare_models(X, y, models=None):
    """Média e desvio da métrica por modelo, do melhor para o pior.

    O baseline entra como linha da tabela, e não como nota de rodapé: sem ele,
    não dá para saber se um número parecido com 0,7 é aprendizado ou é o que
    sairia de chutar respeitando a proporção das classes.
    """
    models = _models() if models is None else models
    cv = _cv()

    linhas = []
    for nome, modelo in models.items():
        valores = cross_val_score(modelo, X, y, cv=cv, scoring=SCORING)
        linhas.append((nome, valores.mean(), valores.std()))

    tabela = pd.DataFrame(linhas, columns=["model", "mean", "sd"]).set_index("model")
    return tabela.sort_values("mean", ascending=False)


def permutation_p(X, y, model=None, n_permutations=300):
    """Compara o modelo contra ele mesmo treinado com os rótulos embaralhados.

    Devolve o score real e a fração de embaralhamentos que chegaram tão longe
    quanto ele. É o teste certo para "o modelo aprendeu algo": a diferença
    entre modelo e baseline na tabela não vem com p, porque as dobras se
    repetem e não são independentes.
    """
    model = _models()["logistica"] if model is None else model
    score, _, p = permutation_test_score(
        model,
        X,
        y,
        cv=_cv(),
        scoring=SCORING,
        n_permutations=n_permutations,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return score, p


def logistic_coefficients(X, y):
    """Coeficientes da logística sobre as variáveis padronizadas, do maior módulo ao menor.

    Padronizadas, as magnitudes são comparáveis entre si. O sinal diz a direção
    e o módulo diz o peso, mas com 39 respostas nenhum coeficiente isolado
    sustenta afirmação sobre causa.
    """
    modelo = _models()["logistica"].fit(X, y)
    coeficientes = pd.Series(modelo[-1].coef_[0], index=X.columns, name="coef")
    return coeficientes.sort_values(key=abs, ascending=False)
