"""Independent semantic checks for the BambooMixer method-development run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import RESULTS
from mixture_response_transfer_common import (
    formula_signature,
    load_json_records,
    mixture_features,
    regression_metrics,
    sha256,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "bamboomixer_response_transfer_design.json"
DEFAULT_DATA_DIR = HERE / "external_data" / "bamboomixer_response_transfer"
PREFIX = "bamboomixer_response_transfer"


def close(observed: float, expected: float, label: str) -> None:
    if not np.isclose(observed, expected, rtol=1e-9, atol=1e-11, equal_nan=True):
        raise AssertionError(f"{label}: {observed} != {expected}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--allow-quick", action="store_true")
    args = parser.parse_args()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    paths = {
        name: RESULTS / f"{PREFIX}_{name}.csv"
        for name in (
            "seed_audit",
            "external_predictions",
            "external_metrics",
            "external_group_bootstrap",
            "anchor_metrics",
            "salt_portfolio",
        )
    }
    paths["summary"] = RESULTS / f"{PREFIX}_summary.json"
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing response-transfer results: {missing}")

    source_path = args.data_dir / "bamboomixer_original_data.json"
    target_path = args.data_dir / "LiAsF6_conductivity.json"
    if sha256(source_path) != design["sources"]["source_sha256"]:
        raise AssertionError("Source hash mismatch")
    if sha256(target_path) != design["sources"]["target_sha256"]:
        raise AssertionError("Target hash mismatch")
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    if summary["status"] != "complete-method-development":
        raise AssertionError("Method-development run is incomplete")
    if summary["mode"] != "formal" and not args.allow_quick:
        raise AssertionError("Quick results cannot verify as formal")
    if summary["design_sha256"] != sha256(DESIGN_PATH):
        raise AssertionError("Design hash mismatch")

    target_records = load_json_records(target_path)
    if len(target_records) != int(design["eligibility"]["target_expected_rows"]):
        raise AssertionError("Target row count changed")
    groups = [formula_signature(record) for record in target_records]
    total_groups = len(set(groups))
    if total_groups != int(
        design["eligibility"]["target_expected_exact_formulations"]
    ):
        raise AssertionError("Exact formulation count changed")
    first = target_records[0]
    reversed_record = {
        **first,
        "solvents": list(reversed(first["solvents"])),
        "salts": list(reversed(first["salts"])),
    }
    if not np.allclose(
        mixture_features([first]),
        mixture_features([reversed_record]),
        rtol=0.0,
        atol=1e-14,
    ):
        raise AssertionError("Mixture representation lost permutation invariance")

    predictions = pd.read_csv(paths["external_predictions"])
    metrics = pd.read_csv(paths["external_metrics"])
    scopes = set(design["models"]["external_scopes"])
    if set(predictions["scope"]) != scopes or set(metrics["scope"]) != scopes:
        raise AssertionError("External scope set changed")
    if len(predictions) != len(target_records) * len(scopes):
        raise AssertionError("External prediction row count changed")
    recomputed = []
    for scope, group in predictions.groupby("scope", sort=True):
        if group["target_row"].nunique() != len(target_records):
            raise AssertionError(f"Target rows missing for {scope}")
        if group["formula_group"].nunique() != total_groups:
            raise AssertionError(f"Target formulation groups missing for {scope}")
        recomputed.append(
            {
                "scope": scope,
                **regression_metrics(
                    group["y_log10_conductivity"].to_numpy(float),
                    group["prediction_log10_conductivity"].to_numpy(float),
                ),
            }
        )
    recomputed_frame = pd.DataFrame(recomputed)
    merged = metrics.merge(
        recomputed_frame,
        on="scope",
        suffixes=("_released", "_recomputed"),
        validate="one_to_one",
    )
    for column in (
        "log_rmse",
        "log_mae",
        "log_r2",
        "raw_rmse",
        "raw_mae",
        "raw_r2",
        "spearman",
    ):
        if not np.allclose(
            merged[f"{column}_released"],
            merged[f"{column}_recomputed"],
            rtol=1e-9,
            atol=1e-11,
            equal_nan=True,
        ):
            raise AssertionError(f"External metric mismatch: {column}")
    full = metrics.set_index("scope").loc["all_source_salts"]
    for column, value in summary["external_zero_shot"]["full_mixture"].items():
        close(float(full[column]), float(value), f"summary full {column}")

    bootstrap = pd.read_csv(paths["external_group_bootstrap"])
    repetitions = (
        100
        if summary["mode"] == "quick"
        else int(design["evaluation"]["group_bootstrap_repetitions"])
    )
    comparators = len(scopes) - 1
    if len(bootstrap) != repetitions * comparators:
        raise AssertionError("Bootstrap row count changed")
    if bootstrap.groupby("comparator")["repetition"].nunique().nunique() != 1:
        raise AssertionError("Bootstrap repetitions are incomplete")

    anchors = pd.read_csv(paths["anchor_metrics"])
    draws = (
        10
        if summary["mode"] == "quick"
        else int(design["evaluation"]["coverage_anchor_draws"])
    )
    budgets = [int(value) for value in design["evaluation"]["anchor_budgets"]]
    if len(anchors) != draws * len(budgets) * 4:
        raise AssertionError("Anchor-metric row count changed")
    for row in anchors.itertuples(index=False):
        encoded = json.loads(str(row.anchor_formula_groups))
        if len(encoded) != int(row.anchor_budget):
            raise AssertionError("Anchor formulation encoding changed")
        if len(set(encoded)) != len(encoded):
            raise AssertionError("Duplicate anchor formulation")
        if int(row.n_anchor_formulations) != int(row.anchor_budget):
            raise AssertionError("Anchor formulation count mismatch")
        if int(row.n_test_formulations) != total_groups - int(row.anchor_budget):
            raise AssertionError("Anchor formulation entered the scored target")
    primary_budget = int(design["evaluation"]["primary_anchor_budget"])
    macro = (
        anchors[anchors["anchor_budget"] == primary_budget]
        .groupby("model")[["log_rmse", "spearman", "raw_r2"]]
        .mean()
    )
    for model, values in summary["five_anchor_macro"].items():
        for metric, value in values.items():
            close(float(macro.loc[model, metric]), float(value), f"{model} {metric}")

    portfolio = pd.read_csv(paths["salt_portfolio"])
    if (portfolio.groupby("target_salt")["model"].nunique() != 2).any():
        raise AssertionError("Salt portfolio model pairs are incomplete")
    if summary["salt_exclusion_portfolio"]["targets"] != int(
        portfolio["target_salt"].nunique()
    ):
        raise AssertionError("Salt portfolio target count changed")
    print(
        json.dumps(
            {
                "status": "verified-complete-method-development",
                "mode": summary["mode"],
                "design_sha256": summary["design_sha256"],
                "external_prediction_rows": len(predictions),
                "anchor_metric_rows": len(anchors),
                "portfolio_targets": int(portfolio["target_salt"].nunique()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

