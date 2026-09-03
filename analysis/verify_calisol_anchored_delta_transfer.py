"""Independent semantic verifier for the formal E6 result package."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from common import RESULTS


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "calisol_anchored_delta_transfer_design.json"
PREFIX = "calisol_anchored_delta"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(observed: float, expected: float, label: str, atol: float = 1e-12) -> None:
    if not np.isclose(observed, expected, rtol=1e-10, atol=atol):
        raise AssertionError(f"{label}: {observed} != {expected}")


def exact_sign_flip_p(differences: np.ndarray) -> float:
    observed = float(np.mean(differences))
    exceed = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(differences)):
        value = float(np.mean(np.asarray(signs) * differences))
        exceed += int(value >= observed - 1e-15)
        total += 1
    return exceed / total


def main() -> None:
    paths = {
        "predictions": RESULTS / f"{PREFIX}_predictions.csv",
        "article_metrics": RESULTS / f"{PREFIX}_article_metrics.csv",
        "macro_metrics": RESULTS / f"{PREFIX}_macro_metrics.csv",
        "shuffled_null": RESULTS / f"{PREFIX}_shuffled_null.csv",
        "random_anchor": RESULTS / f"{PREFIX}_random_anchor_sensitivity.csv",
        "leakage": RESULTS / f"{PREFIX}_leakage_audit.csv",
        "summary": RESULTS / f"{PREFIX}_summary.json",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing E6 result files: {missing}")

    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    predictions = pd.read_csv(paths["predictions"])
    metrics = pd.read_csv(paths["article_metrics"])
    macro = pd.read_csv(paths["macro_metrics"])
    shuffled = pd.read_csv(paths["shuffled_null"])
    random_anchor = pd.read_csv(paths["random_anchor"])
    leakage = pd.read_csv(paths["leakage"])

    if summary["status"] != "complete":
        raise AssertionError("E6 result is not a formal complete run")
    if summary["design_sha256"] != sha256(DESIGN):
        raise AssertionError("E6 design hash mismatch")
    if summary["common_scope_articles"] != 11 or summary["common_scope_units"] != 883:
        raise AssertionError("E6 common scope changed")
    if predictions["is_anchor"].astype(bool).any():
        raise AssertionError("Anchor rows were scored as test observations")
    expected_rows = sum((883 - 11 * budget) * 13 for budget in (1, 2, 3))
    if len(predictions) != expected_rows:
        raise AssertionError(f"Prediction rows: {len(predictions)} != {expected_rows}")
    if len(shuffled) != int(design["inference"]["shuffled_delta_permutations"]):
        raise AssertionError("Shuffled-null count changed")
    if len(random_anchor) != (
        int(design["inference"]["random_anchor_repetitions"])
        * len(design["deployment_contract"]["anchor_budgets"])
    ):
        raise AssertionError("Random-anchor sensitivity count changed")

    for row in predictions.itertuples(index=False):
        anchors = json.loads(str(row.anchor_unit_keys))
        if len(anchors) != int(row.anchor_budget):
            raise AssertionError("Anchor-budget encoding mismatch")
        if str(row.unit_key) in anchors:
            raise AssertionError("An anchor unit appears among scored rows")

    recomputed_rows = []
    for keys, group in predictions.groupby(
        ["article_doi", "anchor_budget", "alpha", "model"], sort=True
    ):
        error = group["y"].to_numpy(float) - group["prediction"].to_numpy(float)
        recomputed_rows.append(
            {
                "article_doi": keys[0],
                "anchor_budget": keys[1],
                "alpha": keys[2],
                "model": keys[3],
                "n_nonanchor": len(group),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "mae": float(np.mean(np.abs(error))),
                "r2": float(r2_score(group["y"], group["prediction"])),
            }
        )
    recomputed = pd.DataFrame(recomputed_rows)
    merged = metrics.merge(
        recomputed,
        on=["article_doi", "anchor_budget", "alpha", "model"],
        suffixes=("_released", "_recomputed"),
        validate="one_to_one",
    )
    if len(merged) != len(metrics):
        raise AssertionError("Article-metric row mismatch")
    for column in ("rmse", "mae", "r2"):
        if not np.allclose(
            merged[f"{column}_released"],
            merged[f"{column}_recomputed"],
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        ):
            raise AssertionError(f"Article metric mismatch: {column}")

    primary = metrics[
        (metrics["anchor_budget"] == 1) & (metrics["alpha"] == 10.0)
    ].pivot(index="article_doi", columns="model", values="rmse")
    delta = primary["neighbor_delta_ridge"].to_numpy(float)
    absolute = primary["neighbor_absolute_ridge"].to_numpy(float)
    anchor = primary["anchor_constant"].to_numpy(float)
    gain_absolute = float(1.0 - delta.mean() / absolute.mean())
    gain_anchor = float(1.0 - delta.mean() / anchor.mean())
    released = summary["primary"]
    close(
        gain_absolute,
        released["relative_macro_rmse_gain_vs_neighbor_absolute"],
        "primary gain vs absolute",
    )
    close(
        gain_anchor,
        released["relative_macro_rmse_gain_vs_anchor_constant"],
        "primary gain vs anchor",
    )
    close(
        exact_sign_flip_p(absolute - delta),
        released["exact_one_sided_sign_flip_p"],
        "exact sign-flip p",
    )
    if int(np.sum(delta < absolute)) != released[
        "positive_articles_vs_neighbor_absolute"
    ]:
        raise AssertionError("Positive article count mismatch")

    selected = predictions[
        (predictions["anchor_budget"] == 1)
        & (predictions["alpha"] == 10.0)
        & (predictions["model"] == "neighbor_delta_ridge")
    ]
    close(
        float(r2_score(selected["y"], selected["prediction"])),
        released["pooled_nonanchor_r2"],
        "pooled R2",
    )
    shuffled_p = float(
        (
            1
            + (
                shuffled["relative_gain_vs_neighbor_absolute"]
                >= released["relative_macro_rmse_gain_vs_neighbor_absolute"]
            ).sum()
        )
        / (1 + len(shuffled))
    )
    close(
        shuffled_p,
        released["shuffled_delta_permutation_p"],
        "shuffled permutation p",
    )

    post_columns = [
        "neighbor_postexclusion_exact_test_chemistry_rows",
        "neighbor_postexclusion_heldout_article_rows",
        "wrong_postexclusion_exact_test_chemistry_rows",
        "wrong_postexclusion_heldout_article_rows",
    ]
    if any((leakage[column] != 0).any() for column in post_columns):
        raise AssertionError("Residual E6 source leakage")

    gate_spec = design["success_gate"]
    gates = {
        "gain_vs_absolute_at_least_5pct": gain_absolute
        >= gate_spec["minimum_relative_macro_rmse_gain_vs_absolute_neighbor"],
        "article_bootstrap_ci_lower_above_zero": released[
            "article_bootstrap_ci95"
        ][0]
        > 0,
        "exact_sign_flip_p_at_most_0_05": released[
            "exact_one_sided_sign_flip_p"
        ]
        <= gate_spec["exact_one_sided_sign_flip_p_at_most"],
        "positive_articles_at_least_8_of_11": released[
            "positive_articles_vs_neighbor_absolute"
        ]
        >= gate_spec["minimum_positive_articles_of_11"],
        "pooled_nonanchor_r2_positive": released["pooled_nonanchor_r2"] > 0,
        "gain_vs_anchor_constant_at_least_5pct": gain_anchor
        >= gate_spec["minimum_relative_macro_rmse_gain_vs_anchor_constant"],
        "advantage_over_median_shuffled_at_least_3pp": released[
            "gain_advantage_over_median_shuffled"
        ]
        >= gate_spec["minimum_gain_advantage_over_median_shuffled_delta"],
        "shuffled_permutation_p_at_most_0_05": shuffled_p
        <= gate_spec["shuffled_delta_permutation_p_at_most"],
        "zero_article_or_chemistry_leakage": True,
    }
    if gates != summary["gates"]:
        raise AssertionError("Released E6 gates do not match independent recomputation")
    expected_decision = (
        "mechanistic-rescue"
        if all(gates.values())
        else (
            "contrast-transfer-harmful"
            if gain_absolute < 0
            else "contrast-transfer-unresolved"
        )
    )
    if summary["decision"] != expected_decision:
        raise AssertionError("E6 decision mismatch")

    verification = {
        "status": "verified-complete",
        "design_sha256": sha256(DESIGN),
        "summary_sha256": sha256(paths["summary"]),
        "prediction_rows": len(predictions),
        "article_metric_rows": len(metrics),
        "shuffled_null_rows": len(shuffled),
        "random_anchor_rows": len(random_anchor),
        "primary_gain": gain_absolute,
        "decision": expected_decision,
        "file_sha256": {name: sha256(path) for name, path in paths.items()},
    }
    (RESULTS / f"{PREFIX}_verified.json").write_text(
        json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
