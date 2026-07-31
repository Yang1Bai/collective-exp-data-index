"""Verify that TRI OER FOM access remains gated by the frozen artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT_PATH = HERE.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from analysis.prepare_tri_oer_neighbor import FREEZE, METADATA, POLICIES, CARDS, PREDICTIONS, ROOT, sha256


def main() -> None:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["status"] != "preoutcome-frozen":
        raise AssertionError("TRI pre-outcome status invalid")
    for relative, expected in freeze["artifact_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"TRI pre-outcome hash mismatch: {relative}")
    frames = [pd.read_csv(path) for path in [METADATA, PREDICTIONS, POLICIES, CARDS]]
    for frame in frames:
        if {column.lower() for column in frame.columns} & {"fom", "target_value", "outcome"}:
            raise AssertionError("TRI target FOM leaked before access")
    metadata, policies, cards = frames[0], frames[2], frames[3]
    required_policies = {
        "uniform_family_first", "composition_novelty_family_first",
        "acid_oer_same_reaction_single", "orr_adjacent_single", "ocx_adjacent_single",
        "neighbor_entity_consensus", "cca_family_first_consensus",
        "cca_family_first_round_robin", "wrong_source_family_first",
        "shuffled_neighbor_family_first",
    }
    if set(policies["policy"]) != required_policies or len(cards) != 3:
        raise AssertionError("TRI policy/card family incomplete")
    print(json.dumps({
        "status": "verified-preoutcome",
        "entities": len(metadata),
        "plates": sorted(metadata["plate"].astype(str).unique()),
        "policies": len(required_policies),
        "cards": len(cards),
        "sentinel_sha256": sha256(FREEZE),
    }, indent=2))


if __name__ == "__main__":
    main()
