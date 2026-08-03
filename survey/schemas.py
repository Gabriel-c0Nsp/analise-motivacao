"""Escalas de conversão e esquemas dos formulários da pesquisa."""

LIKERT_5 = {
    "Discordo totalmente": 1,
    "Discordo parcialmente": 2,
    "Nem concordo nem discordo": 3,
    "Neutro": 3,
    "Concordo parcialmente": 4,
    "Concordo totalmente": 5,
}

LIKERT_ORDER = [
    "Discordo totalmente",
    "Discordo parcialmente",
    "Nem concordo nem discordo",
    "Neutro",
    "Concordo parcialmente",
    "Concordo totalmente",
]

BINARY = {"Não": 0, "Sim": 1}

RATING_5 = {
    "Muito ruim": 1,
    "Ruim": 2,
    "Neutro": 3,
    "Boa": 4,
    "Muito boa": 5,
}

RATING_ORDER = ["Muito ruim", "Ruim", "Neutro", "Boa", "Muito boa"]

# "Adequada" e "Boa" medem coisas diferentes (adequação versus qualidade),
# tornando a ordem entre as duas debatível.
WORKLOAD_4 = {
    "Inadequada": 1,
    "Adequada": 2,
    "Boa": 3,
    "Muito boa": 4,
}

TERM_11 = {
    "1º": 1,
    "2º": 2,
    "3º": 3,
    "4º": 4,
    "5º": 5,
    "6º": 6,
    "7º": 7,
    "8º": 8,
    "9º": 9,
    "10º": 10,
    "Concluindo cadeiras pendentes ou TCC (acima do intervalo de 10 períodos)": 11,
}

SCALES = {
    "likert": LIKERT_5,
    "binary": BINARY,
    "rating": RATING_5,
    "workload": WORKLOAD_4,
    "term": TERM_11,
}

# Resposta Likert a partir da qual "já pensei em desistir" equivale ao "Sim"
# da versão binária de 2025.
QUITTING_AGREEMENT_THRESHOLD = 4

