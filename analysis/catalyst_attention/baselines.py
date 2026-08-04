"""Strong source-only baselines for catalyst transfer benchmarks."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from importlib.metadata import version
from pathlib import Path
import tempfile
from typing import Any, Sequence

import numpy as np
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import CatalystSample, read_pinned_bytes
from .schema import (
    MEASUREMENT_MODALITY_NAMES,
    REACTION_NAMES,
    TARGET_NAMES,
)
from .training import targets_array


TABPFN_PACKAGE_VERSION = "8.1.0"
TABPFN_MODEL_VERSION = "v2"
TABPFN_V2_REGRESSOR_SHA256 = (
    "2ab5a07d5c41dfe6db9aa7ae106fc6de898326c2765be66505a07e2868c10736"
)
TABPFN_V2_REGRESSOR_BYTES = 44_390_977


def _composition_matrix(
    samples: Sequence[CatalystSample], *, surface: bool
) -> np.ndarray:
    matrix = np.zeros((len(samples), 118), dtype=np.float32)
    for row, sample in enumerate(samples):
        elements = (
            sample.surface_elements if surface else sample.elements
        )
        fractions = (
            sample.surface_fractions if surface else sample.fractions
        )
        if len(elements):
            matrix[row, elements - 1] = fractions
    return matrix


def _aligned_curve_matrix(
    samples: Sequence[CatalystSample], length: int
) -> tuple[np.ndarray, np.ndarray]:
    destination = np.linspace(0.0, 1.0, length)
    matrix = np.zeros((len(samples), length * 2), dtype=np.float32)
    present = np.zeros(len(samples), dtype=bool)
    for row, sample in enumerate(samples):
        if not len(sample.curve_axis):
            continue
        source = np.linspace(0.0, 1.0, len(sample.curve_axis))
        channels = [
            np.interp(destination, source, sample.curve_values[:, channel])
            for channel in range(2)
        ]
        matrix[row] = np.concatenate(channels).astype(np.float32)
        present[row] = True
    return matrix, present


def _one_hot(values: np.ndarray, count: int) -> np.ndarray:
    if values.ndim != 1 or np.any(values < 0) or np.any(values >= count):
        raise ValueError("categorical value is outside the one-hot schema")
    matrix = np.zeros((len(values), count), dtype=np.float32)
    matrix[np.arange(len(values)), values] = 1.0
    return matrix


@dataclass
class CatalystTabularFeaturizer:
    """Leakage-safe fixed-width representation fitted on source rows only."""

    include_curve: bool = True
    include_surface: bool = True
    include_conditions: bool = True
    curve_components: int = 24
    maximum_curve_length: int = 256
    curve_length: int = 0
    curve_pipeline: Pipeline | None = None

    def fit(
        self, samples: Sequence[CatalystSample]
    ) -> "CatalystTabularFeaturizer":
        if not samples:
            raise ValueError("tabular featurizer requires source samples")
        for sample in samples:
            sample.validate()
        lengths = [
            len(sample.curve_axis)
            for sample in samples
            if len(sample.curve_axis)
        ]
        self.curve_pipeline = None
        self.curve_length = 0
        if self.include_curve and lengths:
            self.curve_length = min(
                self.maximum_curve_length,
                max(8, int(np.median(lengths))),
            )
            curves, present = _aligned_curve_matrix(
                samples, self.curve_length
            )
            curve_rows = curves[present]
            components = min(
                self.curve_components,
                len(curve_rows) - 1,
                curve_rows.shape[1],
            )
            if components > 0:
                self.curve_pipeline = Pipeline(
                    [
                        ("scale", StandardScaler()),
                        (
                            "pca",
                            PCA(
                                n_components=components,
                                random_state=0,
                            ),
                        ),
                    ]
                )
                self.curve_pipeline.fit(curve_rows)
        return self

    def transform(
        self, samples: Sequence[CatalystSample]
    ) -> np.ndarray:
        if not samples:
            raise ValueError("tabular transform requires samples")
        for sample in samples:
            sample.validate()
        blocks = [_composition_matrix(samples, surface=False)]
        if self.include_surface:
            blocks.extend(
                [
                    _composition_matrix(samples, surface=True),
                    np.asarray(
                        [
                            [float(bool(len(sample.surface_elements)))]
                            for sample in samples
                        ],
                        dtype=np.float32,
                    ),
                ]
            )
        if self.include_conditions:
            values = np.stack(
                [
                    sample.condition_values * sample.condition_mask
                    for sample in samples
                ]
            )
            masks = np.stack(
                [sample.condition_mask for sample in samples]
            )
            blocks.extend([values, masks])
        if self.include_curve:
            present = np.zeros(len(samples), dtype=np.float32)
            if self.curve_pipeline is not None and self.curve_length:
                curves, curve_present = _aligned_curve_matrix(
                    samples, self.curve_length
                )
                embedding = np.zeros(
                    (
                        len(samples),
                        int(
                            self.curve_pipeline.named_steps[
                                "pca"
                            ].n_components_
                        ),
                    ),
                    dtype=np.float32,
                )
                if curve_present.any():
                    embedding[curve_present] = self.curve_pipeline.transform(
                        curves[curve_present]
                    ).astype(np.float32)
                present = curve_present.astype(np.float32)
                blocks.append(embedding)
            blocks.append(present[:, None])
        blocks.extend(
            [
                _one_hot(
                    np.asarray(
                        [sample.reaction_id for sample in samples],
                        dtype=int,
                    ),
                    len(REACTION_NAMES),
                ),
                _one_hot(
                    np.asarray(
                        [sample.modality_id for sample in samples],
                        dtype=int,
                    ),
                    len(MEASUREMENT_MODALITY_NAMES),
                ),
                _one_hot(
                    np.asarray(
                        [
                            TARGET_NAMES.index(sample.target_name)
                            for sample in samples
                        ],
                        dtype=int,
                    ),
                    len(TARGET_NAMES),
                ),
            ]
        )
        matrix = np.concatenate(blocks, axis=1).astype(np.float32)
        if not np.isfinite(matrix).all():
            raise ValueError("tabular representation contains non-finite values")
        return matrix

    def fit_transform(
        self, samples: Sequence[CatalystSample]
    ) -> np.ndarray:
        return self.fit(samples).transform(samples)


@dataclass
class TabPFNCatalystBaseline:
    """Pinned TabPFN-v2 wrapper with a source-fitted catalyst featurizer."""

    model: Any
    featurizer: CatalystTabularFeaturizer
    package_version: str
    model_version: str
    model_sha256: str
    protected_model_directory: Any = field(repr=False)

    def predict(
        self, samples: Sequence[CatalystSample]
    ) -> np.ndarray:
        return np.asarray(
            self.model.predict(self.featurizer.transform(samples)),
            dtype=float,
        ).reshape(-1)

    def manifest(self) -> dict[str, str | int]:
        return {
            "package": "tabpfn",
            "package_version": self.package_version,
            "model_version": self.model_version,
            "model_sha256": self.model_sha256,
            "curve_components": (
                0
                if self.featurizer.curve_pipeline is None
                else int(
                    self.featurizer.curve_pipeline.named_steps[
                        "pca"
                    ].n_components_
                )
            ),
        }


def fit_tabpfn_baseline(
    source_samples: Sequence[CatalystSample],
    *,
    seed: int,
    include_curve: bool = True,
    include_surface: bool = True,
    include_conditions: bool = True,
    model_path: Path,
) -> TabPFNCatalystBaseline:
    """Fit the pinned non-commercial research baseline without target leakage."""

    try:
        from tabpfn import TabPFNRegressor
        from tabpfn.constants import ModelVersion
    except ImportError as error:
        raise RuntimeError(
            "TabPFN baseline requires analysis/catalyst_attention/"
            "requirements-advanced.txt"
        ) from error
    installed = version("tabpfn")
    if installed != TABPFN_PACKAGE_VERSION:
        raise RuntimeError(
            f"TabPFN {TABPFN_PACKAGE_VERSION} is required; found {installed}"
        )
    featurizer = CatalystTabularFeaturizer(
        include_curve=include_curve,
        include_surface=include_surface,
        include_conditions=include_conditions,
    )
    matrix = featurizer.fit_transform(source_samples)
    if not model_path.is_file():
        raise FileNotFoundError(f"TabPFN model not found: {model_path}")
    model_bytes = read_pinned_bytes(
        model_path,
        expected_sha256=TABPFN_V2_REGRESSOR_SHA256,
        expected_size=TABPFN_V2_REGRESSOR_BYTES,
    )
    model_sha256 = hashlib.sha256(model_bytes).hexdigest()
    protected_directory = tempfile.TemporaryDirectory(
        prefix="catalyst-tabpfn-model-"
    )
    protected_path = Path(protected_directory.name) / "tabpfn-v2.ckpt"
    try:
        protected_path.write_bytes(model_bytes)
        protected_path.chmod(0o400)
        model = TabPFNRegressor.create_default_for_version(
            ModelVersion.V2,
            model_path=protected_path,
            device="cpu",
            n_estimators=8,
            random_state=seed,
            ignore_pretraining_limits=True,
            fit_mode="low_memory",
            keep_cache_on_device=False,
            show_progress_bar=False,
        )
        model.fit(matrix, targets_array(source_samples))
    except Exception:
        protected_directory.cleanup()
        raise
    return TabPFNCatalystBaseline(
        model=model,
        featurizer=featurizer,
        package_version=installed,
        model_version=TABPFN_MODEL_VERSION,
        model_sha256=model_sha256,
        protected_model_directory=protected_directory,
    )


@dataclass(frozen=True)
class ExpertPortfolioPrediction:
    """Target-label-free ensemble with disagreement-based abstention."""

    mean: np.ndarray
    standard_deviation: np.ndarray
    eligible: np.ndarray
    disagreement_threshold: float
    weights: np.ndarray


def combine_expert_predictions(
    predictions: Sequence[np.ndarray],
    *,
    weights: Sequence[float] | None = None,
    abstention_fraction: float = 0.2,
) -> ExpertPortfolioPrediction:
    """Combine frozen experts without fitting weights on recipient outcomes."""

    if len(predictions) < 2:
        raise ValueError("expert portfolio requires at least two predictions")
    matrix = np.stack(
        [np.asarray(prediction, dtype=float) for prediction in predictions]
    )
    if matrix.ndim != 2 or matrix.shape[1] == 0:
        raise ValueError("expert predictions must be non-empty vectors")
    if not np.isfinite(matrix).all():
        raise ValueError("expert predictions contain non-finite values")
    if not 0.0 <= abstention_fraction < 1.0:
        raise ValueError("abstention_fraction must be in [0, 1)")
    if weights is None:
        normalized_weights = np.full(
            len(matrix), 1.0 / len(matrix), dtype=float
        )
    else:
        normalized_weights = np.asarray(weights, dtype=float)
        if (
            normalized_weights.shape != (len(matrix),)
            or not np.isfinite(normalized_weights).all()
            or np.any(normalized_weights < 0.0)
            or normalized_weights.sum() <= 0.0
        ):
            raise ValueError("expert weights must be finite and non-negative")
        normalized_weights /= normalized_weights.sum()
    mean = np.average(matrix, axis=0, weights=normalized_weights)
    variance = np.average(
        (matrix - mean[None, :]) ** 2,
        axis=0,
        weights=normalized_weights,
    )
    standard_deviation = np.sqrt(np.maximum(variance, 0.0))
    threshold = float(
        np.quantile(standard_deviation, 1.0 - abstention_fraction)
    )
    eligible = standard_deviation <= threshold
    return ExpertPortfolioPrediction(
        mean=mean,
        standard_deviation=standard_deviation,
        eligible=eligible,
        disagreement_threshold=threshold,
        weights=normalized_weights,
    )
