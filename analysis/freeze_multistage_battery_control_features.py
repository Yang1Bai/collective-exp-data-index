"""Freeze negative-control target features before Stage 2 outcome release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
SOURCE_FEATURES = DIR / "stage2_outcome_free_source_features.csv"
SOURCE_FREEZE = DIR / "STAGE1_SOURCE_FREEZE.json"
OUTPUT = DIR / "stage2_frozen_control_features.csv"
AUDIT = DIR / "STAGE2_CONTROL_FEATURE_FREEZE.json"
SEED = 20260720
RANDOM_FEATURES = 6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    source = pd.read_csv(SOURCE_FEATURES, dtype={"file_id": str})
    freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    source = source.sort_values(["type", "condition_group", "file_id"]).reset_index(drop=True)
    source["global_credibility_source_feature"] = 0.0
    source["shuffled_source_prediction"] = np.nan
    rng = np.random.default_rng(SEED)
    for aging_type, indices in source.groupby("type").groups.items():
        idx = np.array(sorted(indices))
        reliability = max(0.0, min(1.0, float(freeze["model_summaries"][aging_type]["source_oof_r2"])))
        source.loc[idx, "global_credibility_source_feature"] = (
            reliability * source.loc[idx, "source_prediction_centered"].to_numpy()
        )
        group_means = source.loc[idx].groupby("condition_group")["source_prediction"].mean().sort_index()
        groups = group_means.index.to_numpy()
        shuffled_groups = groups.copy()
        rng.shuffle(shuffled_groups)
        mapping = dict(zip(groups, group_means.loc[shuffled_groups].to_numpy()))
        source.loc[idx, "shuffled_source_prediction"] = source.loc[idx, "condition_group"].map(mapping).to_numpy()
    for column in range(RANDOM_FEATURES):
        source[f"random_feature_{column + 1}"] = rng.standard_normal(len(source))
    columns = [
        "file_id", "serial_internal", "serial", "type", "condition_group",
        "global_credibility_source_feature", "wrong_property_mass_prediction",
        "shuffled_source_prediction",
        *[f"random_feature_{index + 1}" for index in range(RANDOM_FEATURES)],
    ]
    source[columns].to_csv(OUTPUT, index=False, lineterminator="\n")
    audit = {
        "status": "verified-outcome-free-controls-frozen",
        "rows": len(source),
        "random_features": RANDOM_FEATURES,
        "shuffle_scope": "condition-group mean predictions permuted separately within calendar and cycle strata",
        "global_credibility": {
            aging_type: max(0.0, min(1.0, float(freeze["model_summaries"][aging_type]["source_oof_r2"])))
            for aging_type in ("k", "z")
        },
        "stage2_numeric_outcomes_opened": False,
        "source_features_sha256": sha256(SOURCE_FEATURES),
        "control_features_sha256": sha256(OUTPUT),
        "claim_guard": "Wrong-property, shuffled-source, global-credibility, and random features are fixed controls and cannot be regenerated after Stage 2 release.",
        "errors": [],
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
