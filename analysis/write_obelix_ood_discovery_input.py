"""Freeze the self-contained input used by the OBELiX OOD campaign.

The resulting NPZ contains only the fixed target table, composition features,
hard-OOD membership, and already-frozen source predictions.  It lets the
sequential campaign run on Balam without the project SQLite database or any
other analysis module.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import composition_features, formula_dataset, load_obelix, random_forest
from run_confirmatory import RANDOM_SEED, SOURCE_SPECS


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "obelix_ood_discovery_design.json"
SOURCE_CACHE_PATH = RESULTS / "obelix_frozen_source_features.csv"
SOURCE_META_PATH = RESULTS / "obelix_frozen_source_features_meta.json"
MEMBERSHIP_PATH = RESULTS / "hard_ood_composition_membership.csv"
OUTPUT_PATH = RESULTS / "obelix_ood_discovery_input.npz"
OUTPUT_META_PATH = RESULTS / "obelix_ood_discovery_input_meta.json"

SOURCE_COLUMNS = {
    "Thermoelectric ZT": "thermoelectric_prior",
    "Alloy yield strength": "alloy_control",
    "CO2R H2 Faradaic efficiency": "catalysis_control",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def main() -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    source_meta = json.loads(SOURCE_META_PATH.read_text(encoding="utf-8"))
    target = load_obelix()
    if len(target) != 500:
        raise AssertionError(f"Expected 500 canonical OBELiX rows, found {len(target)}")

    source_cache = pd.read_csv(SOURCE_CACHE_PATH)
    if source_cache["material_key"].tolist() != target["material_key"].tolist():
        raise AssertionError("Frozen source cache identities do not match OBELiX target order")

    membership = pd.read_csv(MEMBERSHIP_PATH)
    membership = membership[
        membership["edge_id"]
        == "hard_ood_obelix_thermoelectric_zt_to_ionic_conductivity"
    ].copy()
    selected = membership["hard_ood_selected"].astype(str).str.lower().eq("true")
    hard_keys = set(membership.loc[selected, "identity"])
    hard_ood_selected = target["material_key"].isin(hard_keys).to_numpy(bool)

    test_mask = target["split"].eq("test").to_numpy(bool)
    if int(test_mask.sum()) != 110:
        raise AssertionError(f"Expected 110 official-test rows, found {test_mask.sum()}")
    if int(np.sum(test_mask & hard_ood_selected)) != 44:
        raise AssertionError(
            f"Expected 44 hard-OOD official-test rows, found {np.sum(test_mask & hard_ood_selected)}"
        )
    if np.any(~test_mask & hard_ood_selected):
        raise AssertionError("Hard-OOD membership unexpectedly includes official-train rows")

    target_features = composition_features(target["material_key"].tolist()).astype(
        np.float64
    )
    arrays: dict[str, np.ndarray] = {
        "row_index": np.arange(len(target), dtype=np.int64),
        "material_key": target["material_key"].to_numpy(str),
        "value": target["value"].to_numpy(np.float64),
        "split": target["split"].to_numpy(str),
        "group": target["group"].to_numpy(str),
        "hard_ood_selected": hard_ood_selected,
        "composition_features": target_features,
    }

    source_overlaps: dict[str, int] = {}
    source_refit_max_abs_difference: dict[str, float] = {}
    source_pre_serialization_hashes: dict[str, str] = {}
    for source_label, output_name in SOURCE_COLUMNS.items():
        dataset, prop = SOURCE_SPECS[source_label]
        source = formula_dataset(dataset, prop)
        source_features = composition_features(source["material_key"].tolist())
        regenerated = random_forest(RANDOM_SEED, 240).fit(
            source_features, source["value"].to_numpy(np.float64)
        ).predict(target_features)
        values = source_cache[source_label].to_numpy(np.float64)
        maximum_difference = float(np.max(np.abs(regenerated - values)))
        if maximum_difference > 1e-10:
            raise AssertionError(
                f"CSV source cache differs materially for {source_label}: {maximum_difference}"
            )
        source_refit_max_abs_difference[source_label] = maximum_difference
        source_pre_serialization_hashes[source_label] = source_meta[
            "feature_sha256"
        ][source_label]
        arrays[output_name] = values
        source_overlaps[source_label] = len(
            set(source["material_key"]) & set(target["material_key"])
        )

    if any(source_overlaps.values()):
        raise AssertionError(f"Exact source-target composition overlap: {source_overlaps}")

    np.savez(OUTPUT_PATH, **arrays)
    array_hashes = {name: sha256_array(values) for name, values in arrays.items()}
    metadata = {
        "status": "frozen-self-contained-input-for-prespecified-sequential-campaign",
        "design_sha256": hashlib.sha256(design_bytes).hexdigest(),
        "source_cache_sha256": sha256_file(SOURCE_CACHE_PATH),
        "source_metadata_sha256": sha256_file(SOURCE_META_PATH),
        "hard_ood_membership_sha256": sha256_file(MEMBERSHIP_PATH),
        "input_sha256": sha256_file(OUTPUT_PATH),
        "array_sha256": array_hashes,
        "rows": len(target),
        "composition_feature_count": int(arrays["composition_features"].shape[1]),
        "official_train_n": int(np.sum(arrays["split"] == "train")),
        "official_test_n": int(test_mask.sum()),
        "hard_ood_test_n": int(np.sum(test_mask & hard_ood_selected)),
        "source_target_exact_overlaps": source_overlaps,
        "source_pre_serialization_sha256": source_pre_serialization_hashes,
        "source_refit_max_abs_difference": source_refit_max_abs_difference,
        "source_refit_tolerance": 1e-10,
        "source_value_note": (
            "The NPZ uses the already-frozen CSV cache values. Pre-serialization "
            "binary hashes are retained for provenance but are not expected to "
            "survive decimal CSV round-trip or parallel forest last-bit variation."
        ),
    }
    OUTPUT_META_PATH.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
