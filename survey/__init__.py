"""Pacote de análise dos formulários da pesquisa de motivação."""

from survey.descriptive import (
    common_vars,
    compare_freq,
    compare_items,
    crosstab_counts,
    crosstab_rowperc,
    freq_table,
)
from survey.loading import (
    LOADED,
    activity_frame,
    clean_text,
    load_all,
    load_survey,
    register_derived,
    resolve,
)
from survey.schemas import (
    BINARY,
    BLOCKS,
    CAVEATS,
    LIKERT_5,
    LIKERT_ORDER,
    RATING_5,
    RATING_ORDER,
    SCALES,
    SCHEMAS,
    TERM_11,
    WORKLOAD_4,
)
from survey.scores import REJECTED_SCORES, SCORE_DEFS, build_scores, score_table
from survey.stats import cronbach_alpha, spearman_matrix, spearman_pairs

__all__ = [
    "BINARY",
    "BLOCKS",
    "CAVEATS",
    "LIKERT_5",
    "LIKERT_ORDER",
    "LOADED",
    "RATING_5",
    "RATING_ORDER",
    "REJECTED_SCORES",
    "SCALES",
    "SCHEMAS",
    "SCORE_DEFS",
    "TERM_11",
    "WORKLOAD_4",
    "activity_frame",
    "build_scores",
    "clean_text",
    "common_vars",
    "compare_freq",
    "compare_items",
    "cronbach_alpha",
    "crosstab_counts",
    "crosstab_rowperc",
    "freq_table",
    "load_all",
    "load_survey",
    "register_derived",
    "resolve",
    "score_table",
    "spearman_matrix",
    "spearman_pairs",
]
