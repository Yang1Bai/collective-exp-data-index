"""Independently verify the formal cross-database electrolyte benchmark."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error, r2_score

from common import RESULTS
from electrolyte_programme_interaction_common import (
    exact_formulation_signature,
    general_record_overlap_count,
    load_bamboo,
    load_calisol_subset,
    load_finales,
    load_kit,
    load_solventseg,
    percentile_rank,
    sha256,
    source_contains_target_family,
)
from mixture_response_transfer_common import stable_seed


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN = HERE / "bamboomixer_cross_database_interaction_design.json"
PREFIX = "bamboomixer_cross_database_interaction"
VERIFICATION = RESULTS / f"{PREFIX}_verification.json"


def result_path(suffix: str) -> Path:
    return RESULTS / f"{PREFIX}_{suffix}"


def resolve(raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def close(
    observed: float,
    expected: float,
    *,
    label: str,
    atol: float = 1e-12,
) -> None:
    if np.isnan(observed) and np.isnan(expected):
        return
    if not np.isclose(observed, expected, rtol=1e-10, atol=atol):
        raise AssertionError(f"{label}: {observed} != {expected}")


def rank_metrics(
    truth: Sequence[float],
    score: Sequence[float],
) -> dict[str, float]:
    truth = np.asarray(truth, dtype=float)
    score = np.asarray(score, dtype=float)
    if (
        len(truth) < 2
        or np.std(truth) <= 1e-15
        or np.std(score) <= 1e-15
    ):
        return {
            "spearman": float("nan"),
            "top_quartile_precision": float("nan"),
            "normalized_regret": float("nan"),
        }
    rho = float(stats.spearmanr(truth, score).statistic)
    k = max(1, int(math.ceil(0.25 * len(truth))))
    true_top = set(np.argsort(truth, kind="stable")[-k:])
    score_top = set(np.argsort(score, kind="stable")[-k:])
    precision = len(true_top.intersection(score_top)) / k
    selected = int(np.argmax(score))
    span = float(np.max(truth) - np.min(truth))
    regret = 0.0 if span <= 1e-15 else float(
        (np.max(truth) - truth[selected]) / span
    )
    return {
        "spearman": rho,
        "top_quartile_precision": float(precision),
        "normalized_regret": regret,
    }


def regression_metrics(
    truth_log: Sequence[float],
    prediction_log: Sequence[float],
) -> dict[str, float]:
    truth_log = np.asarray(truth_log, dtype=float)
    prediction_log = np.asarray(prediction_log, dtype=float)
    truth_raw = 10.0**truth_log
    prediction_raw = 10.0**prediction_log
    return {
        "n": len(truth_log),
        "log_rmse": float(
            np.sqrt(mean_squared_error(truth_log, prediction_log))
        ),
        "log_r2": float(r2_score(truth_log, prediction_log)),
        "raw_rmse": float(
            np.sqrt(mean_squared_error(truth_raw, prediction_raw))
        ),
        "raw_r2": float(r2_score(truth_raw, prediction_raw)),
        **rank_metrics(truth_log, prediction_log),
    }


def pairwise_concordance(
    frame: pd.DataFrame,
    score: np.ndarray,
    tolerance: float = 2.0,
) -> tuple[float, int]:
    truth = frame["conductivity"].to_numpy(float)
    temperature = frame["temperature_C"].to_numpy(float)
    values = []
    for left in range(len(frame)):
        for right in range(left + 1, len(frame)):
            if abs(temperature[left] - temperature[right]) > tolerance:
                continue
            truth_delta = truth[left] - truth[right]
            score_delta = score[left] - score[right]
            if abs(truth_delta) <= 1e-15:
                continue
            values.append(
                0.5
                if abs(score_delta) <= 1e-15
                else float(np.sign(truth_delta) == np.sign(score_delta))
            )
    return (
        (float(np.mean(values)), len(values))
        if values
        else (float("nan"), 0)
    )


def verify_inputs(design: dict) -> dict:
    resolved = {
        name: resolve(spec["path"])
        for name, spec in design["inputs"].items()
        if "path" in spec
    }
    for name, path in resolved.items():
        expected = design["inputs"][name]["sha256"]
        if sha256(path) != expected:
            raise AssertionError(f"Input hash mismatch: {name}")
    bamboo = load_bamboo(resolved["bamboomixer"])
    solvent, solvent_frame = load_solventseg(resolved["solventseg"])
    calisol, calisol_frame = load_calisol_subset(resolved["calisol_subset"])
    kit, kit_frame = load_kit(resolved["kit"])
    finales, _ = load_finales(
        [resolved["finales_primary"], resolved["finales_secondary"]]
    )
    family = [row for row in bamboo if source_contains_target_family(row)]
    nonfamily = [
        row for row in bamboo if not source_contains_target_family(row)
    ]
    observed = {
        "bamboo_rows": len(bamboo),
        "bamboo_target_family_rows": len(family),
        "bamboo_without_target_family_rows": len(nonfamily),
        "calisol_rows": len(calisol),
        "calisol_articles": int(calisol_frame["source_doi"].nunique()),
        "kit_raw_rows": int(design["inputs"]["kit"]["raw_rows"]),
        "kit_aggregated_rows": len(kit),
        "kit_formulations": int(kit_frame["formula_key"].nunique()),
        "solventseg_rows": len(solvent),
        "solventseg_formulations": len(
            {exact_formulation_signature(row) for row in solvent}
        ),
        "finales_rows": len(finales),
    }
    expected_counts = {
        "bamboo_rows": 10407,
        "bamboo_target_family_rows": 395,
        "bamboo_without_target_family_rows": 10012,
        "calisol_rows": 410,
        "calisol_articles": 3,
        "kit_raw_rows": 5035,
        "kit_aggregated_rows": 1089,
        "kit_formulations": 109,
        "solventseg_rows": 180,
        "solventseg_formulations": 36,
        "finales_rows": 29,
    }
    if observed != expected_counts:
        raise AssertionError(f"Input counts changed: {observed}")
    overlap_kwargs = {
        "composition_tolerance": 1e-4,
        "temperature_tolerance": 0.05,
        "outcome_tolerance": 0.01,
    }
    overlaps = {
        "bamboo_to_calisol": general_record_overlap_count(
            bamboo, calisol, **overlap_kwargs
        ),
        "bamboo_to_kit": general_record_overlap_count(
            bamboo, kit, **overlap_kwargs
        ),
        "bamboo_to_solventseg": general_record_overlap_count(
            bamboo, solvent, **overlap_kwargs
        ),
        "calisol_to_kit": general_record_overlap_count(
            calisol, kit, **overlap_kwargs
        ),
        "calisol_to_solventseg": general_record_overlap_count(
            calisol, solvent, **overlap_kwargs
        ),
        "kit_to_solventseg": general_record_overlap_count(
            kit, solvent, **overlap_kwargs
        ),
    }
    if overlaps != {
        "bamboo_to_calisol": 71,
        "bamboo_to_kit": 0,
        "bamboo_to_solventseg": 0,
        "calisol_to_kit": 0,
        "calisol_to_solventseg": 0,
        "kit_to_solventseg": 0,
    }:
        raise AssertionError(f"Overlap audit changed: {overlaps}")
    return {**observed, "strict_record_overlap_counts": overlaps}


def verify_portfolios(frame: pd.DataFrame) -> None:
    members = [
        "prediction_bamboo_without_target_family",
        "prediction_calisol",
        "prediction_kit",
    ]
    expected = frame[members].mean(axis=1).to_numpy(float)
    observed = frame[
        "prediction_programme_balanced_portfolio"
    ].to_numpy(float)
    if not np.allclose(expected, observed, rtol=1e-12, atol=1e-12):
        raise AssertionError("Programme-balanced mean changed")
    expected_rank = np.round(
        np.mean(
            np.vstack(
                [
                    percentile_rank(frame[column].to_numpy(float))
                    for column in members
                ]
            ),
            axis=0,
        ),
        decimals=12,
    )
    observed_rank = frame[
        "prediction_programme_balanced_rank_consensus"
    ].to_numpy(float)
    if not np.allclose(expected_rank, observed_rank, rtol=1e-12, atol=1e-12):
        raise AssertionError("Programme-balanced rank consensus changed")


def verify_solventseg() -> dict:
    predictions = pd.read_csv(result_path("solventseg_predictions.csv"))
    metrics = pd.read_csv(result_path("solventseg_metrics.csv"))
    bootstrap = pd.read_csv(result_path("solventseg_bootstrap.csv"))
    rank_table = pd.read_csv(
        result_path("solventseg_rank_permutation.csv")
    )
    anchor_metrics = pd.read_csv(
        result_path("solventseg_anchor_metrics.csv")
    )
    anchor_contrasts = pd.read_csv(
        result_path("solventseg_anchor_contrasts.csv")
    )
    if len(predictions) != 180 or len(metrics) != 72:
        raise AssertionError("SolventSeg result row count changed")
    verify_portfolios(predictions)
    truth = np.log10(predictions["conductivity_mS_cm"].to_numpy(float))
    if not np.allclose(
        truth,
        predictions["truth_log10"].to_numpy(float),
        rtol=1e-12,
        atol=1e-12,
    ):
        raise AssertionError("SolventSeg truth transform changed")
    scopes = {
        "all_180_rows": np.arange(len(predictions)),
        "fixed_25_C": np.flatnonzero(
            np.isclose(predictions["temperature_C"].to_numpy(float), 25.0)
        ),
    }
    models = [
        column.removeprefix("prediction_")
        for column in predictions.columns
        if column.startswith("prediction_")
    ]
    for scope, indices in scopes.items():
        for model in models:
            row = metrics[
                metrics["scope"].eq(scope) & metrics["model"].eq(model)
            ].iloc[0]
            score = predictions[f"prediction_{model}"].to_numpy(float)[indices]
            rank = rank_metrics(truth[indices], score)
            for key, value in rank.items():
                close(
                    value,
                    float(row[key]),
                    label=f"{scope}/{model}/{key}",
                    atol=(
                        5e-4
                        if key == "spearman"
                        and model == "programme_balanced_rank_consensus"
                        else 1e-4
                        if key == "spearman"
                        else 1e-12
                    ),
                )
            if model != "programme_balanced_rank_consensus":
                absolute = regression_metrics(truth[indices], score)
                for key in ("n", "log_rmse", "log_r2", "raw_rmse", "raw_r2"):
                    close(
                        float(absolute[key]),
                        float(row[key]),
                        label=f"{scope}/{model}/{key}",
                    )
            elif row[
                ["log_rmse", "log_r2", "raw_rmse", "raw_r2"]
            ].notna().any():
                raise AssertionError("Rank score was treated as an absolute response")
    if len(bootstrap) != 9 * 5000:
        raise AssertionError("Formulation bootstrap is incomplete")
    if not (
        bootstrap.groupby(["model", "comparator"]).size() == 5000
    ).all():
        raise AssertionError("Bootstrap contrast family is incomplete")
    if len(anchor_metrics) != 3 * 100 * 11:
        raise AssertionError("Anchor metric table is incomplete")
    if len(anchor_contrasts) != 3 * 100 * 5:
        raise AssertionError("Anchor contrast table is incomplete")
    for row in anchor_contrasts.itertuples(index=False):
        first = anchor_metrics[
            anchor_metrics["anchor_budget"].eq(row.anchor_budget)
            & anchor_metrics["draw"].eq(row.draw)
            & anchor_metrics["model"].eq(row.model)
        ].iloc[0]
        second = anchor_metrics[
            anchor_metrics["anchor_budget"].eq(row.anchor_budget)
            & anchor_metrics["draw"].eq(row.draw)
            & anchor_metrics["model"].eq(row.comparator)
        ].iloc[0]
        close(
            float(first["spearman"] - second["spearman"]),
            float(row.spearman_gain),
            label="Anchor Spearman contrast",
        )
        close(
            float(
                first["top_quartile_precision"]
                - second["top_quartile_precision"]
            ),
            float(row.top_quartile_precision_gain),
            label="Anchor precision contrast",
        )
        close(
            float(
                second["normalized_regret"] - first["normalized_regret"]
            ),
            float(row.normalized_regret_reduction),
            label="Anchor regret contrast",
        )
        if np.isfinite(row.relative_log_rmse_gain):
            close(
                float(1.0 - first["log_rmse"] / second["log_rmse"]),
                float(row.relative_log_rmse_gain),
                label="Anchor RMSE contrast",
            )
    fixed = scopes["fixed_25_C"]
    rng = np.random.default_rng(
        stable_seed("solventseg-fixed25-permutation")
    )
    declared = rank_table["model"].tolist()
    observed = {
        model: float(
            stats.spearmanr(
                truth[fixed],
                predictions[f"prediction_{model}"].to_numpy(float)[fixed],
            ).statistic
        )
        for model in declared
    }
    exceed = {model: 0 for model in declared}
    for _ in range(10000):
        permuted = rng.permutation(truth[fixed])
        for model in declared:
            score = predictions[
                f"prediction_{model}"
            ].to_numpy(float)[fixed]
            value = float(stats.spearmanr(permuted, score).statistic)
            exceed[model] += int(value >= observed[model] - 1e-15)
    raw_p = {
        model: (exceed[model] + 1) / 10001
        for model in declared
    }
    ordered = sorted(raw_p, key=raw_p.get)
    adjusted = {}
    running = 0.0
    for rank, model in enumerate(ordered):
        running = max(
            running,
            min(1.0, raw_p[model] * (len(ordered) - rank)),
        )
        adjusted[model] = running
    for row in rank_table.itertuples(index=False):
        close(
            observed[row.model],
            row.observed_spearman,
            label="Observed rank",
            atol=(
                5e-4
                if row.model == "programme_balanced_rank_consensus"
                else 1e-4
            ),
        )
        close(raw_p[row.model], row.one_sided_p, label="Permutation p")
        close(adjusted[row.model], row.holm_p, label="Holm p")
    return {
        "predictions": len(predictions),
        "metrics": len(metrics),
        "bootstrap_rows": len(bootstrap),
        "anchor_metric_rows": len(anchor_metrics),
        "anchor_contrast_rows": len(anchor_contrasts),
        "rank_permutations_per_model": 10000,
    }


def verify_finales() -> dict:
    predictions = pd.read_csv(result_path("finales_predictions.csv"))
    metrics = pd.read_csv(result_path("finales_metrics.csv"))
    if len(predictions) != 29 or len(metrics) != 40:
        raise AssertionError("FINALES result row count changed")
    verify_portfolios(predictions)
    for row in metrics.itertuples(index=False):
        phase, _, *tail = row.scope.split("|")
        mask = (
            predictions["phase"].eq(phase)
            & predictions["split"].eq("evaluation")
        )
        if tail:
            mask &= predictions["hard_ood_40pct"].astype(bool)
        selected = predictions.loc[mask].reset_index(drop=True)
        if row.model in {
            "target_extra_trees",
            "target_hist_gradient_boosting",
            "target_linear",
        }:
            score = selected[row.model].to_numpy(float)
        else:
            score = selected[
                f"prediction_{row.model}"
            ].to_numpy(float)
        truth = np.log10(selected["conductivity"].to_numpy(float))
        recalculated = rank_metrics(truth, score)
        concordance, pairs = pairwise_concordance(selected, score)
        close(concordance, row.pairwise_concordance, label="FINALES concordance")
        if pairs != row.temperature_matched_pairs:
            raise AssertionError("FINALES pair count changed")
        for key, value in recalculated.items():
            close(
                value,
                getattr(row, key),
                label=f"FINALES {key}",
                atol=1e-4 if key == "spearman" else 1e-12,
            )
    return {"predictions": len(predictions), "metric_rows": len(metrics)}


def main() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    if design["status"] != "frozen-post-outcome-cross-database-method-development":
        raise AssertionError("Design is not frozen")
    summary_path = result_path("summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary["mode"] != "formal":
        raise AssertionError("Only the formal result may be verified")
    if summary["design_sha256"] != sha256(DESIGN):
        raise AssertionError("Summary design hash mismatch")
    inputs = verify_inputs(design)
    stored_audit = json.loads(
        result_path("input_audit.json").read_text(encoding="utf-8")
    )
    for key, value in inputs.items():
        if stored_audit[key] != value:
            raise AssertionError(f"Stored input audit mismatch: {key}")
    seed_audit = pd.read_csv(result_path("seed_audit.csv"))
    if len(seed_audit) != 7 * 3 * 2:
        raise AssertionError("Seed audit is incomplete")
    if set(seed_audit["seed"]) != set(
        design["models"]["source_model"]["seeds"]
    ):
        raise AssertionError("Formal source seeds changed")
    solvent = verify_solventseg()
    finales = verify_finales()
    if summary["solventseg"]["routing"]["decision"] not in {
        "prediction",
        "ranking",
        "abstain",
    }:
        raise AssertionError("Invalid routing decision")
    files = {
        path.name: sha256(path)
        for path in sorted(RESULTS.glob(f"{PREFIX}_*"))
        if path != VERIFICATION
    }
    verification = {
        "status": "verified-complete",
        "verification_mode": "independent-recalculation",
        "design_sha256": sha256(DESIGN),
        "summary_sha256": sha256(summary_path),
        "input_audit": inputs,
        "seed_audit_rows": len(seed_audit),
        "solventseg": solvent,
        "finales": finales,
        "routing_decision": summary["solventseg"]["routing"]["decision"],
        "result_sha256": files,
        "claim_guard": design["claim_guard"],
    }
    VERIFICATION.write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
