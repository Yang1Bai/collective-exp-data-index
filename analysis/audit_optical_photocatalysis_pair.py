"""Fetch and outcome-blindly audit the optical -> photocatalysis database pair.

The script intentionally does not load the recipient HER column.  It verifies
the target schema, structures, fixed split, OOD geometry, and donor coverage,
then writes a no-outcome target metadata table for the frozen retrospective
benchmark.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
RAW_DIR = ROOT / "data" / "external" / "optical_photocatalysis"
RESULTS_DIR = HERE / "results"
AUDIT_PATH = RESULTS_DIR / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = RESULTS_DIR / "optical_photocatalysis_target_metadata.csv"

RDLogger.DisableLog("rdApp.error")


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_text_hash(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "collective-exp-data-index/optical-photocatalysis-audit",
            "Accept": "application/zip,text/csv,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception as first_error:
        curl = shutil.which("curl")
        if curl is None:
            raise RuntimeError(f"Download failed and curl is unavailable: {url}") from first_error
        if partial.exists():
            partial.unlink()
        command = [
            curl,
            "-L",
            "--fail",
            "--retry",
            "4",
            "--retry-all-errors",
            "--connect-timeout",
            "20",
            "--max-time",
            "240",
            "-A",
            "collective-exp-data-index/optical-photocatalysis-audit",
            url,
            "-o",
            str(partial),
        ]
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"Both download paths failed for {url}") from first_error
    if not partial.exists() or partial.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file is empty: {url}")
    partial.replace(output)


def require_hashes(path: Path, expected_md5: str, expected_sha256: str) -> None:
    actual_md5 = file_hash(path, "md5")
    actual_sha256 = file_hash(path, "sha256")
    if actual_md5 != expected_md5:
        raise RuntimeError(f"MD5 mismatch for {path.name}: {actual_md5}")
    if actual_sha256 != expected_sha256:
        raise RuntimeError(f"SHA256 mismatch for {path.name}: {actual_sha256}")


def ensure_source(design: dict[str, object]) -> Path:
    source = design["source"]
    path = RAW_DIR / str(source["file_name"])
    if not path.exists():
        download(str(source["download_url"]), path)
    require_hashes(path, str(source["required_md5"]), str(source["required_sha256"]))
    return path


def ensure_targets(design: dict[str, object]) -> tuple[Path, Path, Path]:
    target = design["target"]
    archive_path = RAW_DIR / "PMC8372320_supplementary_files.zip"
    specs = [target["development_file"], target["blind_file"]]
    extracted = [RAW_DIR / str(spec["name"]) for spec in specs]
    needs_archive = any(not path.exists() for path in extracted)
    if needs_archive:
        download(str(target["supplementary_archive_url"]), archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            available = set(archive.namelist())
            for spec, output in zip(specs, extracted, strict=True):
                name = str(spec["name"])
                if name not in available:
                    raise RuntimeError(f"Target member missing from supplementary archive: {name}")
                with archive.open(name) as source, output.open("wb") as handle:
                    shutil.copyfileobj(source, handle)
    for spec, path in zip(specs, extracted, strict=True):
        require_hashes(path, str(spec["required_md5"]), str(spec["required_sha256"]))
    return extracted[0], extracted[1], archive_path


def canonicalize(value: object) -> tuple[str | None, Chem.Mol | None]:
    if pd.isna(value):
        return None, None
    text = str(value).strip()
    if not text:
        return None, None
    molecule = Chem.MolFromSmiles(text)
    if molecule is None:
        return None, None
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True), molecule


def scaffold_key(molecule: Chem.Mol | None, canonical_smiles: str | None) -> str | None:
    if molecule is None or canonical_smiles is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
    if scaffold.GetNumAtoms() == 0:
        return "acyclic-" + stable_text_hash(canonical_smiles)
    smiles = Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=True)
    return "murcko-" + smiles


def parse_structures(frame: pd.DataFrame, smiles_column: str) -> pd.DataFrame:
    output = frame.copy()
    parsed = output[smiles_column].map(canonicalize)
    output["canonical_smiles"] = parsed.map(lambda item: item[0])
    output["_molecule"] = parsed.map(lambda item: item[1])
    output["scaffold"] = [
        scaffold_key(molecule, smiles)
        for molecule, smiles in zip(output["_molecule"], output["canonical_smiles"], strict=True)
    ]
    return output


def fingerprints(
    molecules: Iterable[Chem.Mol],
) -> list[DataStructs.ExplicitBitVect]:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2,
        fpSize=2048,
        includeChirality=True,
    )
    return [generator.GetFingerprint(molecule) for molecule in molecules]


def maximum_similarities(
    query_fingerprints: list[DataStructs.ExplicitBitVect],
    reference_fingerprints: list[DataStructs.ExplicitBitVect],
) -> np.ndarray:
    if not reference_fingerprints:
        return np.full(len(query_fingerprints), np.nan)
    return np.asarray(
        [
            max(DataStructs.BulkTanimotoSimilarity(query, reference_fingerprints))
            for query in query_fingerprints
        ],
        dtype=float,
    )


def leave_one_out_similarities(
    values: list[DataStructs.ExplicitBitVect],
) -> np.ndarray:
    output = np.full(len(values), np.nan)
    for index, query in enumerate(values):
        references = values[:index] + values[index + 1 :]
        if references:
            output[index] = max(DataStructs.BulkTanimotoSimilarity(query, references))
    return output


def quantiles(values: pd.Series) -> dict[str, float | None]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        return {key: None for key in ("min", "q10", "q25", "median", "q75", "q90", "max")}
    probs = numeric.quantile([0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
    return {
        "min": float(probs.loc[0.0]),
        "q10": float(probs.loc[0.1]),
        "q25": float(probs.loc[0.25]),
        "median": float(probs.loc[0.5]),
        "q75": float(probs.loc[0.75]),
        "q90": float(probs.loc[0.9]),
        "max": float(probs.loc[1.0]),
    }


def deterministic_scope(frame: pd.DataFrame, fraction: float) -> set[str]:
    count = int(math.ceil(fraction * len(frame)))
    ordered = frame.assign(
        _tie=frame["canonical_smiles"].map(stable_text_hash)
    ).sort_values(["max_similarity_to_development", "_tie"], ascending=[True, True])
    return set(ordered.head(count)["target_key"])


def property_profile(
    donor: pd.DataFrame,
    property_columns: list[str],
) -> dict[str, dict[str, int | float]]:
    profile: dict[str, dict[str, int | float]] = {}
    for column in property_columns:
        numeric = pd.to_numeric(donor[column], errors="coerce")
        valid = donor[numeric.notna()].copy()
        profile[column] = {
            "valid_rows": int(numeric.notna().sum()),
            "valid_fraction": float(numeric.notna().mean()),
            "unique_molecules": int(valid["canonical_smiles"].nunique()),
            "unique_scaffolds": int(valid["scaffold"].nunique()),
        }
    return profile


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    source_path = ensure_source(design)
    development_path, blind_path, archive_path = ensure_targets(design)

    target_required = {"ID", "CAS", "SMILES", "HER (µmol/h)"}
    for path in (development_path, blind_path):
        header = set(pd.read_csv(path, nrows=0).columns)
        missing = target_required - header
        if missing:
            raise RuntimeError(f"Missing required target columns in {path.name}: {sorted(missing)}")

    # Deliberately exclude HER from this audit and its derived metadata.
    development = pd.read_csv(development_path, usecols=["ID", "CAS", "SMILES"])
    blind = pd.read_csv(blind_path, usecols=["ID", "CAS", "SMILES"])
    development["split"] = "development"
    blind["split"] = "blind"
    target = pd.concat([development, blind], ignore_index=True)
    target = parse_structures(target, "SMILES")
    target["target_key"] = target.apply(
        lambda row: f"{row['split']}:{row['ID']}", axis=1
    )

    source_columns = [
        "Tag",
        "Chromophore",
        "Solvent",
        *design["source"]["candidate_properties"],
        "Reference",
    ]
    donor = pd.read_csv(source_path, usecols=source_columns)
    donor = parse_structures(donor, "Chromophore")

    valid_target = target[target["canonical_smiles"].notna()].copy()
    valid_donor = donor[donor["canonical_smiles"].notna()].copy()
    target_smiles = set(valid_target["canonical_smiles"])
    donor_smiles = set(valid_donor["canonical_smiles"])
    exact_overlap = target_smiles & donor_smiles
    retained_donor = valid_donor[~valid_donor["canonical_smiles"].isin(target_smiles)].copy()

    target_unique = (
        valid_target.sort_values(["split", "ID"])
        .drop_duplicates(["split", "canonical_smiles"], keep="first")
        .copy()
    )
    within_split_duplicate_rows = {
        split: int(
            frame["canonical_smiles"].notna().sum()
            - frame.loc[frame["canonical_smiles"].notna(), "canonical_smiles"].nunique()
        )
        for split, frame in target.groupby("split")
    }
    development_unique = target_unique[target_unique["split"] == "development"].copy()
    blind_unique = target_unique[target_unique["split"] == "blind"].copy()

    development_fps = fingerprints(list(development_unique["_molecule"]))
    blind_fps = fingerprints(list(blind_unique["_molecule"]))
    retained_donor_unique = (
        retained_donor.drop_duplicates("canonical_smiles")
        .sort_values("canonical_smiles")
        .copy()
    )
    donor_fps = fingerprints(list(retained_donor_unique["_molecule"]))

    development_unique["max_similarity_to_development"] = leave_one_out_similarities(
        development_fps
    )
    blind_unique["max_similarity_to_development"] = maximum_similarities(
        blind_fps, development_fps
    )
    development_unique["max_similarity_to_retained_donor"] = maximum_similarities(
        development_fps, donor_fps
    )
    blind_unique["max_similarity_to_retained_donor"] = maximum_similarities(
        blind_fps, donor_fps
    )
    metadata = pd.concat([development_unique, blind_unique], ignore_index=True)
    metadata["exact_in_raw_donor"] = metadata["canonical_smiles"].isin(exact_overlap)
    hard_40 = deterministic_scope(blind_unique, 0.40)
    hard_25 = deterministic_scope(blind_unique, 0.25)
    metadata["hard_ood_40pct"] = metadata["target_key"].isin(hard_40)
    metadata["hard_ood_25pct"] = metadata["target_key"].isin(hard_25)

    cross_split_overlap = set(development_unique["canonical_smiles"]) & set(
        blind_unique["canonical_smiles"]
    )
    development_scaffolds = set(development_unique["scaffold"].dropna())
    blind_scaffolds = set(blind_unique["scaffold"].dropna())
    invalid_target_fraction = float(target["canonical_smiles"].isna().mean())
    invalid_donor_fraction = float(donor["canonical_smiles"].isna().mean())

    source_properties = property_profile(
        retained_donor,
        list(design["source"]["candidate_properties"]),
    )
    minimum_source_molecules = int(
        design["donor_modeling"]["property_admission_gate"]["minimum_unique_molecules"]
    )
    properties_passing_size = [
        name
        for name, item in source_properties.items()
        if int(item["unique_molecules"]) >= minimum_source_molecules
    ]

    quality = design["outcome_independent_audit"]["minimum_quality"]
    gates = {
        "development_row_count": len(development) == int(quality["development_rows"]),
        "blind_row_count": len(blind) == int(quality["blind_rows"]),
        "target_smiles_validity": invalid_target_fraction
        <= float(quality["maximum_invalid_smiles_fraction"]),
        "cross_split_exact_overlap": len(cross_split_overlap)
        <= int(quality["maximum_cross_split_exact_molecule_overlap"]),
        "retained_donor_size": retained_donor_unique["canonical_smiles"].nunique()
        >= int(quality["minimum_retained_donor_unique_molecules"]),
        "property_size_eligibility": len(properties_passing_size)
        >= int(quality["minimum_admissible_donor_properties"]),
        "primary_ood_size": len(hard_40) >= int(quality["minimum_primary_ood_molecules"]),
    }
    errors = [name for name, passed in gates.items() if not passed]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metadata_output = metadata[
        [
            "target_key",
            "ID",
            "CAS",
            "split",
            "canonical_smiles",
            "scaffold",
            "exact_in_raw_donor",
            "max_similarity_to_development",
            "max_similarity_to_retained_donor",
            "hard_ood_40pct",
            "hard_ood_25pct",
        ]
    ].sort_values(["split", "ID"])
    metadata_output.to_csv(METADATA_PATH, index=False, lineterminator="\n")

    audit = {
        "status": "schema-and-coverage-valid" if not errors else "invalid",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH, "sha256"),
        "outcome_access": (
            "Recipient HER values were not loaded by this audit. Only target IDs, CAS values, "
            "SMILES, split membership, and the existence of the HER column were checked."
        ),
        "input_files": {
            "donor": {
                "path": str(source_path.relative_to(ROOT)),
                "md5": file_hash(source_path, "md5"),
                "sha256": file_hash(source_path, "sha256"),
                "bytes": source_path.stat().st_size,
            },
            "target_development": {
                "path": str(development_path.relative_to(ROOT)),
                "md5": file_hash(development_path, "md5"),
                "sha256": file_hash(development_path, "sha256"),
                "bytes": development_path.stat().st_size,
            },
            "target_blind": {
                "path": str(blind_path.relative_to(ROOT)),
                "md5": file_hash(blind_path, "md5"),
                "sha256": file_hash(blind_path, "sha256"),
                "bytes": blind_path.stat().st_size,
            },
            "target_supplementary_archive": {
                "path": str(archive_path.relative_to(ROOT)),
                "sha256": file_hash(archive_path, "sha256"),
                "bytes": archive_path.stat().st_size,
                "note": "Archive hash is recorded but only the frozen member-file hashes are normative.",
            },
        },
        "dataset_and_grain": {
            "donor": design["source"]["declared_grain"],
            "recipient": design["target"]["declared_grain"],
        },
        "donor": {
            "rows": int(len(donor)),
            "valid_structure_rows": int(donor["canonical_smiles"].notna().sum()),
            "invalid_structure_fraction": invalid_donor_fraction,
            "unique_molecules": int(valid_donor["canonical_smiles"].nunique()),
            "unique_scaffolds": int(valid_donor["scaffold"].nunique()),
            "exact_recipient_overlap_molecules": int(len(exact_overlap)),
            "exact_recipient_overlap_rows": int(
                valid_donor["canonical_smiles"].isin(target_smiles).sum()
            ),
            "retained_rows_after_exact_exclusion": int(len(retained_donor)),
            "retained_unique_molecules": int(retained_donor_unique["canonical_smiles"].nunique()),
            "retained_unique_scaffolds": int(retained_donor_unique["scaffold"].nunique()),
            "properties_after_exact_exclusion": source_properties,
            "properties_passing_size_gate_only": properties_passing_size,
            "source_skill_gate": "pending donor-only grouped cross-validation",
            "top_solvent_tokens": {
                str(key): int(value)
                for key, value in donor["Solvent"].astype(str).value_counts().head(12).items()
            },
            "solid_state_or_self_host_rows": int(
                (
                    donor["Chromophore"].astype(str).str.strip()
                    == donor["Solvent"].astype(str).str.strip()
                ).sum()
            ),
        },
        "recipient": {
            "raw_rows": {
                "development": int(len(development)),
                "blind": int(len(blind)),
            },
            "valid_structure_rows": {
                "development": int(
                    ((target["split"] == "development") & target["canonical_smiles"].notna()).sum()
                ),
                "blind": int(
                    ((target["split"] == "blind") & target["canonical_smiles"].notna()).sum()
                ),
            },
            "invalid_structure_fraction": invalid_target_fraction,
            "within_split_duplicate_canonical_rows": {
                "development": within_split_duplicate_rows.get("development", 0),
                "blind": within_split_duplicate_rows.get("blind", 0),
            },
            "cross_split_exact_molecule_overlap": int(len(cross_split_overlap)),
            "unique_scaffolds": {
                "development": int(len(development_scaffolds)),
                "blind": int(len(blind_scaffolds)),
                "blind_unseen_in_development": int(len(blind_scaffolds - development_scaffolds)),
            },
            "blind_scaffold_overlap_fraction": float(
                len(blind_scaffolds & development_scaffolds) / len(blind_scaffolds)
                if blind_scaffolds
                else 0.0
            ),
            "blind_max_similarity_to_development": quantiles(
                blind_unique["max_similarity_to_development"]
            ),
            "blind_max_similarity_to_retained_donor": quantiles(
                blind_unique["max_similarity_to_retained_donor"]
            ),
            "development_max_similarity_to_retained_donor": quantiles(
                development_unique["max_similarity_to_retained_donor"]
            ),
            "hard_ood_40pct_molecules": int(len(hard_40)),
            "hard_ood_25pct_molecules": int(len(hard_25)),
            "metadata_rows": int(len(metadata_output)),
            "metadata_sha256": file_hash(METADATA_PATH, "sha256"),
        },
        "gates": gates,
        "errors": errors,
        "warnings": [
            "The benchmark is retrospective because the papers and their published scientific conclusions were inspected before design freeze.",
            "The donor environments do not exactly reproduce the recipient triethylamine-methanol-water suspension; environment-specific models are sensitivities.",
            "A property passing the size gate is not admitted until donor-only scaffold-held-out skill is demonstrated.",
            "Blind outcomes remain locked until development-only source admission and a blind-release manifest are complete.",
        ],
    }
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False))

    if errors:
        raise SystemExit("Optical-photocatalysis schema/coverage audit failed.")


if __name__ == "__main__":
    main()
