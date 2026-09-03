"""Verify completeness and provenance of the neighborhood-policy benchmark."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN = ANALYSIS / "neighbor_transfer_policy_design.json"
INPUT_META = RESULTS / "obelix_ood_discovery_input_meta.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    summary_path = RESULTS / "neighbor_transfer_policy_summary.json"
    complete_path = RESULTS / "neighbor_transfer_policy_COMPLETE.json"
    required = [
        summary_path,
        complete_path,
        RESULTS / "neighbor_transfer_policy_balam_checksums.sha256",
        RESULTS / "neighbor_transfer_policy_reach.csv",
        RESULTS / "neighbor_transfer_policy_trajectories.csv",
        RESULTS / "neighbor_transfer_policy_contrasts.csv",
        RESULTS / "neighbor_transfer_policy_bootstrap.csv",
        RESULTS / "neighbor_transfer_policy_secondary_utility.csv",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing policy results: " + ", ".join(missing))

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    input_meta = json.loads(INPUT_META.read_text(encoding="utf-8"))
    design_hash = sha256_file(DESIGN)
    if summary["design_sha256"] != design_hash:
        raise AssertionError("Summary design hash does not match the frozen design")
    if summary["input_sha256"] != input_meta["input_sha256"]:
        raise AssertionError("Summary input hash does not match frozen input metadata")
    if complete["summary_sha256"] != sha256_file(summary_path):
        raise AssertionError("COMPLETE sentinel summary hash mismatch")

    checksum_path = RESULTS / "neighbor_transfer_policy_balam_checksums.sha256"
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        local_path = ROOT / relative.strip()
        if not local_path.is_file():
            raise FileNotFoundError(f"Checksum target is missing: {relative}")
        if sha256_file(local_path) != expected:
            raise AssertionError(f"Checksum mismatch for {relative}")

    reaches = pd.read_csv(RESULTS / "neighbor_transfer_policy_reach.csv")
    contrasts = pd.read_csv(RESULTS / "neighbor_transfer_policy_contrasts.csv")
    bootstrap = pd.read_csv(RESULTS / "neighbor_transfer_policy_bootstrap.csv")
    trajectories = pd.read_csv(
        RESULTS / "neighbor_transfer_policy_trajectories.csv"
    )
    utility = pd.read_csv(
        RESULTS / "neighbor_transfer_policy_secondary_utility.csv"
    )
    expected_policies = {
        "uniform_random",
        "target_ucb_beta1",
        "target_mean_greedy",
        "composition_novelty",
        "thermoelectric_prior_static",
        "target_source_rank_fusion",
        "target_source_novelty_rank_fusion",
        "alloy_prior_static_control",
        "catalysis_prior_static_control",
        "shuffled_thermoelectric_static_control",
    }
    if set(reaches["policy"]) != expected_policies:
        raise AssertionError("Policy coverage differs from the frozen design")
    if len(reaches) != 2 * 100 * len(expected_policies):
        raise AssertionError(f"Unexpected reach row count: {len(reaches)}")
    counts = reaches.groupby(["scope", "policy"])["seed"].nunique()
    if not (counts == 100).all():
        raise AssertionError("Not every policy has 100 paired seeds in both scopes")
    if len(contrasts) != 20:
        raise AssertionError(f"Expected 20 contrasts, found {len(contrasts)}")
    if len(bootstrap) != 20 * 5000:
        raise AssertionError(f"Expected 100000 bootstrap rows, found {len(bootstrap)}")
    if len(trajectories) != 2 * 100 * len(expected_policies) * 40:
        raise AssertionError(f"Unexpected trajectory row count: {len(trajectories)}")
    if len(utility) != 2 * 100 * len(expected_policies):
        raise AssertionError(f"Unexpected secondary-utility row count: {len(utility)}")

    policy_summary = (
        reaches.groupby(["scope", "policy"], sort=True)
        .agg(
            seeds=("seed", "size"),
            mean_experiments=("experiments_to_hit", "mean"),
            median_experiments=("experiments_to_hit", "median"),
            censor_fraction=("censored", "mean"),
        )
        .reset_index()
    )
    saved_policy_summary = pd.DataFrame(summary["policies"]).sort_values(
        ["scope", "policy"]
    ).reset_index(drop=True)
    pd.testing.assert_frame_equal(
        policy_summary,
        saved_policy_summary[policy_summary.columns],
        check_dtype=False,
        rtol=1e-12,
        atol=1e-12,
    )

    if trajectories.duplicated(["scope", "seed", "policy", "step"]).any():
        raise AssertionError("Duplicate trajectory scope/seed/policy/step rows")
    reach_lookup = reaches.set_index(["scope", "seed", "policy"])
    utility_lookup = utility.set_index(["scope", "seed", "policy"])
    inferred_pool_max: dict[str, list[float]] = {}
    for key, local in trajectories.groupby(["scope", "seed", "policy"], sort=False):
        local = local.sort_values("step")
        if local["step"].tolist() != list(range(1, 41)):
            raise AssertionError(f"Incomplete or unordered trajectory for {key}")
        hits = local["is_true_top5_hit"].astype(bool).to_numpy()
        expected_reach = int(np.flatnonzero(hits)[0] + 1) if hits.any() else 41
        if int(reach_lookup.loc[key, "experiments_to_hit"]) != expected_reach:
            raise AssertionError(f"First-hit reach does not match trajectory for {key}")
        record = utility_lookup.loc[key]
        cumulative = np.cumsum(hits)
        if not np.isclose(record["cumulative_hit_auc_to_40"], cumulative.sum()):
            raise AssertionError(f"Cumulative-hit AUC mismatch for {key}")
        true_hit_n = int(reach_lookup.loc[key, "true_hit_n"])
        for horizon in (5, 10, 20, 40):
            local_horizon = local.iloc[:horizon]
            hit_count = int(local_horizon["is_true_top5_hit"].astype(bool).sum())
            best_y = float(local_horizon["chosen_y"].max())
            if int(record[f"top5_hits_at_{horizon}"]) != hit_count:
                raise AssertionError(f"Hit-count mismatch for {key} at {horizon}")
            if not np.isclose(
                record[f"top5_recall_at_{horizon}"], hit_count / true_hit_n
            ):
                raise AssertionError(f"Recall mismatch for {key} at {horizon}")
            if not np.isclose(record[f"best_y_at_{horizon}"], best_y):
                raise AssertionError(f"Best-y mismatch for {key} at {horizon}")
            inferred_pool_max.setdefault(str(key[0]), []).append(
                float(
                    record[f"best_y_at_{horizon}"]
                    + record[f"regret_to_pool_max_at_{horizon}"]
                )
            )
    for scope, values in inferred_pool_max.items():
        if not np.allclose(values, values[0], rtol=0, atol=1e-12):
            raise AssertionError(f"Inconsistent inferred pool maximum for {scope}")

    bootstrap_keys = ["scope", "family", "left_policy", "right_policy"]
    for _, row in contrasts.iterrows():
        local = reaches[reaches["scope"] == row["scope"]]
        paired = local.pivot(
            index="seed", columns="policy", values="experiments_to_hit"
        )
        effect = (
            paired[row["right_policy"]] - paired[row["left_policy"]]
        ).to_numpy(float)
        if not np.isclose(row["mean_experiments_saved_by_left"], effect.mean()):
            raise AssertionError(f"Contrast mean mismatch for {row[bootstrap_keys].tolist()}")
        if not np.isclose(row["fraction_seeds_left_improves"], np.mean(effect > 0)):
            raise AssertionError(
                f"Contrast improvement fraction mismatch for {row[bootstrap_keys].tolist()}"
            )
        if not np.isclose(row["fraction_seeds_tied"], np.mean(effect == 0)):
            raise AssertionError(f"Contrast tie fraction mismatch for {row[bootstrap_keys].tolist()}")
        selected = bootstrap.copy()
        for column in bootstrap_keys:
            selected = selected[selected[column] == row[column]]
        if len(selected) != 5000:
            raise AssertionError(
                f"Bootstrap coverage mismatch for {row[bootstrap_keys].tolist()}"
            )
        interval = np.quantile(
            selected["mean_experiments_saved_by_left"].to_numpy(float),
            [0.025, 0.975],
        )
        if not np.allclose(interval, json.loads(row["bootstrap_95"]), atol=1e-12):
            raise AssertionError(
                f"Bootstrap interval mismatch for {row[bootstrap_keys].tolist()}"
            )

    static_policies = {
        "thermoelectric_prior_static",
        "alloy_prior_static_control",
        "catalysis_prior_static_control",
        "shuffled_thermoelectric_static_control",
    }
    for (scope, policy), local in trajectories[
        trajectories["policy"].isin(static_policies)
    ].groupby(["scope", "policy"], sort=True):
        sequences = {
            tuple(group.sort_values("step")["chosen_index"].astype(int))
            for _, group in local.groupby("seed")
        }
        if len(sequences) != 1:
            raise AssertionError(f"Static policy unexpectedly varies: {scope}/{policy}")

    print(
        json.dumps(
            {
                "status": "verified-complete",
                "design_sha256": design_hash,
                "input_sha256": input_meta["input_sha256"],
                "reach_rows": len(reaches),
                "contrasts": len(contrasts),
                "bootstrap_rows": len(bootstrap),
                "trajectory_rows": len(trajectories),
                "secondary_utility_rows": len(utility),
                "numeric_recomputation": "passed",
                "all_remote_checksums": "matched",
                "static_policy_unique_trajectories_per_scope": 1,
                "claim_guard": summary["claim_guard"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
