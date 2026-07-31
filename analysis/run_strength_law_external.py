"""Test transport of a direct UTS--yield-strength law across alloy datasets."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import RESULTS, connect, ensure_output_dirs

SEED = 20260714
N_BOOT = 5000

DATASETS = {
    "borg": {
        "dataset": "mpea-dataset-borg",
        "ys": "PROPERTY: YS (MPa)",
        "uts": "PROPERTY: UTS (MPa)",
    },
    "birdshot": {
        "dataset": "birdshot-high-entropy-alloy-campaign",
        "ys": "Yield Strength (MPa)",
        "uts": "UTS_True (Mpa)",
    },
}


def paired_rows(label: str, spec: dict[str, str]) -> pd.DataFrame:
    with connect() as connection:
        raw = pd.read_sql_query(
            """SELECT source_row_id,material_key,property,value,conditions_json
               FROM measurements WHERE dataset=? AND property IN (?,?)""",
            connection,
            params=(spec["dataset"], spec["ys"], spec["uts"]),
        )
    pairs = raw.pivot_table(
        index=["source_row_id", "material_key"], columns="property", values="value", aggfunc="median"
    ).dropna().reset_index()
    pairs = pairs[(pairs[spec["ys"]] > 0) & (pairs[spec["uts"]] > 0)].copy()
    pairs = pairs.rename(columns={spec["ys"]: "YS_MPa", spec["uts"]: "UTS_MPa"})
    pairs["dataset_label"] = label
    pairs["log_ys"] = np.log10(pairs["YS_MPa"])
    pairs["log_uts"] = np.log10(pairs["UTS_MPa"])
    pairs["uts_ys_ratio"] = pairs["UTS_MPa"] / pairs["YS_MPa"]
    return pairs


def fit_line(frame: pd.DataFrame) -> dict[str, float]:
    slope, intercept = np.polyfit(frame["log_uts"], frame["log_ys"], 1)
    prediction = intercept + slope * frame["log_uts"].to_numpy(float)
    y = frame["log_ys"].to_numpy(float)
    r2 = 1 - np.sum((y - prediction) ** 2) / np.sum((y - y.mean()) ** 2)
    return {
        "n_rows": len(frame),
        "n_compositions": int(frame["material_key"].nunique()),
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
        "rmse_log10": float(np.sqrt(np.mean((y - prediction) ** 2))),
        "median_uts_ys_ratio": float(frame["uts_ys_ratio"].median()),
    }


def bootstrap_weights(frame: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    codes, keys = pd.factorize(frame["material_key"], sort=True)
    cluster_counts = rng.multinomial(len(keys), np.full(len(keys), 1 / len(keys)))
    return cluster_counts[codes].astype(float)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cutoff = weights.sum() / 2
    return float(values[np.searchsorted(np.cumsum(weights), cutoff, side="left")])


def weighted_fit(frame: pd.DataFrame, weights: np.ndarray) -> dict[str, float]:
    x = frame["log_uts"].to_numpy(float)
    y = frame["log_ys"].to_numpy(float)
    total = weights.sum()
    x_mean = np.sum(weights * x) / total
    y_mean = np.sum(weights * y) / total
    slope = np.sum(weights * (x - x_mean) * (y - y_mean)) / np.sum(weights * (x - x_mean) ** 2)
    intercept = y_mean - slope * x_mean
    prediction = intercept + slope * x
    denominator = np.sum(weights * (y - y_mean) ** 2)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(1 - np.sum(weights * (y - prediction) ** 2) / denominator),
        "median_uts_ys_ratio": weighted_median(frame["uts_ys_ratio"].to_numpy(float), weights),
    }


def external_metrics(source: pd.DataFrame, target: pd.DataFrame) -> dict[str, float]:
    source_fit = fit_line(source)
    prediction = source_fit["intercept"] + source_fit["slope"] * target["log_uts"].to_numpy(float)
    y = target["log_ys"].to_numpy(float)
    denominator = np.sum((y - y.mean()) ** 2)
    return {
        "external_r2": float(1 - np.sum((y - prediction) ** 2) / denominator),
        "external_rmse_log10": float(np.sqrt(np.mean((y - prediction) ** 2))),
        "external_mean_error_log10": float(np.mean(prediction - y)),
    }


def weighted_external_metrics(
    source: pd.DataFrame,
    source_weights: np.ndarray,
    target: pd.DataFrame,
    target_weights: np.ndarray,
) -> dict[str, float]:
    source_fit = weighted_fit(source, source_weights)
    prediction = source_fit["intercept"] + source_fit["slope"] * target["log_uts"].to_numpy(float)
    y = target["log_ys"].to_numpy(float)
    center = np.sum(target_weights * y) / target_weights.sum()
    denominator = np.sum(target_weights * (y - center) ** 2)
    error = prediction - y
    return {
        "external_r2": float(1 - np.sum(target_weights * error**2) / denominator),
        "external_rmse_log10": float(np.sqrt(np.sum(target_weights * error**2) / target_weights.sum())),
        "external_mean_error_log10": float(np.sum(target_weights * error) / target_weights.sum()),
    }


def main() -> None:
    ensure_output_dirs()
    frames = {label: paired_rows(label, spec) for label, spec in DATASETS.items()}
    overlap = set(frames["borg"]["material_key"]) & set(frames["birdshot"]["material_key"])
    if overlap:
        raise AssertionError(f"Borg/BIRDSHOT exact composition overlap: {len(overlap)}")
    pairs = pd.concat(frames.values(), ignore_index=True)
    pairs.to_csv(RESULTS / "strength_law_paired_rows.csv", index=False)
    fits = {label: fit_line(frame) for label, frame in frames.items()}
    external = external_metrics(frames["borg"], frames["birdshot"])
    reference_log_uts = float(pairs["log_uts"].median())

    rng = np.random.default_rng(SEED)
    rows = []
    for iteration in range(N_BOOT):
        borg_weights = bootstrap_weights(frames["borg"], rng)
        birdshot_weights = bootstrap_weights(frames["birdshot"], rng)
        borg_fit = weighted_fit(frames["borg"], borg_weights)
        birdshot_fit = weighted_fit(frames["birdshot"], birdshot_weights)
        ext = weighted_external_metrics(
            frames["borg"], borg_weights, frames["birdshot"], birdshot_weights
        )
        rows.append({
            "bootstrap": iteration,
            "slope_difference_borg_minus_birdshot": borg_fit["slope"] - birdshot_fit["slope"],
            "intercept_difference_borg_minus_birdshot": borg_fit["intercept"] - birdshot_fit["intercept"],
            "predicted_log_ys_difference_at_reference": (
                borg_fit["intercept"] + borg_fit["slope"] * reference_log_uts
                - birdshot_fit["intercept"] - birdshot_fit["slope"] * reference_log_uts
            ),
            "median_ratio_difference_borg_minus_birdshot": (
                borg_fit["median_uts_ys_ratio"] - birdshot_fit["median_uts_ys_ratio"]
            ),
            **ext,
        })
    bootstrap = pd.DataFrame(rows)
    bootstrap.to_csv(RESULTS / "strength_law_cluster_bootstrap.csv", index=False)

    def interval(column: str) -> list[float]:
        return bootstrap[column].quantile([0.025, 0.975]).tolist()

    summary = {
        "analysis_status": "post-external-confirmation-diagnostic",
        "canonical_composition_overlap": len(overlap),
        "fits": fits,
        "borg_to_birdshot": external,
        "reference_log10_uts": reference_log_uts,
        "cluster_bootstrap_95": {
            "slope_difference_borg_minus_birdshot": interval("slope_difference_borg_minus_birdshot"),
            "predicted_log_ys_difference_at_reference": interval("predicted_log_ys_difference_at_reference"),
            "median_ratio_difference_borg_minus_birdshot": interval("median_ratio_difference_borg_minus_birdshot"),
            "external_r2": interval("external_r2"),
        },
        "interpretation": (
            "The Borg direct linear calibration is strong in its source dataset but does not transport to "
            "BIRDSHOT. This rejects an unconditional shared calibration, not all conditional strength relations."
        ),
    }
    (RESULTS / "strength_law_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
