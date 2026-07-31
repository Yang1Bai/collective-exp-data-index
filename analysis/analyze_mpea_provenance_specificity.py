"""Elemental-system inference for the MPEA strengthening experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from common import RESULTS


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "mpea_provenance_specificity_design.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-path", type=Path, default=DESIGN_PATH)
    parser.add_argument("--output-prefix", default="mpea_provenance_specificity")
    parser.add_argument("--bootstrap-replicates", type=int)
    parser.add_argument("--signflip-replicates", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def interval(values: np.ndarray) -> list[float]:
    return [
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    ]


def aggregate(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    local = frame if scope == "all" else frame[frame["scope"].eq(scope)]
    if local.empty:
        raise RuntimeError(f"No rows for scope {scope}")
    work = local[["group", "observed", "baseline", "real_augmented", "shuffled_augmented"]].copy()
    work["base_se"] = (work["observed"] - work["baseline"]) ** 2
    work["real_se"] = (work["observed"] - work["real_augmented"]) ** 2
    work["shuffled_se"] = (work["observed"] - work["shuffled_augmented"]) ** 2
    work["y"] = work["observed"]
    work["y2"] = work["observed"] ** 2
    return (
        work.groupby("group", as_index=False)
        .agg(
            n=("observed", "size"),
            base_sse=("base_se", "sum"),
            real_sse=("real_se", "sum"),
            shuffled_sse=("shuffled_se", "sum"),
            y_sum=("y", "sum"),
            y2_sum=("y2", "sum"),
        )
        .sort_values("group", kind="mergesort")
        .reset_index(drop=True)
    )


def metrics_from_totals(
    n: np.ndarray,
    base_sse: np.ndarray,
    augmented_sse: np.ndarray,
    y_sum: np.ndarray,
    y2_sum: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    base_rmse = np.sqrt(base_sse / n)
    aug_rmse = np.sqrt(augmented_sse / n)
    gain = (base_rmse - aug_rmse) / base_rmse
    tss = y2_sum - np.square(y_sum) / n
    r2 = 1.0 - augmented_sse / tss
    return gain, r2


def condition_inference(
    frame: pd.DataFrame,
    scope: str,
    replicates: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    grouped = aggregate(frame, scope)
    arrays = {
        column: grouped[column].to_numpy(float)
        for column in (
            "n",
            "base_sse",
            "real_sse",
            "shuffled_sse",
            "y_sum",
            "y2_sum",
        )
    }
    total = {key: np.asarray([value.sum()]) for key, value in arrays.items()}
    real_gain, real_r2 = metrics_from_totals(
        total["n"],
        total["base_sse"],
        total["real_sse"],
        total["y_sum"],
        total["y2_sum"],
    )
    shuffled_gain, shuffled_r2 = metrics_from_totals(
        total["n"],
        total["base_sse"],
        total["shuffled_sse"],
        total["y_sum"],
        total["y2_sum"],
    )
    bootstrap = {
        "real_gain": np.empty(replicates),
        "real_r2": np.empty(replicates),
        "shuffled_gain": np.empty(replicates),
        "real_minus_shuffled_gain": np.empty(replicates),
    }
    groups = len(grouped)
    probability = np.full(groups, 1.0 / groups)
    batch = 1000
    for start in range(0, replicates, batch):
        stop = min(replicates, start + batch)
        weights = rng.multinomial(groups, probability, size=stop - start).astype(float)
        totals = {key: weights @ value for key, value in arrays.items()}
        boot_real_gain, boot_real_r2 = metrics_from_totals(
            totals["n"],
            totals["base_sse"],
            totals["real_sse"],
            totals["y_sum"],
            totals["y2_sum"],
        )
        boot_shuffled_gain, _ = metrics_from_totals(
            totals["n"],
            totals["base_sse"],
            totals["shuffled_sse"],
            totals["y_sum"],
            totals["y2_sum"],
        )
        bootstrap["real_gain"][start:stop] = boot_real_gain
        bootstrap["real_r2"][start:stop] = boot_real_r2
        bootstrap["shuffled_gain"][start:stop] = boot_shuffled_gain
        bootstrap["real_minus_shuffled_gain"][start:stop] = (
            boot_real_gain - boot_shuffled_gain
        )
    q4_counts = None
    if scope == "q4":
        q4_counts = (
            frame[frame["scope"].eq("q4")]
            .groupby(["repeat", "learner"])["group"]
            .nunique()
            .astype(int)
        )
    return {
        "scope": scope,
        "evaluation_systems": int(groups),
        "prediction_rows": int(arrays["n"].sum()),
        "observed": {
            "real_relative_rmse_gain": float(real_gain[0]),
            "real_augmented_r2": float(real_r2[0]),
            "shuffled_relative_rmse_gain": float(shuffled_gain[0]),
            "shuffled_augmented_r2": float(shuffled_r2[0]),
            "real_minus_shuffled_gain": float(real_gain[0] - shuffled_gain[0]),
            "base_rmse": float(
                math.sqrt(total["base_sse"][0] / total["n"][0])
            ),
            "real_augmented_rmse": float(
                math.sqrt(total["real_sse"][0] / total["n"][0])
            ),
            "shuffled_augmented_rmse": float(
                math.sqrt(total["shuffled_sse"][0] / total["n"][0])
            ),
        },
        "cluster_ci95": {
            key: interval(value) for key, value in bootstrap.items()
        },
        "q4_systems_per_model_draw": (
            {
                "min": int(q4_counts.min()),
                "median": float(q4_counts.median()),
                "max": int(q4_counts.max()),
                "unique_union": int(
                    frame.loc[frame["scope"].eq("q4"), "group"].nunique()
                ),
            }
            if q4_counts is not None
            else None
        ),
    }


def cluster_loss_difference(
    first: pd.DataFrame,
    first_column: str,
    second: pd.DataFrame,
    second_column: str,
    scope: str,
) -> pd.Series:
    keys = ["repeat", "learner", "raw_row_id", "group"]
    columns = [*keys, "scope", "observed", first_column]
    left = first[columns].rename(
        columns={"scope": "scope_first", "observed": "observed_first", first_column: "first"}
    )
    right = second[[*keys, "scope", "observed", second_column]].rename(
        columns={
            "scope": "scope_second",
            "observed": "observed_second",
            second_column: "second",
        }
    )
    merged = left.merge(right, on=keys, validate="one_to_one")
    if not np.allclose(merged["observed_first"], merged["observed_second"]):
        raise AssertionError("Primary contrast outcomes are not aligned")
    if scope != "all":
        merged = merged[
            merged["scope_first"].eq(scope) & merged["scope_second"].eq(scope)
        ]
    merged["loss_reduction"] = (
        (merged["observed_first"] - merged["second"]) ** 2
        - (merged["observed_first"] - merged["first"]) ** 2
    )
    return merged.groupby("group")["loss_reduction"].mean().sort_index()


def signflip_test(
    effects: pd.Series,
    replicates: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    values = effects.to_numpy(float)
    observed = float(values.mean())
    null = np.empty(replicates)
    batch = 2000
    for start in range(0, replicates, batch):
        stop = min(replicates, start + batch)
        signs = rng.choice(
            np.asarray([-1.0, 1.0]),
            size=(stop - start, len(values)),
            replace=True,
        )
        null[start:stop] = (signs @ values) / len(values)
    p = float((1 + np.count_nonzero(null >= observed)) / (replicates + 1))
    bootstrap = np.empty(replicates)
    probability = np.full(len(values), 1.0 / len(values))
    for start in range(0, replicates, batch):
        stop = min(replicates, start + batch)
        weights = rng.multinomial(
            len(values), probability, size=stop - start
        ).astype(float)
        bootstrap[start:stop] = (weights @ values) / len(values)
    return {
        "systems": int(len(values)),
        "mean_system_equal_mse_reduction": observed,
        "cluster_bootstrap_ci95": interval(bootstrap),
        "one_sided_signflip_p": p,
    }


def holm(values: list[float]) -> list[float]:
    p = np.asarray(values, dtype=float)
    order = np.argsort(p, kind="mergesort")
    sorted_adjusted = np.empty(len(p))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[index]))
        sorted_adjusted[rank] = running
    adjusted = np.empty(len(p))
    for rank, index in enumerate(order):
        adjusted[index] = sorted_adjusted[rank]
    return adjusted.tolist()


def main() -> None:
    args = parse_args()
    design_path = args.design_path.resolve()
    design_text = design_path.read_text(encoding="utf-8")
    design = json.loads(design_text)
    prefix = args.output_prefix
    predictions_path = RESULTS / f"{prefix}_predictions.csv.gz"
    audit_path = RESULTS / f"{prefix}_audit.json"
    summary_path = RESULTS / f"{prefix}_inference_summary.json"
    if summary_path.exists() and not args.overwrite:
        raise FileExistsError("Inference output exists; pass --overwrite")
    frame = pd.read_csv(predictions_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(design_text.encode("utf-8")).hexdigest()
    if audit["design_sha256"] != expected_hash:
        raise AssertionError("Design hash mismatch")
    replicates = args.bootstrap_replicates or int(
        design["inference"]["bootstrap_replicates"]
    )
    signflip_replicates = args.signflip_replicates or int(
        design["inference"]["signflip_replicates"]
    )
    seed = int(design["inference"]["seed"])
    scopes = ("all", "q1", "q2", "q3", "q4")

    summaries: list[dict[str, Any]] = []
    for condition, local in frame.groupby("condition", sort=True):
        identity = local.iloc[0]
        for scope in scopes:
            result = condition_inference(
                local,
                scope,
                replicates,
                np.random.default_rng(stable_seed_local(seed, condition, scope)),
            )
            summaries.append(
                {
                    "condition": condition,
                    "arms": identity["arms"],
                    "provenance_mode": identity["provenance_mode"],
                    "donor": identity["donor"],
                    "contract": identity["contract"],
                    "budget": int(identity["budget"]),
                    **result,
                }
            )

    conditions = {name: local for name, local in frame.groupby("condition")}
    strict = conditions["provenance__full_doi_disjoint"]
    primary_specs = [
        (
            "strict_uts_vs_target_only",
            strict,
            "real_augmented",
            strict,
            "baseline",
        ),
        (
            "strict_uts_vs_shuffled_uts",
            strict,
            "real_augmented",
            strict,
            "shuffled_augmented",
        ),
        (
            "strict_uts_vs_hardness",
            strict,
            "real_augmented",
            conditions["specificity__hardness"],
            "real_augmented",
        ),
        (
            "strict_uts_vs_elongation",
            strict,
            "real_augmented",
            conditions["specificity__elongation"],
            "real_augmented",
        ),
    ]
    primary: list[dict[str, Any]] = []
    for name, first, first_column, second, second_column in primary_specs:
        effects = cluster_loss_difference(
            first,
            first_column,
            second,
            second_column,
            design["inference"]["primary_scope"],
        )
        primary.append(
            {
                "contrast": name,
                "direction": (
                    "positive means lower mean squared error for the first named method"
                ),
                **signflip_test(
                    effects,
                    signflip_replicates,
                    np.random.default_rng(
                        stable_seed_local(seed, "primary", name)
                    ),
                ),
            }
        )
    adjusted = holm([row["one_sided_signflip_p"] for row in primary])
    for row, value in zip(primary, adjusted):
        row["holm_adjusted_p"] = value
        row["holm_significant_0_05"] = bool(value < 0.05)

    summary_index = {
        (row["condition"], row["scope"]): row for row in summaries
    }
    provenance = [
        summary_index[(f"provenance__{mode}", scope)]
        for mode in design["arms"]["provenance_ladder"]["provenance_modes"]
        for scope in ("all", "q4")
    ]
    donors = [
        summary_index[
            (
                (
                    "provenance__full_doi_disjoint"
                    if donor == "uts"
                    else f"specificity__{donor}"
                ),
                scope,
            )
        ]
        for donor in design["arms"]["donor_specificity"]["donors"]
        for scope in ("all", "q4")
    ]
    state = [
        summary_index[
            (
                (
                    "provenance__full_doi_disjoint"
                    if contract == "full_state"
                    else f"state__{contract}"
                ),
                scope,
            )
        ]
        for contract in design["arms"]["state_dependence"]["contracts"]
        for scope in ("all", "q4")
    ]
    learning = [
        summary_index[(f"target_only__budget_{budget}", "q4")]
        for budget in design["arms"]["target_label_equivalence"]["budgets"]
    ]
    strict_q4 = summary_index[("provenance__full_doi_disjoint", "q4")]
    transfer_rmse = strict_q4["observed"]["real_augmented_rmse"]
    curve = sorted(
        (
            int(row["budget"]),
            float(row["observed"]["base_rmse"]),
        )
        for row in learning
    )
    label_equivalence: dict[str, Any] = {
        "transferred_model_budget": 60,
        "transferred_model_q4_rmse": transfer_rmse,
        "target_only_curve": [
            {"budget": budget, "q4_rmse": rmse} for budget, rmse in curve
        ],
    }
    crossing = None
    for (low_budget, low_rmse), (high_budget, high_rmse) in zip(
        curve[:-1], curve[1:]
    ):
        if (low_rmse - transfer_rmse) * (high_rmse - transfer_rmse) <= 0 and low_rmse != high_rmse:
            fraction = (transfer_rmse - low_rmse) / (high_rmse - low_rmse)
            crossing = math.exp(
                math.log(low_budget)
                + fraction * (math.log(high_budget) - math.log(low_budget))
            )
            break
    if crossing is None:
        label_equivalence["status"] = (
            "not_reached_by_maximum_budget"
            if min(rmse for _, rmse in curve) > transfer_rmse
            else "already_matched_at_minimum_budget"
        )
        label_equivalence["estimated_equivalent_target_labels"] = None
    else:
        label_equivalence["status"] = "interpolated_within_frozen_curve"
        label_equivalence["estimated_equivalent_target_labels"] = float(crossing)

    payload = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": expected_hash,
        "replicates": {
            "elemental_system_cluster_bootstrap": replicates,
            "elemental_system_signflip": signflip_replicates,
        },
        "primary_contrasts": primary,
        "primary_family_holm_survivors": [
            row["contrast"] for row in primary if row["holm_significant_0_05"]
        ],
        "provenance_ladder": provenance,
        "donor_specificity": donors,
        "state_dependence": state,
        "target_label_equivalence": label_equivalence,
        "all_condition_summaries": summaries,
        "claim_guard": design["claim_guard"],
    }
    summary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "primary_family_holm_survivors": payload[
                    "primary_family_holm_survivors"
                ],
                "target_label_equivalence": label_equivalence,
                "summary": summary_path.name,
            },
            indent=2,
        )
    )


def stable_seed_local(*parts: object) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little")


if __name__ == "__main__":
    main()
