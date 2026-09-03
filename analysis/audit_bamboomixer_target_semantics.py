"""Correct the primary BambooMixer benchmark to the declared LiAsF6 target.

The downloaded extension archive contains LiAsF6 plus four reference salts.
The original retrospective script evaluated every archive row although the
design and manuscript declared LiAsF6 as the target.  This audit restricts the
already-generated, seed-averaged predictions to exact LiAsF6 records and
repeats the frozen formula-group bootstrap.  It does not refit or tune a model.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from common import RESULTS, ensure_output_dirs
from mixture_response_transfer_common import (
    conductivity_records,
    formula_signature,
    load_json_records,
    mixture_features,
    regression_metrics,
    response_target,
    salt_identity,
    sha256,
    stable_seed,
)
from run_bamboomixer_response_transfer_development import (
    anchor_metrics,
    bootstrap_external_contrasts,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "bamboomixer_response_transfer_design.json"
TARGET_PATH = HERE / "external_data" / "bamboomixer_response_transfer" / "LiAsF6_conductivity.json"
PREDICTIONS_PATH = RESULTS / "bamboomixer_response_transfer_external_predictions.csv"
METRICS_PATH = RESULTS / "bamboomixer_LiAsF6_only_external_metrics.csv"
BOOTSTRAP_PATH = RESULTS / "bamboomixer_LiAsF6_only_group_bootstrap.csv"
SUMMARY_PATH = RESULTS / "bamboomixer_LiAsF6_only_summary.json"
ANCHOR_PATH = RESULTS / "bamboomixer_LiAsF6_only_anchor_metrics.csv"
CORRECTED_PREDICTIONS_PATH = RESULTS / "bamboomixer_LiAsF6_only_external_predictions.csv"


def interval(values: pd.Series) -> list[float]:
    return [float(values.quantile(0.025)), float(values.quantile(0.975))]


def main() -> None:
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if sha256(TARGET_PATH) != design["sources"]["target_sha256"]:
        raise RuntimeError("Target archive hash mismatch")
    records = conductivity_records(load_json_records(TARGET_PATH))
    archive_salts = np.asarray([salt_identity(record) for record in records])
    selected_rows = np.flatnonzero(archive_salts == "LiAsF6")
    if len(selected_rows) == 0:
        raise AssertionError("No LiAsF6 records")

    predictions = pd.read_csv(PREDICTIONS_PATH)
    selected = predictions[predictions["target_row"].isin(selected_rows)].copy()
    if selected["target_row"].nunique() != len(selected_rows):
        raise AssertionError("Prediction rows do not align with target archive")
    selected.to_csv(CORRECTED_PREDICTIONS_PATH, index=False)

    metric_rows = []
    prediction_map: dict[str, np.ndarray] = {}
    ordered_rows = np.asarray(sorted(selected_rows.tolist()))
    y_target: np.ndarray | None = None
    for scope, frame in selected.groupby("scope", sort=True):
        frame = frame.sort_values("target_row")
        if not np.array_equal(frame["target_row"].to_numpy(), ordered_rows):
            raise AssertionError(f"Target-row order changed for {scope}")
        y = frame["y_log10_conductivity"].to_numpy(dtype=float)
        prediction = frame["prediction_log10_conductivity"].to_numpy(dtype=float)
        if y_target is None:
            y_target = y
        elif not np.allclose(y_target, y):
            raise AssertionError("Outcomes changed between scopes")
        prediction_map[str(scope)] = prediction
        metric_rows.append({"scope": scope, **regression_metrics(y, prediction)})
    assert y_target is not None
    metrics = pd.DataFrame(metric_rows).sort_values("scope")
    metrics.to_csv(METRICS_PATH, index=False)

    selected_records = [records[index] for index in ordered_rows]
    formula_groups = np.asarray(
        [formula_signature(record) for record in selected_records]
    )
    bootstrap = bootstrap_external_contrasts(
        y_target,
        prediction_map,
        formula_groups,
        repetitions=int(design["evaluation"]["group_bootstrap_repetitions"]),
        seed=stable_seed("external-bootstrap", "LiAsF6-only-semantic-correction"),
    )
    bootstrap.to_csv(BOOTSTRAP_PATH, index=False)
    strict_x = mixture_features(selected_records)
    strict_y = response_target(selected_records)
    anchors = anchor_metrics(
        strict_x,
        strict_y,
        formula_groups,
        prediction_map["all_source_salts"],
        budgets=[5],
        draws=int(design["evaluation"]["coverage_anchor_draws"]),
        alpha=float(design["models"]["few_shot_adapter"]["alpha"]),
    )
    anchors.to_csv(ANCHOR_PATH, index=False)
    five_anchor_macro = (
        anchors.groupby("model", sort=True)[["log_rmse", "raw_r2", "spearman"]]
        .mean()
        .to_dict(orient="index")
    )
    by_scope = metrics.set_index("scope")
    full = by_scope.loc["all_source_salts"]
    contrasts = {}
    for comparator, frame in bootstrap.groupby("comparator", sort=True):
        contrasts[str(comparator)] = {
            "relative_log_rmse_gain_mean": float(frame["relative_log_rmse_gain"].mean()),
            "relative_log_rmse_gain_ci95": interval(frame["relative_log_rmse_gain"]),
            "spearman_gain_mean": float(frame["spearman_gain"].mean()),
            "spearman_gain_ci95": interval(frame["spearman_gain"]),
            "raw_r2_gain_mean": float(frame["raw_r2_gain"].mean()),
            "raw_r2_gain_ci95": interval(frame["raw_r2_gain"]),
        }

    summary = {
        "status": "verified-semantic-correction-post-outcome",
        "claim_guard": (
            "This correction restricts existing predictions to the declared LiAsF6 target. "
            "It does not refit or tune a model and cannot change the retrospective status of the benchmark."
        ),
        "problem_found": (
            "The extension archive contains LiAsF6 and four reference salts; the original analysis "
            "mistakenly treated every archive row as the declared LiAsF6 target."
        ),
        "archive_salt_rows": dict(sorted(Counter(archive_salts.tolist()).items())),
        "declared_target": "LiAsF6",
        "corrected_target_rows": int(len(selected_rows)),
        "corrected_target_formulations": int(len(set(formula_groups.tolist()))),
        "corrected_external_metrics": {
            key: (int(value) if key == "n" else float(value))
            for key, value in full.to_dict().items()
        },
        "corrected_contrasts": contrasts,
        "corrected_five_anchor_macro": five_anchor_macro,
        "files": {
            METRICS_PATH.name: sha256(METRICS_PATH),
            BOOTSTRAP_PATH.name: sha256(BOOTSTRAP_PATH),
            ANCHOR_PATH.name: sha256(ANCHOR_PATH),
            CORRECTED_PREDICTIONS_PATH.name: sha256(CORRECTED_PREDICTIONS_PATH),
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
