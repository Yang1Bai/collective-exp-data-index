"""Freeze 300 outcome-independent scaffold draws per discovery budget."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_transfer_method_discovery_config.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
DRAW_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_draws.csv"
)
MANIFEST_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_draws_manifest.json"
)
BASE_DRAW_SCRIPT = HERE / "prepare_optical_photocatalysis_development_draws.py"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_draw_module():
    spec = importlib.util.spec_from_file_location("frozen_draws", BASE_DRAW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the frozen draw implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Design changed after pair audit")
    if audit["recipient"]["metadata_sha256"] != file_hash(METADATA_PATH):
        raise RuntimeError("Outcome-free metadata changed after pair audit")

    development = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    scaffold_rows = {
        str(scaffold): group.index.to_numpy(dtype=int)
        for scaffold, group in development.groupby("scaffold", sort=True)
    }
    budgets = [int(value) for value in config["development_design"]["label_budgets"]]
    repeats = int(config["development_design"]["scaffold_draws_per_budget"])
    draw_module = load_draw_module()
    frames = [
        draw_module.make_draw(development, scaffold_rows, budget, repeat)
        for budget in budgets
        for repeat in range(repeats)
    ]
    draws = pd.concat(frames, ignore_index=True)
    draws.to_csv(DRAW_PATH, index=False, lineterminator="\n")

    for budget in budgets:
        rows = draws[(draws["budget"] == budget) & (draws["role"] == "training")]
        counts = rows.groupby("repeat").size()
        if len(counts) != repeats or set(counts.astype(int)) != {budget}:
            raise RuntimeError(f"Training budget drift at {budget}")
    for (budget, repeat), rows in draws.groupby(["budget", "repeat"]):
        training_scaffolds = set(
            rows.loc[rows["role"] == "training", "scaffold"].astype(str)
        )
        excluded_keys = set(rows["target_key"].astype(str))
        evaluation_scaffolds = set(
            development.loc[
                ~development["target_key"].isin(excluded_keys), "scaffold"
            ].astype(str)
        )
        if training_scaffolds & evaluation_scaffolds:
            raise RuntimeError(
                f"Scaffold crossed training/evaluation at {budget}/{repeat}"
            )

    manifest = {
        "status": "outcome-independent-method-discovery-draws-frozen",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "draw_implementation_sha256": file_hash(BASE_DRAW_SCRIPT),
        "draw_sha256": file_hash(DRAW_PATH),
        "budgets": budgets,
        "repeats_per_budget": repeats,
        "stored_rows": int(len(draws)),
        "outcome_access": "No recipient HER value or calculated descriptor was loaded.",
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
