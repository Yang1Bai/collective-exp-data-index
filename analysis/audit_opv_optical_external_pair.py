"""Outcome-free audit for experimental optical knowledge borrowing into OPV.

The target CSV physically contains photovoltaic outcomes, but this script
requests only identity, structure, provenance, and device-state columns.  It
must run before any row-level target outcome is opened by the analysis code.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import rdFingerprintGenerator

import prepare_optical_photocatalysis_donor_features as optical


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TARGET_ZIP = ROOT / "data" / "external" / "opv_borrowing" / "opvdb.zip"
TARGET_MEMBER = "data/opv_devices_strict_molecular_benchmark.csv"
SOURCE_CSV = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "DB for chromophore_Sci_Data_rev02.csv"
)
RESULTS = HERE / "results"
METADATA_CSV = RESULTS / "opv_optical_target_metadata_no_outcomes.csv"
AUDIT_JSON = RESULTS / "opv_optical_external_pair_audit.json"

ALLOWED_TARGET_COLUMNS = [
    "id",
    "doi",
    "doi_norm",
    "donor",
    "acceptor",
    "donor_canonical",
    "acceptor_canonical",
    "donor_smiles",
    "acceptor_smiles",
    "d_a_ratio",
    "additive",
    "additive_canonical",
    "additive_ratio",
    "device_structure",
    "device_type",
    "etl",
    "etl_canonical",
    "htl",
    "htl_canonical",
    "active_layer_thickness",
    "solvent",
    "solvent_canonical",
    "annealing_temp",
]
FORBIDDEN_TARGET_COLUMNS = {
    "voc",
    "jsc",
    "ff",
    "pce",
    "pce_recomputed",
    "pce_relative_error_percent",
    "pce_avg",
    "pce_best",
    "homo_d",
    "lumo_d",
    "eg_d",
    "homo_a",
    "lumo_a",
    "eg_a",
}

RDLogger.DisableLog("rdApp.error")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def portable_zip_member(archive: zipfile.ZipFile, expected: str) -> str:
    """Resolve ZIP members created with either POSIX or Windows separators."""
    matches = {
        name.replace("\\", "/"): name for name in archive.namelist()
    }
    try:
        return matches[expected.replace("\\", "/")]
    except KeyError as error:
        raise KeyError(
            f"ZIP member {expected!r} was not found after path normalization"
        ) from error


def normalize_doi(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().rstrip(".,;")


def canonicalize_series(values: pd.Series) -> tuple[list[str], list[Chem.Mol | None]]:
    canonical: list[str] = []
    molecules: list[Chem.Mol | None] = []
    for value in values:
        smiles, molecule = optical.canonicalize(value)
        canonical.append(smiles or "")
        molecules.append(molecule)
    return canonical, molecules


def source_scope(
    raw: pd.DataFrame, scope: str
) -> tuple[list[str], list[Chem.Mol], set[str]]:
    canonical, molecules = canonicalize_series(raw["Chromophore"])
    solvent_canonical, _ = canonicalize_series(raw["Solvent"])
    frame = pd.DataFrame(
        {
            "canonical_smiles": canonical,
            "solvent_canonical": solvent_canonical,
            "reference_doi": raw["Reference"].map(normalize_doi),
        }
    )
    frame = frame[frame["canonical_smiles"].ne("")].copy()
    if scope == "self_host_solid":
        frame = frame[
            frame["canonical_smiles"].eq(frame["solvent_canonical"])
        ].copy()
    elif scope != "global":
        raise ValueError(scope)
    unique = frame.drop_duplicates("canonical_smiles")
    scope_molecules = [
        Chem.MolFromSmiles(value)
        for value in unique["canonical_smiles"].astype(str)
    ]
    if any(molecule is None for molecule in scope_molecules):
        raise AssertionError("Canonical source structure stopped parsing")
    return (
        unique["canonical_smiles"].astype(str).tolist(),
        scope_molecules,  # type: ignore[arg-type]
        set(frame["reference_doi"].astype(str)) - {""},
    )


def max_similarity(
    target_smiles: list[str],
    source_smiles: list[str],
    excluded: set[str],
) -> dict[str, float]:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    retained = [value for value in source_smiles if value not in excluded]
    source_fingerprints = [
        generator.GetFingerprint(Chem.MolFromSmiles(value))  # type: ignore[arg-type]
        for value in retained
    ]
    output: dict[str, float] = {}
    for smiles in sorted(set(target_smiles)):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            output[smiles] = float("nan")
            continue
        fingerprint = generator.GetFingerprint(molecule)
        similarities = DataStructs.BulkTanimotoSimilarity(
            fingerprint, source_fingerprints
        )
        output[smiles] = float(max(similarities)) if similarities else 0.0
    return output


def distribution(values: pd.Series) -> dict[str, float]:
    numeric = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    if not len(numeric):
        return {}
    return {
        "min": float(np.min(numeric)),
        "q10": float(np.quantile(numeric, 0.10)),
        "q25": float(np.quantile(numeric, 0.25)),
        "median": float(np.median(numeric)),
        "q75": float(np.quantile(numeric, 0.75)),
        "q90": float(np.quantile(numeric, 0.90)),
        "max": float(np.max(numeric)),
    }


def main() -> None:
    if not TARGET_ZIP.exists() or not SOURCE_CSV.exists():
        raise FileNotFoundError("Required target or source file is missing")
    with zipfile.ZipFile(TARGET_ZIP) as archive:
        target_member = portable_zip_member(archive, TARGET_MEMBER)
        header = pd.read_csv(archive.open(target_member), nrows=0)
        if not set(ALLOWED_TARGET_COLUMNS).issubset(header.columns):
            missing = sorted(set(ALLOWED_TARGET_COLUMNS) - set(header.columns))
            raise AssertionError(f"Target metadata columns missing: {missing}")
        target = pd.read_csv(
            archive.open(target_member),
            usecols=ALLOWED_TARGET_COLUMNS,
            dtype={"id": "string", "doi": "string", "doi_norm": "string"},
            low_memory=False,
        )
    if FORBIDDEN_TARGET_COLUMNS.intersection(target.columns):
        raise AssertionError("A target outcome column entered the audit")
    if len(target) != 21_720:
        raise AssertionError(f"Unexpected strict molecular rows: {len(target)}")

    donor_canonical, donor_molecules = canonicalize_series(
        target["donor_smiles"]
    )
    acceptor_canonical, acceptor_molecules = canonicalize_series(
        target["acceptor_smiles"]
    )
    target["donor_smiles_canonical"] = donor_canonical
    target["acceptor_smiles_canonical"] = acceptor_canonical
    target["doi_normalized_audit"] = target["doi_norm"].fillna(
        target["doi"]
    ).map(normalize_doi)
    target["donor_scaffold"] = [
        optical.scaffold_key(molecule, smiles) if molecule is not None else ""
        for smiles, molecule in zip(
            donor_canonical, donor_molecules, strict=True
        )
    ]
    target["acceptor_scaffold"] = [
        optical.scaffold_key(molecule, smiles) if molecule is not None else ""
        for smiles, molecule in zip(
            acceptor_canonical, acceptor_molecules, strict=True
        )
    ]
    target["pair_key"] = (
        target["donor_smiles_canonical"]
        + "||"
        + target["acceptor_smiles_canonical"]
    )
    target["doi_pair_key"] = (
        target["doi_normalized_audit"] + "||" + target["pair_key"]
    )

    valid = target["donor_smiles_canonical"].ne("") & target[
        "acceptor_smiles_canonical"
    ].ne("")
    target_molecules = set(
        target.loc[valid, "donor_smiles_canonical"].astype(str)
    ) | set(target.loc[valid, "acceptor_smiles_canonical"].astype(str))
    target_dois = set(target["doi_normalized_audit"].astype(str)) - {""}

    source = pd.read_csv(SOURCE_CSV, low_memory=False)
    global_smiles, _, global_dois = source_scope(source, "global")
    solid_smiles, _, solid_dois = source_scope(source, "self_host_solid")

    global_exact = target_molecules.intersection(global_smiles)
    solid_exact = target_molecules.intersection(solid_smiles)
    global_doi_overlap = target_dois.intersection(global_dois)
    solid_doi_overlap = target_dois.intersection(solid_dois)

    global_support = max_similarity(
        sorted(target_molecules), global_smiles, target_molecules
    )
    solid_support = max_similarity(
        sorted(target_molecules), solid_smiles, target_molecules
    )
    for role in ("donor", "acceptor"):
        smiles_column = f"{role}_smiles_canonical"
        target[f"{role}_global_source_support"] = target[smiles_column].map(
            global_support
        )
        target[f"{role}_solid_source_support"] = target[smiles_column].map(
            solid_support
        )
    target["pair_global_source_support"] = np.sqrt(
        target["donor_global_source_support"].clip(lower=0)
        * target["acceptor_global_source_support"].clip(lower=0)
    )
    target["pair_solid_source_support"] = np.sqrt(
        target["donor_solid_source_support"].clip(lower=0)
        * target["acceptor_solid_source_support"].clip(lower=0)
    )
    target["external_doi_holdout"] = target["doi_normalized_audit"].map(
        lambda value: int(
            hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8], 16
        )
        % 5
        == 0
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    target.to_csv(METADATA_CSV, index=False, lineterminator="\n")
    audit = {
        "status": "metadata-audited-row-outcomes-unopened",
        "target": {
            "dataset": "OPV-DB strict molecular benchmark",
            "doi": "10.5281/zenodo.20841543",
            "zip_sha256": sha256(TARGET_ZIP),
            "member": TARGET_MEMBER,
            "rows": int(len(target)),
            "valid_structure_rows": int(valid.sum()),
            "unique_dois": int(target["doi_normalized_audit"].nunique()),
            "unique_donors": int(
                target["donor_smiles_canonical"].replace("", np.nan).nunique()
            ),
            "unique_acceptors": int(
                target["acceptor_smiles_canonical"]
                .replace("", np.nan)
                .nunique()
            ),
            "unique_pairs": int(target["pair_key"].nunique()),
            "unique_doi_pairs": int(target["doi_pair_key"].nunique()),
            "unique_donor_scaffolds": int(
                target["donor_scaffold"].replace("", np.nan).nunique()
            ),
            "unique_acceptor_scaffolds": int(
                target["acceptor_scaffold"].replace("", np.nan).nunique()
            ),
            "external_holdout_rows": int(
                target["external_doi_holdout"].sum()
            ),
            "external_holdout_dois": int(
                target.loc[
                    target["external_doi_holdout"], "doi_normalized_audit"
                ].nunique()
            ),
            "state_coverage_percent": {
                column: float(100.0 * target[column].notna().mean())
                for column in (
                    "device_structure",
                    "device_type",
                    "etl",
                    "htl",
                    "solvent",
                    "additive",
                    "d_a_ratio",
                    "active_layer_thickness",
                    "annealing_temp",
                )
            },
        },
        "source": {
            "dataset": "Deep4Chem experimental optical properties",
            "doi": "10.6084/m9.figshare.12045567.v2",
            "csv_sha256": sha256(SOURCE_CSV),
            "global_unique_molecules": int(len(global_smiles)),
            "solid_unique_molecules": int(len(solid_smiles)),
            "exact_target_molecule_overlap_global": int(len(global_exact)),
            "exact_target_molecule_overlap_solid": int(len(solid_exact)),
            "target_doi_overlap_global": int(len(global_doi_overlap)),
            "target_doi_overlap_solid": int(len(solid_doi_overlap)),
            "strict_source_policy": (
                "Retrain after excluding every exact target molecule and every "
                "target DOI; exact-overlap models are lookup upper bounds only."
            ),
        },
        "support_after_exact_target_exclusion": {
            "donor_global": distribution(
                target["donor_global_source_support"]
            ),
            "acceptor_global": distribution(
                target["acceptor_global_source_support"]
            ),
            "pair_global": distribution(target["pair_global_source_support"]),
            "donor_solid": distribution(
                target["donor_solid_source_support"]
            ),
            "acceptor_solid": distribution(
                target["acceptor_solid_source_support"]
            ),
            "pair_solid": distribution(target["pair_solid_source_support"]),
            "row_coverage_counts": {
                f"pair_global_ge_{threshold:.2f}": int(
                    (target["pair_global_source_support"] >= threshold).sum()
                )
                for threshold in (0.20, 0.25, 0.30, 0.35, 0.40)
            }
            | {
                f"pair_solid_ge_{threshold:.2f}": int(
                    (target["pair_solid_source_support"] >= threshold).sum()
                )
                for threshold in (0.20, 0.25, 0.30, 0.35, 0.40)
            },
        },
        "outcome_sentinel": {
            "allowed_columns_read": ALLOWED_TARGET_COLUMNS,
            "forbidden_columns_not_read": sorted(FORBIDDEN_TARGET_COLUMNS),
            "metadata_csv": str(METADATA_CSV.relative_to(ROOT)),
            "metadata_sha256": sha256(METADATA_CSV),
        },
        "environment": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "rdkit": rdBase.rdkitVersion,
        },
    }
    AUDIT_JSON.write_text(
        json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
