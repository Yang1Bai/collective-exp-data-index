"""Multimodal attention models for catalyst knowledge transfer."""

from .data import (
    CatalystSample,
    load_ocx24_csv,
    load_seccm_archives,
    load_specgen_archive,
)
from .model import CatalystAttentionConfig, CatalystTransferTransformer
from .baselines import (
    CatalystTabularFeaturizer,
    ExpertPortfolioPrediction,
    TabPFNCatalystBaseline,
    combine_expert_predictions,
    fit_tabpfn_baseline,
)

__all__ = [
    "CatalystAttentionConfig",
    "CatalystSample",
    "CatalystTabularFeaturizer",
    "CatalystTransferTransformer",
    "ExpertPortfolioPrediction",
    "TabPFNCatalystBaseline",
    "combine_expert_predictions",
    "fit_tabpfn_baseline",
    "load_ocx24_csv",
    "load_seccm_archives",
    "load_specgen_archive",
]