SCHEMAS = {
    "students_2025_06": {
        "file": "dados/alunos_geral.csv",
        "label": "Alunos 2025",
        "year": 2025,
        "month": 6,
        "block": "general",
        "columns": {
            "age_range": ("Qual sua faixa etária?", "categorical"),
            "school_base": ("Recebi uma boa base de aprendizado durante os anos escolares.", "likert"),
            "welcomed_by_faculty": ("Me sinto acolhido(a) por professores e monitores quando tenho dúvidas.", "likert"),
            "participates_lab": ("Participa de algum laboratório ou projeto de pesquisa da universidade?", "binary"),
            "participates_extra": ("Participa de atividades extra curriculares, como eventos e esportes na faculdade?", "binary"),
            "financial_hardship": ("Atualmente enfrento dificuldades financeiras.", "likert"),
            "welcoming_environment": ("Considero o meio acadêmico do qual faço parte acolhedor.", "likert"),
            "has_scholarship": ("Recebe alguma bolsa/auxilio da faculdade?", "binary"),
            "dropped_courses": ("Já trancou cadeiras por não acompanhar o conteúdo?", "binary"),
            "change_major": ("Considera trocar de curso?", "binary"),
            "works": ("Trabalha no contraturno das aulas?", "binary"),
            "keeps_up": ("Consigo acompanhar a maioria dos conteúdos ministrados em sala de aula atualmente.", "likert"),
            "financial_impact": ("As dificuldades financeiras afetam minha vida acadêmica.", "likert"),
            "lab_helps": ("A participação em laboratórios ou projetos de pesquisa ajuda (ou ajudaria) a compreender melhor os conteúdos das disciplinas.", "likert"),
            "knows_opportunities": ("Você conhece as oportunidades de iniciação científica, monitoria ou laboratórios oferecidas pela universidade?", "binary"),
            "meets_requirements": ("Você atende aos requisitos necessários para participar de projetos de iniciação científica (CR acima de 7.0 e disciplinas pagas em caso de reprovação)?", "binary"),
            "job_ready": ("Me sinto preparado(a) para atuar no mercado de trabalho com o que aprendo na graduação.", "likert"),
            "curriculum_rating": ("Como você avalia a grade currilar vigente?", "rating"),
            "facilities_rating": ("Como você avalia a infraestrutura do prédio de computação?", "rating"),
        },
    },

    "researchers_2025_06": {
        "file": "dados/bolsistas.csv",
        "label": "Bolsistas 2025",
        "year": 2025,
        "month": 6,
        "block": "activity",
        "columns": {
            "age_range": ("Qual sua faixa etária?", "categorical"),
            "activity_type": ("Qual o tipo de atividade que você realiza atualmente?", "categorical"),
            "activity_role": ("Qual a sua participação em relação às atividades citadas acima?", "categorical"),
            "workload_rating": ("Como você avalia a carga horária da atividade em relação à sua rotina de estudos?", "workload"),
            "lab_helped": ("A participação em projetos de pesquisa ou laboratórios ajudou a compreender melhor os conteúdos vistos em sala de aula.", "likert"),
            "career_contribution": ("A atividade que desenvolvo no projeto contribui para a minha formação profissional.", "likert"),
            "considered_quitting": ("Já pensou em desistir da atividade de laboratório ou extensão por excesso de demandas acadêmicas?", "binary"),
            "stipend_enough": ("A bolsa que recebo é suficiente para cobrir minhas principais despesas acadêmicas.", "likert"),
            "good_supervision": ("Recebo orientação adequada do meu professor orientador.", "likert"),
            "lacks_time": ("Sinto que não tenho tempo suficiente para conciliar as disciplinas regulares, a atividade no laboratório/projeto e minha vida pessoal.", "likert"),
            "academic_output": ("Sua participação no projeto já resultou em alguma produção acadêmica? (ex: artigo, resumo, apresentação em evento, etc.).", "binary"),
            "recommended_to_peers": ("Você já recomendou a colegas a participação no laboratório ou projeto?", "binary"),
            "multiple_projects": ("Você participa de mais de um projeto/laboratório ao mesmo tempo?", "binary"),
            "soft_skills": ("A participação no laboratório/projeto contribui para o desenvolvimento das minhas habilidades interpessoais (como comunicação, trabalho em equipe e liderança).", "likert"),
            "recognition_motivates": ("O reconhecimento (formal ou informal) pelo meu trabalho no laboratório/projeto contribuiu para minha motivação no curso.", "likert"),
            "reduces_dropout": ("Acredito que as atividades extracurriculares contribuem para reduzir a evasão de alunos do curso.", "likert"),
        },
    },

    "students_researchers_2026_04": {
        "file": "dados/nova_pesquisa.csv",
        "label": "Pesquisa 2026",
        "year": 2026,
        "month": 4,
        "block": "general+activity",
        "columns": {
            "age_range": ("Qual sua faixa etária?", "categorical"),
            "term": ("Qual período você está cursando atualmente?", "term"),
            "participates_lab": ("Você participa de algum laboratório, projeto de pesquisa ou atividade de extensão na universidade?", "binary"),
            "works": ("Trabalha no contraturno das aulas?", "binary"),
            "financial_impact": ("As dificuldades financeiras afetam minha vida acadêmica.", "likert"),
            "welcomed_by_faculty": ("Me sinto acolhido(a) por professores e monitores quando tenho dúvidas.", "likert"),
            "welcoming_environment": ("Considero o meio acadêmico do qual faço parte acolhedor.", "likert"),
            "facilities_rating": ("Como você avalia a infraestrutura do prédio de computação?", "rating"),
            "keeps_up": ("Consigo acompanhar a maioria dos conteúdos ministrados em sala de aula atualmente.", "likert"),
            "teaching_quality": ("Estou satisfeito(a) com a qualidade das aulas ministradas pela maioria dos professores.", "likert"),
            "burnout": ("Já experienciei ansiedade, estresse intenso ou esgotamento em decorrência das demandas acadêmicas.", "likert"),
            "dropped_courses": ("Já trancou cadeiras por não acompanhar o conteúdo?", "binary"),
            "change_major": ("Considera trocar de curso?", "binary"),
            "job_ready": ("Me sinto preparado(a) para atuar no mercado de trabalho com o que aprendo na graduação.", "likert"),
            "career_clarity": ("Já tenho clareza sobre a área da Engenharia da Computação em que quero atuar profissionalmente.", "likert"),
            "curriculum_rating": ("Como você avalia a grade currilar vigente?", "rating"),
            "knows_opportunities": ("Você conhece as oportunidades de iniciação científica, monitoria ou laboratórios oferecidas pela universidade?", "binary"),
            "meets_requirements": ("Você atende aos requisitos necessários para participar de projetos de iniciação científica (CR acima de 7.0 e disciplinas pagas em caso de reprovação)?", "binary"),
            "lab_helps": ("A participação em laboratórios ou projetos de pesquisa ajuda (ou ajudaria) a compreender melhor os conteúdos das disciplinas.", "likert"),
            "activity_type": ("Qual o tipo de atividade que você realiza atualmente?", "categorical"),
            "activity_role": ("Qual a sua participação em relação às atividades citadas acima?", "categorical"),
            "career_contribution": ("A atividade que desenvolvo no projeto contribui para a minha formação profissional.", "likert"),
            "good_supervision": ("Recebo orientação adequada do meu professor orientador.", "likert"),
            "lacks_time": ("Sinto que não tenho tempo suficiente para conciliar as disciplinas regulares, a atividade no laboratório/projeto e minha vida pessoal.", "likert"),
            "recognition_motivates": ("O reconhecimento (formal ou informal) pelo meu trabalho no laboratório/projeto contribuiu para minha motivação no curso.", "likert"),
            "academic_output": ("Sua participação em projeto(s) já resultou em alguma produção acadêmica (artigo, resumo, apresentação em evento, etc.)?", "binary"),
            "considered_quitting": ("Já pensei em desistir da atividade de laboratório/extensão por excesso de demandas acadêmicas.", "likert"),
        },
    },
}

CAVEATS = {
    "participates_lab": (
        "Escopo mudou em 2026: passou a incluir atividade de extensão. A alta de 38% "
        "para 64% mistura mudança real com mudança de pergunta."
    ),
    "considered_quitting": (
        "Era binária em 2025 e virou Likert em 2026, por isso a comparação direta entre os "
        "dois formulários é recusada. A comparação válida é sobre considered_quitting_bin, "
        "coluna presente nos dois datasets, na qual a resposta Likert maior ou igual a 4 "
        "equivale ao Sim de 2025."
    ),
    "activity_type": (
        "Campo livre com 19 valores únicos em 39 respostas, incluindo 'Nenhum', 'nenhuma', "
        "'Estudo' e 'Trabalho remoto'. Exige normalização manual antes de qualquer uso."
    ),
    "lab_helps": (
        "Mede expectativa, porque é respondida também por quem nunca participou. Não é o "
        "mesmo item que lab_helped, que mede experiência e só existe em 2025."
    ),
}
