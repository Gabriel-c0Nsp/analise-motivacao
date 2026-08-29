"""Gera as figuras do relatório final, todas na mesma formatação.

Cada função devolve uma das figuras numeradas do relatório, já com o estilo
exigido: Times New Roman, corpo 10 em todo texto do desenho e gravação em 300
dpi. Nenhuma escreve título dentro da figura, porque a legenda numerada abaixo
dela, no texto, já a identifica.

A Figura 2 não aparece aqui: é uma captura de tela do repositório, e não um
gráfico.

Uso: python make_figures.py [diretório de saída]
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

from survey import (
    REPORT_WIDTH,
    build_scores,
    cluster_labels,
    cluster_profile,
    crosstab_counts,
    crosstab_rowperc,
    load_all,
    plot_cluster_profile,
    plot_crosstab,
    plot_dendrogram,
    save_figure,
    use_report_style,
)

OUTPUT_DIR = Path("figuras")

# Os grupos saem da clusterização numerados, e o número não diz nada a quem lê.
# A primeira lista está na ordem do rótulo, do grupo 0 ao 2, e a segunda na
# ordem em que os blocos aparecem da esquerda para a direita no dendrograma.
GROUP_NAMES = ["Período inicial", "Veteranos que trabalham", "Participantes com folga"]
GROUP_NAMES_LEFT_TO_RIGHT = ["Veteranos que trabalham", "Participantes com folga", "Período inicial"]

# Rótulo curto de cada nível da escala de concordância, quebrado em duas linhas
# para caber no eixo. O texto por extenso não cabe em cinco categorias lado a lado.
SHORT_LIKERT = {
    1: "Discordo\ntotalmente",
    2: "Discordo\nparcialmente",
    3: "Nem concordo\nnem discordo",
    4: "Concordo\nparcialmente",
    5: "Concordo\ntotalmente",
}

# Do vermelho ao azul, na ordem da escala, para a discordância e a concordância
# ficarem em extremos opostos e o neutro em cinza.
LIKERT_COLORS = ["#a50026", "#f46d43", "#d9d9d9", "#74add1", "#313695"]


def _percent(valor, casas=1):
    """Formata o percentual com vírgula decimal, como se escreve em português."""
    return ("%.*f%%" % (casas, valor)).replace(".", ",")


def figure_1_dendrogram(datasets):
    """Dendrograma de Ward sobre a pesquisa de 2026."""
    figura, eixo = plt.subplots(figsize=(REPORT_WIDTH, 2.8))
    plot_dendrogram(
        datasets["students_researchers_2026_04"],
        group_names=GROUP_NAMES_LEFT_TO_RIGHT,
        ax=eixo,
    )
    figura.tight_layout()
    return figura


def figure_3_cluster_profile(datasets):
    """Mapa de calor do perfil médio dos três grupos."""
    frame = datasets["students_researchers_2026_04"]
    perfil = cluster_profile(
        frame,
        cluster_labels(frame, k=3),
        extras=["change_major", "dropped_courses"],
        names=GROUP_NAMES,
    ).iloc[:, [1, 2, 0]]

    figura, eixo = plt.subplots(figsize=(REPORT_WIDTH, 4.4))
    plot_cluster_profile(perfil, ax=eixo)
    figura.tight_layout()
    return figura


def figure_4_requirements(datasets):
    """Participação segundo o atendimento aos requisitos, nas duas coletas.

    A leitura é por linha: de cada grupo de respondentes, quantos participam de
    atividade acadêmica. O n de cada linha entra no rótulo do eixo porque as
    duas linhas têm tamanhos bem diferentes, e o percentual sozinho esconde isso.
    """
    painel = [
        ("Alunos 2025 (n=29)", datasets["students_2025_06"]),
        ("Pesquisa 2026 (n=39)", datasets["students_researchers_2026_04"]),
    ]
    figura, eixos = plt.subplots(1, 2, figsize=(REPORT_WIDTH, 3.2), sharey=True)

    for eixo, (titulo, frame) in zip(eixos, painel):
        contagens = crosstab_counts(frame, "meets_requirements", "participates_lab")
        tabela = crosstab_rowperc(frame, "meets_requirements", "participates_lab")
        tabela.index = [
            "Não atende (n=%d)" % contagens.loc[0].sum(),
            "Atende (n=%d)" % contagens.loc[1].sum(),
        ]
        tabela.columns = ["Não participa", "Participa"]
        tabela.columns.name = "Atividade acadêmica"

        plot_crosstab(tabela, title=titulo, ax=eixo)
        for barra in eixo.patches:
            altura = barra.get_height()
            eixo.text(
                barra.get_x() + barra.get_width() / 2,
                altura + 1.5,
                _percent(altura),
                ha="center",
                va="bottom",
            )

    eixos[1].set_ylabel("")
    eixos[0].get_legend().remove()
    figura.tight_layout()
    return figura


def figure_5_welcoming(datasets):
    """Acolhimento percebido segundo a intenção de trocar de curso, nas duas coletas.

    A legenda da escala é única para os dois painéis, no rodapé, porque repetir
    cinco categorias em cada um ocuparia o espaço das próprias barras. Ela vem
    em três colunas: em uma linha só, os cinco rótulos ficam mais largos que a
    página, e a figura inteira teria de ser reduzida para caber.
    """
    painel = [
        ("Alunos 2025", datasets["students_2025_06"]),
        ("Pesquisa 2026", datasets["students_researchers_2026_04"]),
    ]
    figura, eixos = plt.subplots(2, 1, figsize=(REPORT_WIDTH, 5.2), sharey=True)

    for eixo, (titulo, frame) in zip(eixos, painel):
        contagens = crosstab_counts(frame, "change_major", "welcoming_environment")
        tabela = crosstab_rowperc(frame, "change_major", "welcoming_environment")
        medias = frame.groupby("change_major")["welcoming_environment"].mean()

        tabela.index = [
            "Não considera trocar\n(n=%d, média %s)"
            % (contagens.loc[0].sum(), ("%.2f" % medias[0]).replace(".", ",")),
            "Considera trocar\n(n=%d, média %s)"
            % (contagens.loc[1].sum(), ("%.2f" % medias[1]).replace(".", ",")),
        ]
        tabela.columns = [SHORT_LIKERT[nivel] for nivel in tabela.columns]
        tabela.columns.name = None

        plot_crosstab(tabela, title="%s (n=%d)" % (titulo, len(frame)), ax=eixo)
        for posicao, barra in enumerate(eixo.patches):
            barra.set_color(LIKERT_COLORS[posicao // len(tabela)])
        eixo.get_legend().remove()
        # Nenhuma categoria passa de 45% em nenhum dos grupos, e o eixo cheio
        # deixaria metade do desenho vazia. A escala é a mesma nos dois painéis,
        # então a comparação entre as coletas continua direta.
        eixo.set_ylim(0, 50)

    for eixo in eixos:
        eixo.set_ylabel("% das respostas do grupo")

    figura.legend(
        [plt.Rectangle((0, 0), 1, 1, color=cor) for cor in LIKERT_COLORS],
        [SHORT_LIKERT[nivel].replace("\n", " ") for nivel in range(1, 6)],
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 0.005),
    )
    figura.tight_layout(rect=[0, 0.11, 1, 1])
    return figura


FIGURES = {
    "figura-1-dendrograma.png": figure_1_dendrogram,
    "figura-3-perfil-dos-grupos.png": figure_3_cluster_profile,
    "figura-4-requisitos-e-participacao.png": figure_4_requirements,
    "figura-5-acolhimento-e-troca-de-curso.png": figure_5_welcoming,
}


def main(output_dir=OUTPUT_DIR):
    """Grava todas as figuras do relatório no diretório indicado."""
    plt.switch_backend("Agg")
    use_report_style()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = load_all(verbose=False)
    # As figuras de agrupamento usam os dois scores como variáveis, e eles são
    # colunas derivadas: precisam existir antes de qualquer desenho.
    build_scores(datasets["students_researchers_2026_04"])

    for nome, funcao in FIGURES.items():
        figura = funcao(datasets)
        save_figure(figura, output_dir / nome)
        plt.close(figura)
        print("gravado: %s" % (output_dir / nome))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DIR)
