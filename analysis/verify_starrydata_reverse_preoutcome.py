"""Verify the Starrydata outcome-free freeze before target ZT access."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"
FREEZE = RESULTS / "starrydata_reverse_PREOUTCOME.json"

REQUIRED_POLICIES = {
    "uniform_family_first",
    "composition_novelty_family_first",
    "estm_best_same_domain",
    "obelix_adjacent_single",
    "caltech_adjacent_single",
    "neighbor_entity_consensus",
    "cca_family_first_consensus",
    "cca_family_first_round_robin",
    "wrong_source_family_first",
    "shuffled_neighbor_family_first",
}
FORBIDDEN = {"y", "zt", "target_value", "outcome"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["status"] != "preoutcome-frozen":
        raise AssertionError("Pre-outcome sentinel is not frozen")
    for relative, expected in freeze["artifact_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"Artifact hash mismatch: {relative}")

    metadata = pd.read_csv(RESULTS / "starrydata_reverse_target_metadata.csv")
    predictions = pd.read_csv(RESULTS / "starrydata_reverse_source_predictions.csv")
    policies = pd.read_csv(RESULTS / "starrydata_reverse_policy_orders.csv")
    cards = pd.read_csv(RESULTS / "starrydata_reverse_hypothesis_cards.csv")
    for name, frame in {
        "metadata": metadata,
        "predictions": predictions,
        "policies": policies,
        "cards": cards,
    }.items():
        leaked = {column.lower() for column in frame.columns} & FORBIDDEN
        if leaked:
            raise AssertionError(f"Target outcome column in {name}: {sorted(leaked)}")
    if metadata["entity_id"].duplicated().any():
        raise AssertionError("Target entity identifiers are not unique")
    if set(policies["policy"]) != REQUIRED_POLICIES:
        raise AssertionError("Fixed policy family is incomplete or changed")
    evaluation_n = int(metadata["split"].eq("evaluation").sum())
    counts = policies.groupby("policy").size()
    if not (counts == evaluation_n).all():
        raise AssertionError("Every fixed policy must rank the complete evaluation pool")
    if len(cards) < 3 or not cards["written_before_target_outcome"].astype(bool).all():
        raise AssertionError("Prewritten hypothesis-card gate failed")
    if metadata["component_id"].nunique() < 40 or metadata["provenance_group"].nunique() < 20:
        raise AssertionError("Independent-unit minimum gate failed")
    print(
        json.dumps(
            {
                "status": "verified-preoutcome",
                "target_entities": len(metadata),
                "evaluation_entities": evaluation_n,
                "components": int(metadata["component_id"].nunique()),
                "policies": len(REQUIRED_POLICIES),
                "hypothesis_cards": len(cards),
                "sentinel_sha256": sha256(FREEZE),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
