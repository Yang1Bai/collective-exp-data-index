"""Freeze outcome-independent scaffold draws for the recipient development gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
DRAW_PATH = HERE / "results" / "optical_photocatalysis_development_draws.csv"
MANIFEST_PATH = (
    HERE / "results" / "optical_photocatalysis_development_draws_manifest.json"
)

SEED = 20260724
REPEATS = 100


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_draw(
    development: pd.DataFrame,
    scaffold_rows: dict[str, np.ndarray],
    budget: int,
    repeat: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + budget * 1000 + repeat)
    scaffold_order = rng.permutation(np.asarray(sorted(scaffold_rows), dtype=object))
    roles = np.full(len(development), "evaluation", dtype=object)
    remaining = budget
    boundary_scaffold = ""

    for scaffold in scaffold_order:
        rows = scaffold_rows[str(scaffold)]
        if remaining == 0:
            break
        if len(rows) <= remaining:
            roles[rows] = "training"
            remaining -= len(rows)
            continue

        member_order = rng.permutation(len(rows))
        chosen = rows[member_order[:remaining]]
        excluded = rows[member_order[remaining:]]
        roles[chosen] = "training"
        roles[excluded] = "excluded_boundary_scaffold"
        boundary_scaffold = str(scaffold)
        remaining = 0
        break

    if remaining != 0 or int(np.sum(roles == "training")) != budget:
        raise RuntimeError(
            f"Could not construct exact outcome-free budget {budget}, repeat {repeat}"
        )

    stored = roles != "evaluation"
    result = development.loc[stored, ["target_key", "scaffold"]].copy()
    result.insert(0, "repeat", repeat)
    result.insert(1, "budget", budget)
    result["role"] = roles[stored]
    result["boundary_scaffold"] = boundary_scaffold

    training_scaffolds = set(result.loc[result["role"] == "training", "scaffold"])
    excluded_keys = set(result["target_key"])
    evaluation_scaffolds = set(
        development.loc[
            ~development["target_key"].isin(excluded_keys), "scaffold"
        ]
    )
    if training_scaffolds & evaluation_scaffolds:
        raise RuntimeError("A scaffold crossed training and evaluation")
    return result


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if file_hash(DESIGN_PATH) != audit["design_sha256"]:
        raise RuntimeError("Design changed after the outcome-independent audit")
    if file_hash(METADATA_PATH) != audit["recipient"]["metadata_sha256"]:
        raise RuntimeError("Outcome-free metadata changed after audit")

    budgets = [
        int(value)
        for value in design["recipient_modeling"]["label_budgets"]
        if int(value) < int(audit["recipient"]["raw_rows"]["development"])
    ]
    development = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    if len(development) != int(audit["recipient"]["raw_rows"]["development"]):
        raise RuntimeError("Development row count changed")

    scaffold_rows = {
        str(scaffold): group.index.to_numpy(dtype=int)
        for scaffold, group in development.groupby("scaffold", sort=True)
    }
    frames = [
        make_draw(development, scaffold_rows, budget, repeat)
        for budget in budgets
        for repeat in range(REPEATS)
    ]
    draws = pd.concat(frames, ignore_index=True)
    draws.to_csv(DRAW_PATH, index=False, lineterminator="\n")

    role_counts = (
        draws.groupby(["budget", "repeat", "role"])
        .size()
        .rename("rows")
        .reset_index()
    )
    training_counts = role_counts.query("role == 'training'")
    for budget in budgets:
        observed = set(
            training_counts.loc[training_counts["budget"] == budget, "rows"].astype(int)
        )
        if observed != {budget}:
            raise RuntimeError(f"Training budget drift for {budget}: {observed}")

    manifest = {
        "status": "outcome-independent-development-draws-frozen",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "draw_sha256": file_hash(DRAW_PATH),
        "seed": SEED,
        "repeats": REPEATS,
        "budgets": budgets,
        "stored_rows": int(len(draws)),
        "role_counts_by_budget": {
            str(budget): {
                role: int(
                    role_counts.loc[
                        (role_counts["budget"] == budget)
                        & (role_counts["role"] == role),
                        "rows",
                    ].sum()
                )
                for role in sorted(
                    set(role_counts.loc[role_counts["budget"] == budget, "role"])
                )
            }
            for budget in budgets
        },
        "boundary_policy": (
            "Only training and boundary-excluded keys are stored. Every other "
            "development key is evaluation. If the final selected scaffold exceeds "
            "the exact label budget, a deterministic subset enters training and "
            "every unselected molecule from that scaffold is excluded from evaluation."
        ),
        "outcome_access": "No recipient HER values or calculated descriptors were loaded.",
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
