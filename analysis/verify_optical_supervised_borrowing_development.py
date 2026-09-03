"""Independently verify focused optical borrowing development results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
SCOPE_PATH = HERE / "results" / "optical_supervised_borrowing_scopes.csv"
SCOPE_MANIFEST_PATH = (
    HERE / "results" / "optical_supervised_borrowing_scopes_manifest.json"
)
SOURCE_VERIFIED_PATH = (
    HERE / "results" / "optical_supervised_source_VERIFIED.json"
)
METRICS_PATH = (
    HERE / "results" / "optical_supervised_borrowing_metrics.csv"
)
CONTRAST_PATH = (
    HERE / "results" / "optical_supervised_borrowing_contrasts.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_supervised_borrowing_summary.json"
)
RELEASE_PATH = (
    HERE / "results" / "optical_supervised_borrowing_release.json"
)
VERIFIED_PATH = (
    HERE / "results" / "optical_supervised_borrowing_VERIFIED.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return bool(
        np.isclose(left, right, atol=tolerance, rtol=tolerance)
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    scope_manifest = json.loads(
        SCOPE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    source_verified = json.loads(
        SOURCE_VERIFIED_PATH.read_text(encoding="utf-8")
    )
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    release = json.loads(RELEASE_PATH.read_text(encoding="utf-8"))
    if scope_manifest["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise AssertionError("OOD scopes predate focused config")
    if scope_manifest["scope_sha256"] != sha256(SCOPE_PATH):
        raise AssertionError("OOD scope hash mismatch")
    if source_verified["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise AssertionError("Source verification predates focused config")
    if summary["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise AssertionError("Development summary predates focused config")
    if summary["metrics_sha256"] != sha256(METRICS_PATH):
        raise AssertionError("Development metric hash mismatch")
    if summary["contrasts_sha256"] != sha256(CONTRAST_PATH):
        raise AssertionError("Development contrast hash mismatch")
    if release["development_summary_sha256"] != sha256(SUMMARY_PATH):
        raise AssertionError("Release summary hash mismatch")
    if bool(release["blind_outcomes_opened"]):
        raise AssertionError("Blind outcomes were marked opened")

    metrics = pd.read_csv(METRICS_PATH)
    contrasts = pd.read_csv(CONTRAST_PATH)
    scopes = pd.read_csv(SCOPE_PATH)
    methods = [item["name"] for item in config["methods"]]
    budgets = [int(value) for value in config["development"]["label_budgets"]]
    repeats = int(config["development"]["draws_per_budget"])
    expected_metric_rows = len(methods) * len(budgets) * repeats * 2
    if len(metrics) != expected_metric_rows:
        raise AssertionError("Development metric row count mismatch")
    if len(contrasts) != (len(methods) - 1) * len(budgets) * repeats * 2:
        raise AssertionError("Development contrast row count mismatch")
    if set(metrics["method"]) != set(methods):
        raise AssertionError("Development method registry drift")
    if set(metrics["scope"]) != {
        "dynamic_hard_ood_40pct",
        "full_scaffold_separated_evaluation",
    }:
        raise AssertionError("Development scope registry drift")
    required_metric_columns = {
        "training_scaffolds",
        "insufficient_scaffold_abstention",
        "selected_correction_weight",
        "mean_absolute_correction",
    }
    if not required_metric_columns.issubset(metrics.columns):
        raise AssertionError("Development scaffold-abstention audit is missing")
    if not np.isfinite(metrics[["rmse", "mae", "r2"]]).all().all():
        raise AssertionError("Nonfinite primary development metric")

    stored_abstention = (
        metrics["insufficient_scaffold_abstention"]
        .astype(str)
        .str.lower()
        .map({"true": True, "false": False})
    )
    if stored_abstention.isna().any():
        raise AssertionError("Invalid scaffold-abstention flag")
    expected_abstention = metrics["training_scaffolds"].astype(int) < 3
    if not np.array_equal(
        stored_abstention.to_numpy(bool),
        expected_abstention.to_numpy(bool),
    ):
        raise AssertionError("Scaffold-abstention rule mismatch")
    draw_audit = metrics[
        [
            "budget",
            "repeat",
            "training_scaffolds",
            "insufficient_scaffold_abstention",
        ]
    ].drop_duplicates()
    expected_draws = len(budgets) * repeats
    if len(draw_audit) != expected_draws:
        raise AssertionError("Draw-level scaffold audit is not unique")
    draw_abstention = (
        draw_audit["insufficient_scaffold_abstention"]
        .astype(str)
        .str.lower()
        .eq("true")
    )
    abstention_draws = int(draw_abstention.sum())
    if (
        abstention_draws
        != int(summary["insufficient_scaffold_abstention_draws"])
    ):
        raise AssertionError("Scaffold-abstention draw count mismatch")
    by_budget = (
        draw_audit[draw_abstention]
        .groupby("budget")
        .size()
        .reindex(budgets, fill_value=0)
    )
    expected_by_budget = {
        str(int(budget)): int(count)
        for budget, count in by_budget.items()
    }
    if (
        summary["insufficient_scaffold_abstention_draws_by_budget"]
        != expected_by_budget
    ):
        raise AssertionError("Scaffold-abstention budget count mismatch")

    baseline = metrics[
        metrics["method"] == "target_only_hurdle"
    ][["budget", "repeat", "scope", "rmse"]].rename(
        columns={"rmse": "expected_target_only_rmse"}
    )
    recomputed = contrasts.merge(
        baseline, on=["budget", "repeat", "scope"], how="left"
    )
    expected_gain = (
        recomputed["expected_target_only_rmse"] - recomputed["rmse"]
    ) / recomputed["expected_target_only_rmse"]
    if not np.allclose(
        recomputed["target_only_rmse"],
        recomputed["expected_target_only_rmse"],
        atol=1e-12,
        rtol=1e-12,
    ):
        raise AssertionError("Stored target-only RMSE mismatch")
    if not np.allclose(
        recomputed["relative_rmse_gain"],
        expected_gain,
        atol=1e-12,
        rtol=1e-12,
    ):
        raise AssertionError("Relative RMSE gain mismatch")

    hard_counts = (
        scopes.groupby(["budget", "repeat"])[
            "dynamic_hard_ood_40pct"
        ]
        .sum()
        .astype(int)
    )
    metric_hard_counts = (
        metrics[
            (metrics["method"] == "target_only_hurdle")
            & (metrics["scope"] == "dynamic_hard_ood_40pct")
        ]
        .set_index(["budget", "repeat"])["evaluation_rows"]
        .astype(int)
    )
    if not hard_counts.sort_index().equals(metric_hard_counts.sort_index()):
        raise AssertionError("Dynamic hard-OOD evaluation count mismatch")

    adapters = metrics[
        metrics["method"].str.endswith("_residual")
    ]
    if adapters["selected_correction_weight"].isna().any():
        raise AssertionError("Adapter correction weight is missing")
    allowed_weights = {
        float(value)
        for value in config["target_adapter"]["correction_weights"]
    }
    if not set(adapters["selected_correction_weight"]).issubset(
        allowed_weights
    ):
        raise AssertionError("Undeclared adapter correction weight")
    baselines = metrics[
        metrics["method"].isin(
            ["target_only_hurdle", "target_only_direct_regression"]
        )
    ]
    if baselines["selected_correction_weight"].notna().any():
        raise AssertionError("Target-only model has a donor correction")

    abstaining_adapters = adapters[
        adapters["insufficient_scaffold_abstention"]
        .astype(str)
        .str.lower()
        .eq("true")
    ]
    if not np.array_equal(
        abstaining_adapters["selected_correction_weight"].to_numpy(float),
        np.zeros(len(abstaining_adapters)),
    ):
        raise AssertionError("Abstaining adapter has a nonzero correction weight")
    if not np.array_equal(
        abstaining_adapters["mean_absolute_correction"].to_numpy(float),
        np.zeros(len(abstaining_adapters)),
    ):
        raise AssertionError("Abstaining adapter changed a target prediction")
    abstention_baseline = metrics[
        (metrics["method"] == "target_only_hurdle")
        & metrics["insufficient_scaffold_abstention"]
        .astype(str)
        .str.lower()
        .eq("true")
    ][
        ["budget", "repeat", "scope", "rmse", "mae", "r2", "spearman"]
    ].rename(
        columns={
            "rmse": "baseline_rmse",
            "mae": "baseline_mae",
            "r2": "baseline_r2",
            "spearman": "baseline_spearman",
        }
    )
    abstention_comparison = abstaining_adapters.merge(
        abstention_baseline,
        on=["budget", "repeat", "scope"],
        how="left",
        validate="many_to_one",
    )
    for metric in ["rmse", "mae", "r2", "spearman"]:
        if not np.allclose(
            abstention_comparison[metric],
            abstention_comparison[f"baseline_{metric}"],
            atol=0.0,
            rtol=0.0,
            equal_nan=True,
        ):
            raise AssertionError(
                f"Abstaining adapter differs from target-only {metric}"
            )

    primary_method = config["development_release_gate"]["primary_method"]
    primary_budget = int(config["development"]["primary_budget"])
    primary_scope = config["development"]["primary_scope"]
    subset = contrasts[
        (contrasts["method"] == primary_method)
        & (contrasts["budget"] == primary_budget)
        & (contrasts["scope"] == primary_scope)
    ]
    mean_gain = float(subset["relative_rmse_gain"].mean())
    positive_fraction = float((subset["relative_rmse_gain"] > 0).mean())
    nonzero_fraction = float(
        (subset["selected_correction_weight"] > 0).mean()
    )
    if not close(mean_gain, summary["primary_mean_relative_rmse_gain"]):
        raise AssertionError("Primary mean gain mismatch")
    if not close(
        positive_fraction, summary["primary_positive_draw_fraction"]
    ):
        raise AssertionError("Primary positive fraction mismatch")
    if not close(
        nonzero_fraction,
        summary["primary_nonzero_correction_fraction"],
    ):
        raise AssertionError("Primary nonzero correction fraction mismatch")
    admitted = bool(summary["admitted_to_blind"])
    if admitted != all(bool(value) for value in summary["gate_checks"].values()):
        raise AssertionError("Development release decision mismatch")
    expected_release_status = (
        "blind-release-candidate" if admitted else "blind-release-denied"
    )
    if release["status"] != expected_release_status:
        raise AssertionError("Release status mismatch")
    if admitted and release["selected_method"] != primary_method:
        raise AssertionError("Released method mismatch")
    if not admitted and release["selected_method"] is not None:
        raise AssertionError("A method was released after abstention")

    script_text = (
        HERE / "run_optical_supervised_borrowing_development.py"
    ).read_text(encoding="utf-8")
    if "SC-012-D1SC02150H-s006.csv" in script_text:
        raise AssertionError("Blind target path appears in development code")
    verified = {
        "status": "verified-complete-focused-development",
        "focused_config_sha256": sha256(CONFIG_PATH),
        "source_verified_sha256": sha256(SOURCE_VERIFIED_PATH),
        "scope_manifest_sha256": sha256(SCOPE_MANIFEST_PATH),
        "development_summary_sha256": sha256(SUMMARY_PATH),
        "development_release_sha256": sha256(RELEASE_PATH),
        "metric_rows": int(len(metrics)),
        "contrast_rows": int(len(contrasts)),
        "insufficient_scaffold_abstention_draws": abstention_draws,
        "admitted_to_blind": admitted,
        "selected_method": release["selected_method"],
        "claim_guard": config["claim_guard"],
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
