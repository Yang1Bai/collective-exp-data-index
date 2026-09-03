"""Pre-model structural audit for the SpecGen derivative OER systems.

The derivative outcomes are already public and aggregate results were reported
in the source article. This audit therefore freezes a retrospective reanalysis,
not a prospective or outcome-blind experiment. It intentionally avoids fitting
any target-outcome model.
"""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Dataset" / "ref6" / "44160_2025_983_MOESM4_ESM.zip"
MEMBERS = {
    "source": "SpecGen/data/data.xlsx",
    "A": "SpecGen/data/transfer_A.xlsx",
    "B": "SpecGen/data/transfer_B.xlsx",
    "C": "SpecGen/data/transfer_C.xlsx",
    "D": "SpecGen/data/transfer_D.xlsx",
}
GROUP_MEANINGS = {
    "source": "terephthalic ligand; Co-Ni-Cu-Mg-Cd-Zn",
    "A": "2-aminoterephthalic ligand; Co-Ni-Cu-Mg-Cd-Zn",
    "B": "1,3,5-benzenetricarboxylic ligand; Co-Ni-Cu-Mg-Cd-Zn",
    "C": "terephthalic ligand; Co-Ni-Cu-Fe-Cd-Zn",
    "D": "terephthalic ligand; Co-Ni-Cu-Mg-Mn-Zn",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_member(payload: bytes) -> dict[str, pd.DataFrame]:
    book = pd.ExcelFile(BytesIO(payload))
    frames: dict[str, pd.DataFrame] = {}
    for sheet in ("UV", "metals", "overpotential"):
        frames[sheet] = pd.read_excel(
            BytesIO(payload), sheet_name=sheet, header=0
        )
    return frames


def numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    converted = frame.apply(pd.to_numeric, errors="coerce")
    if converted.isna().any().any():
        raise AssertionError("Non-numeric values found in a required matrix")
    return converted


def main() -> None:
    with ZipFile(ARCHIVE) as archive:
        payloads = {key: archive.read(member) for key, member in MEMBERS.items()}

    data = {key: read_member(payload) for key, payload in payloads.items()}
    source_uv = numeric_frame(data["source"]["UV"])
    scaler = StandardScaler().fit(source_uv)
    source_scaled = scaler.transform(source_uv)
    pca = PCA(n_components=0.995, svd_solver="full").fit(source_scaled)
    source_scores = pca.transform(source_scaled)
    source_index = NearestNeighbors(n_neighbors=2).fit(source_scores)
    source_nn = source_index.kneighbors(source_scores)[0][:, 1]
    source_reference_distance = float(
        np.quantile(source_nn, 0.95)
    )

    groups = {}
    for key, frames in data.items():
        uv = numeric_frame(frames["UV"])
        metals = numeric_frame(frames["metals"])
        outcome = numeric_frame(frames["overpotential"])
        if not (len(uv) == len(metals) == len(outcome)):
            raise AssertionError(f"Row misalignment in group {key}")
        if list(uv.columns) != list(source_uv.columns):
            raise AssertionError(f"Wavelength schema mismatch in group {key}")

        scores = pca.transform(scaler.transform(uv))
        nearest = NearestNeighbors(n_neighbors=1).fit(source_scores).kneighbors(
            scores
        )[0][:, 0]
        groups[key] = {
            "meaning": GROUP_MEANINGS[key],
            "rows": int(len(uv)),
            "spectral_features": int(uv.shape[1]),
            "unique_spectra": int(
                uv.round(10).astype(str).agg("|".join, axis=1).nunique()
            ),
            "metal_slots": list(metals.columns),
            "composition_sum_min": float(metals.sum(axis=1).min()),
            "composition_sum_max": float(metals.sum(axis=1).max()),
            "outcome_cells_present": int(outcome.notna().all(axis=1).sum()),
            "source_pca_components_99_5pct": int(pca.n_components_),
            "nearest_source_score_distance": {
                "median": float(np.median(nearest)),
                "q95": float(np.quantile(nearest, 0.95)),
            },
            "fraction_within_source_loo_q95": float(
                np.mean(nearest <= source_reference_distance)
            ),
        }

    output = {
        "status": "eligible-retrospective-pre-model-freeze",
        "created_after_public_aggregate_outcomes_were_known": True,
        "claim_guard": (
            "This is a retrospective system-held-out reanalysis of public data. "
            "It can test whether a frozen source relation ranks derivative-system "
            "OER candidates and whether few target anchors improve transfer. It "
            "cannot establish prospective discovery or independence from the "
            "source study's experimental programme."
        ),
        "archive_sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        "member_sha256": {
            key: sha256_bytes(payload) for key, payload in payloads.items()
        },
        "source_loo_pca_nn_q95": source_reference_distance,
        "groups": groups,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
