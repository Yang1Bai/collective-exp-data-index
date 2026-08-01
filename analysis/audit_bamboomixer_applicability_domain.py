"""Post-outcome, predictor-only applicability audit for the LiAsF6 benchmark.

The transfer benchmark defines OOD by salt identity and independent data
provenance.  This script asks a different, descriptive question: how far is the
recipient from the source in the *actual representation used by the model*?

Outcome values are used only to reproduce the eligibility filter frozen in
``bamboomixer_response_transfer_design.json``.  They are not supplied to any
distance calculation, threshold, or model in this audit.  The audit is
therefore descriptive and cannot upgrade the retrospective benchmark to a
confirmatory result.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from common import RESULTS, ensure_output_dirs
from mixture_response_transfer_common import (
    CHEMISTRY_FEATURE_DIM,
    MOLECULE_FEATURE_DIM,
    conductivity_records,
    formula_signature,
    load_json_records,
    mixture_features,
    salt_identity,
    sha256,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "bamboomixer_response_transfer_design.json"
DATA_DIR = HERE / "external_data" / "bamboomixer_response_transfer"
SOURCE_PATH = DATA_DIR / "bamboomixer_original_data.json"
TARGET_PATH = DATA_DIR / "LiAsF6_conductivity.json"
SUMMARY_PATH = RESULTS / "bamboomixer_applicability_domain_summary.json"
ROWS_PATH = RESULTS / "bamboomixer_applicability_domain_distances.csv"


def empirical_percentile(reference: np.ndarray, value: float) -> float:
    reference = np.asarray(reference, dtype=float)
    return float(np.mean(reference <= float(value)) * 100.0)


def pca_embedding(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    scaler = StandardScaler().fit(source)
    source_z = scaler.transform(source)
    target_z = scaler.transform(target)
    active = np.std(source_z, axis=0) > 1e-12
    source_z = source_z[:, active]
    target_z = target_z[:, active]
    maximum = min(50, source_z.shape[1], source_z.shape[0] - 1)
    pca = PCA(n_components=maximum, svd_solver="randomized", random_state=20260801)
    source_pca = pca.fit_transform(source_z)
    target_pca = pca.transform(target_z)
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    keep = int(np.searchsorted(cumulative, 0.95) + 1)
    keep = max(2, min(keep, maximum))
    return source_pca[:, :keep], target_pca[:, :keep], {
        "active_standardized_dimensions": int(active.sum()),
        "pca_dimensions": keep,
        "variance_explained": float(cumulative[keep - 1]),
    }


def nearest_other_group_distances(matrix: np.ndarray, groups: np.ndarray) -> np.ndarray:
    output = np.empty(len(matrix), dtype=float)
    for group in sorted(set(groups.tolist())):
        query = np.flatnonzero(groups == group)
        reference = np.flatnonzero(groups != group)
        model = NearestNeighbors(n_neighbors=1, algorithm="brute", n_jobs=-1)
        model.fit(matrix[reference])
        distance, _ = model.kneighbors(matrix[query])
        output[query] = distance[:, 0]
    return output


def distance_audit(
    name: str,
    source: np.ndarray,
    target: np.ndarray,
    source_salts: np.ndarray,
) -> tuple[dict, np.ndarray, np.ndarray]:
    source_pca, target_pca, representation = pca_embedding(source, target)
    source_reference = nearest_other_group_distances(source_pca, source_salts)
    model = NearestNeighbors(n_neighbors=1, algorithm="brute", n_jobs=-1)
    model.fit(source_pca)
    target_distance, target_neighbor = model.kneighbors(target_pca)
    target_distance = target_distance[:, 0]
    target_neighbor = target_neighbor[:, 0]
    q95 = float(np.quantile(source_reference, 0.95))
    median = float(np.median(target_distance))
    summary = {
        "representation": name,
        **representation,
        "reference_definition": "source row to nearest row from a different source salt",
        "reference_median_distance": float(np.median(source_reference)),
        "reference_q95_distance": q95,
        "target_median_distance": median,
        "target_q95_distance": float(np.quantile(target_distance, 0.95)),
        "target_median_reference_percentile": empirical_percentile(source_reference, median),
        "target_fraction_within_reference_q95": float(np.mean(target_distance <= q95)),
    }
    return summary, target_distance, target_neighbor


def component_smiles(records: list[dict], component: str) -> set[str]:
    return {
        str(item["smiles"])
        for record in records
        for item in record[component]
    }


def main() -> None:
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if sha256(SOURCE_PATH) != design["sources"]["source_sha256"]:
        raise RuntimeError("Source data hash mismatch")
    if sha256(TARGET_PATH) != design["sources"]["target_sha256"]:
        raise RuntimeError("Target data hash mismatch")

    source_records = conductivity_records(load_json_records(SOURCE_PATH))
    target_archive_records = conductivity_records(load_json_records(TARGET_PATH))
    target_archive_salts = {
        salt_identity(record) for record in target_archive_records
    }
    target_records = [
        record
        for record in target_archive_records
        if salt_identity(record) == "LiAsF6"
    ]
    source_salts = np.asarray([salt_identity(record) for record in source_records])
    target_salts = sorted({salt_identity(record) for record in target_records})
    if target_salts != ["LiAsF6"] or "LiAsF6" in set(source_salts.tolist()):
        raise AssertionError("Salt-identity boundary changed")

    x_source = mixture_features(source_records)
    x_target = mixture_features(target_records)
    state_start = CHEMISTRY_FEATURE_DIM
    salt_start = 2 * MOLECULE_FEATURE_DIM
    salt_end = 3 * MOLECULE_FEATURE_DIM
    environment_source = np.concatenate(
        [x_source[:, :salt_start], x_source[:, state_start:]], axis=1
    )
    environment_target = np.concatenate(
        [x_target[:, :salt_start], x_target[:, state_start:]], axis=1
    )

    full_summary, full_distance, full_neighbor = distance_audit(
        "full_mixture_representation", x_source, x_target, source_salts
    )
    environment_summary, environment_distance, environment_neighbor = distance_audit(
        "solvent_and_state_without_salt_identity",
        environment_source,
        environment_target,
        source_salts,
    )

    source_salt_rows = []
    source_salt_names = []
    for salt in sorted(set(source_salts.tolist())):
        index = int(np.flatnonzero(source_salts == salt)[0])
        source_salt_names.append(salt)
        source_salt_rows.append(x_source[index, salt_start:salt_end])
    source_salt_matrix = np.vstack(source_salt_rows)
    target_salt_vector = x_target[0, salt_start:salt_end][None, :]
    salt_scaler = StandardScaler().fit(source_salt_matrix)
    source_salt_z = salt_scaler.transform(source_salt_matrix)
    target_salt_z = salt_scaler.transform(target_salt_vector)
    active = np.std(source_salt_z, axis=0) > 1e-12
    source_salt_z = source_salt_z[:, active]
    target_salt_z = target_salt_z[:, active]
    salt_model = NearestNeighbors(n_neighbors=2, algorithm="brute").fit(source_salt_z)
    source_salt_distance, _ = salt_model.kneighbors(source_salt_z)
    target_salt_distance, target_salt_neighbor = salt_model.kneighbors(
        target_salt_z, n_neighbors=1
    )
    salt_reference = source_salt_distance[:, 1]
    salt_distance = float(target_salt_distance[0, 0])
    nearest_salt = source_salt_names[int(target_salt_neighbor[0, 0])]

    temperatures_source = np.asarray([float(r["temperature"]) for r in source_records])
    temperatures_target = np.asarray([float(r["temperature"]) for r in target_records])
    concentrations_source = np.asarray([float(r["salt_molar_ratio"]) for r in source_records])
    concentrations_target = np.asarray([float(r["salt_molar_ratio"]) for r in target_records])

    row_frame = pd.DataFrame(
        {
            "target_row": np.arange(len(target_records)),
            "formula_group": [formula_signature(record) for record in target_records],
            "temperature_C": temperatures_target,
            "salt_molar_ratio": concentrations_target,
            "full_representation_distance": full_distance,
            "full_nearest_source_salt": source_salts[full_neighbor],
            "environment_distance": environment_distance,
            "environment_nearest_source_salt": source_salts[environment_neighbor],
        }
    )
    row_frame.to_csv(ROWS_PATH, index=False)

    source_solvents = component_smiles(source_records, "solvents")
    target_solvents = component_smiles(target_records, "solvents")
    summary = {
        "status": "complete-post-outcome-descriptive-applicability-audit",
        "claim_guard": (
            "Recipient outcomes were already public. Outcome values only reproduce the frozen "
            "eligibility filter and are not used in features, distances, thresholds, or interpretation. "
            "This audit quantifies representation support but cannot establish confirmatory transfer."
        ),
        "source_sha256": sha256(SOURCE_PATH),
        "target_sha256": sha256(TARGET_PATH),
        "source_rows": len(source_records),
        "target_rows": len(target_records),
        "target_archive_rows": len(target_archive_records),
        "target_archive_salts": sorted(target_archive_salts),
        "source_salts": len(set(source_salts.tolist())),
        "target_exact_formulations": len(set(row_frame["formula_group"])),
        "identity_boundary": {
            "target_salt_absent_from_source": True,
            "target_salt": "LiAsF6",
        },
        "full_representation": full_summary,
        "environment_without_salt_identity": environment_summary,
        "salt_descriptor": {
            "active_standardized_dimensions": int(active.sum()),
            "nearest_source_salt": nearest_salt,
            "target_nearest_distance": salt_distance,
            "source_leave_one_salt_out_median_distance": float(np.median(salt_reference)),
            "source_leave_one_salt_out_q95_distance": float(np.quantile(salt_reference, 0.95)),
            "target_distance_reference_percentile": empirical_percentile(
                salt_reference, salt_distance
            ),
        },
        "explicit_state_support": {
            "temperature_C": {
                "source_range": [float(temperatures_source.min()), float(temperatures_source.max())],
                "target_range": [float(temperatures_target.min()), float(temperatures_target.max())],
                "target_fraction_inside_source_range": float(
                    np.mean(
                        (temperatures_target >= temperatures_source.min())
                        & (temperatures_target <= temperatures_source.max())
                    )
                ),
            },
            "salt_molar_ratio": {
                "source_range": [float(concentrations_source.min()), float(concentrations_source.max())],
                "target_range": [float(concentrations_target.min()), float(concentrations_target.max())],
                "target_fraction_inside_source_range": float(
                    np.mean(
                        (concentrations_target >= concentrations_source.min())
                        & (concentrations_target <= concentrations_source.max())
                    )
                ),
            },
            "source_unique_solvent_smiles": len(source_solvents),
            "target_unique_solvent_smiles": len(target_solvents),
            "target_solvent_identity_fraction_seen_in_source": float(
                len(target_solvents & source_solvents) / max(1, len(target_solvents))
            ),
        },
        "distance_rows_sha256": sha256(ROWS_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
