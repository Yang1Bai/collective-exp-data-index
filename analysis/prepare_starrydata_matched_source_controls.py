"""Build predeclared Starrydata matched-source controls without target outcomes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.common import composition_features  # noqa: E402
from analysis.prepare_starrydata_reverse_transport import load_caltech_source  # noqa: E402
from analysis.run_caltech_ionic_external_policy import source_entities  # noqa: E402

RESULTS = HERE / "results"
FREEZE = RESULTS / "starrydata_reverse_PREOUTCOME.json"
METADATA = RESULTS / "starrydata_reverse_target_metadata.csv"
PREDICTIONS = RESULTS / "starrydata_reverse_source_predictions.csv"
OUTPUT = RESULTS / "starrydata_reverse_matched_source_controls.csv"
AUDIT = RESULTS / "starrydata_reverse_matched_source_controls.json"

SOURCE_MAP = {
    "obelix_adjacent_ionic": "obelix_same_property",
    "borg_wrong_mechanical": "borg_mechanical_control",
    "ocx_wrong_catalysis": "ocx_catalysis_control",
}
ADJACENT = ["obelix_adjacent_ionic", "caltech_adjacent_ionic"]
WRONG = ["borg_wrong_mechanical", "ocx_wrong_catalysis"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "little")


def verify_original_freeze() -> dict:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    for relative, expected in freeze["artifact_hashes"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"Original pre-outcome artifact changed: {relative}")
    return freeze


def group_preserving_subset(frame: pd.DataFrame, target_n: int, label: str) -> pd.DataFrame:
    groups = {str(group): local.index.to_numpy(int) for group, local in frame.groupby("group")}
    order = sorted(groups, key=lambda group: hashlib.sha256(f"{label}|{group}".encode()).hexdigest())
    selected: list[int] = []
    deferred: list[str] = []
    for group in order:
        members = list(groups[group])
        if len(selected) + len(members) <= target_n:
            selected.extend(members)
        else:
            deferred.append(group)
    if deferred:
        best = min(deferred, key=lambda group: (abs(len(selected) + len(groups[group]) - target_n), group))
        if abs(len(selected) + len(groups[best]) - target_n) < abs(len(selected) - target_n):
            selected.extend(groups[best])
    return frame.loc[sorted(selected)].reset_index(drop=True)


def fit_rank(frame: pd.DataFrame, target_x: np.ndarray, label: str) -> np.ndarray:
    x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    model = ExtraTreesRegressor(
        n_estimators=400,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed(label),
        n_jobs=-1,
    )
    model.fit(x, frame["value"].to_numpy(float))
    prediction = model.predict(target_x)
    return pd.Series(prediction).rank(method="average", pct=True).to_numpy()


def deciles(values: pd.Series) -> np.ndarray:
    ranked = values.rank(method="average", pct=True).to_numpy(float)
    return np.minimum(9, np.floor(ranked * 10).astype(int))


def main() -> None:
    freeze = verify_original_freeze()
    metadata = pd.read_csv(METADATA)
    frozen_predictions = pd.read_csv(PREDICTIONS)
    if any(column.lower() in {"y", "zt", "target_value", "outcome"} for column in metadata.columns):
        raise AssertionError("Target outcome is forbidden in matched-control generation")
    target_keys = set(metadata["material_key"])
    target_dois = {value for value in metadata["normalized_doi"].dropna().astype(str) if value}
    target_x = composition_features(metadata["material_key"].tolist()).astype(np.float32)
    frames: dict[str, pd.DataFrame] = {}
    for source in ADJACENT + WRONG:
        if source == "caltech_adjacent_ionic":
            frames[source] = load_caltech_source(target_keys, target_dois)
        else:
            frames[source] = source_entities(SOURCE_MAP[source], target_keys, target_dois)

    output = metadata[["entity_id", "split", "component_id"]].copy()
    audit_pairs: list[dict] = []
    for adjacent in ADJACENT:
        for wrong in WRONG:
            matched_n = min(len(frames[adjacent]), len(frames[wrong]))
            adjacent_subset = group_preserving_subset(frames[adjacent], matched_n, f"size|{adjacent}|{wrong}|adjacent")
            wrong_subset = group_preserving_subset(frames[wrong], matched_n, f"size|{adjacent}|{wrong}|wrong")
            pair = f"{adjacent}_vs_{wrong}"
            output[f"size_matched_{adjacent}_for_{wrong}_rank"] = fit_rank(
                adjacent_subset, target_x, f"size-rank|{pair}|adjacent"
            )
            output[f"size_matched_{wrong}_for_{adjacent}_rank"] = fit_rank(
                wrong_subset, target_x, f"size-rank|{pair}|wrong"
            )
            adjacent_distance = frozen_predictions[f"{adjacent}_coverage_distance"]
            wrong_distance = frozen_predictions[f"{wrong}_coverage_distance"]
            adjacent_decile = deciles(adjacent_distance)
            wrong_decile = deciles(wrong_distance)
            output[f"coverage_matched_{pair}"] = adjacent_decile == wrong_decile
            audit_pairs.append(
                {
                    "pair": pair,
                    "requested_entities": matched_n,
                    "adjacent_entities": len(adjacent_subset),
                    "wrong_entities": len(wrong_subset),
                    "coverage_matched_target_entities": int(np.sum(adjacent_decile == wrong_decile)),
                }
            )
    # OCx is the frozen skill match for both ionic sources: its grouped OOF
    # Spearman lies within 0.05 of each; no target result enters that choice.
    output["skill_matched_wrong_rank"] = frozen_predictions["ocx_wrong_catalysis_rank"].to_numpy()
    output.to_csv(OUTPUT, index=False)
    audit = {
        "status": "outcome-independent-controls-complete",
        "claim_guard": "Generated after smoke outcome access but uses no target outcome column and implements controls named before access.",
        "original_preoutcome_sha256": sha256(FREEZE),
        "original_artifact_hashes": freeze["artifact_hashes"],
        "target_entities": len(output),
        "pairs": audit_pairs,
        "skill_match": {
            "control": "ocx_wrong_catalysis",
            "criterion": "absolute grouped OOF Spearman difference <= 0.05",
        },
        "output_sha256": sha256(OUTPUT),
    }
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
