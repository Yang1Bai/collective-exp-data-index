"""Fit donor-only optical models and create outcome-free recipient features."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
import sklearn
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
SOURCE_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "DB for chromophore_Sci_Data_rev02.csv"
)
SUMMARY_PATH = HERE / "results" / "optical_photocatalysis_source_skill.json"
FEATURE_PATH = HERE / "results" / "optical_photocatalysis_donor_features.csv"
OOF_PATH = HERE / "results" / "optical_photocatalysis_donor_oof_predictions.csv"

SEED = 20260724
N_ESTIMATORS = 300
N_BOOTSTRAP = 1000
PROPERTY_SLUGS = {
    "Absorption max (nm)": "absorption_nm",
    "Emission max (nm)": "emission_nm",
    "Lifetime (ns)": "log1p_lifetime_ns",
    "Quantum yield": "quantum_yield",
    "log(e/mol-1 dm3 cm-1)": "log_extinction",
}

RDLogger.DisableLog("rdApp.error")


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def canonicalize(smiles: object) -> tuple[str | None, Chem.Mol | None]:
    if pd.isna(smiles):
        return None, None
    molecule = Chem.MolFromSmiles(str(smiles).strip())
    if molecule is None:
        return None, None
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True), molecule


def scaffold_key(molecule: Chem.Mol, canonical_smiles: str) -> str:
    scaffold = MurckoScaffold.GetScaffoldForMol(molecule)
    if scaffold.GetNumAtoms() == 0:
        return "acyclic-" + stable_hash(canonical_smiles)
    return "murcko-" + Chem.MolToSmiles(
        scaffold, canonical=True, isomericSmiles=True
    )


def feature_matrix(molecules: list[Chem.Mol]) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2,
        fpSize=2048,
        includeChirality=True,
    )
    output = np.zeros((len(molecules), 2048), dtype=np.uint8)
    for row, molecule in enumerate(molecules):
        bits = generator.GetFingerprintAsNumPy(molecule)
        output[row] = bits.astype(np.uint8, copy=False)
    return output


def transform_property(name: str, values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    if name == "Lifetime (ns)":
        numeric = numeric.where(numeric >= 0)
        return np.log1p(numeric)
    if name == "Quantum yield":
        return numeric.where((numeric >= 0) & (numeric <= 1))
    if name in {"Absorption max (nm)", "Emission max (nm)"}:
        return numeric.where((numeric >= 150) & (numeric <= 1200))
    if name == "log(e/mol-1 dm3 cm-1)":
        return numeric.where((numeric >= 0) & (numeric <= 10))
    return numeric


def donor_model(seed: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=N_ESTIMATORS,
        min_samples_leaf=2,
        max_features=0.5,
        random_state=seed,
        n_jobs=-1,
    )


def bootstrap_spearman_lower(
    truth: np.ndarray,
    prediction: np.ndarray,
    groups: np.ndarray,
    seed: int,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    unique_groups = np.asarray(sorted(set(groups.astype(str))))
    group_rows = {
        group: np.flatnonzero(groups.astype(str) == group) for group in unique_groups
    }
    estimates = np.full(N_BOOTSTRAP, np.nan)
    for repeat in range(N_BOOTSTRAP):
        sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        indices = np.concatenate([group_rows[group] for group in sampled])
        estimate = stats.spearmanr(truth[indices], prediction[indices]).statistic
        if np.isfinite(estimate):
            estimates[repeat] = estimate
    finite = estimates[np.isfinite(estimates)]
    if not len(finite):
        return float("nan"), float("nan"), float("nan")
    low, median, high = np.quantile(finite, [0.025, 0.5, 0.975])
    return float(low), float(median), float(high)


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["status"] != "schema-and-coverage-valid":
        raise RuntimeError("Pair audit is not valid")
    current_design_hash = file_hash(DESIGN_PATH)
    if current_design_hash != audit["design_sha256"]:
        raise RuntimeError("Design changed after the schema/coverage audit")
    if file_hash(METADATA_PATH) != audit["recipient"]["metadata_sha256"]:
        raise RuntimeError("Outcome-free target metadata changed after audit")
    if file_hash(SOURCE_PATH) != design["source"]["required_sha256"]:
        raise RuntimeError("Donor file hash changed")

    metadata = pd.read_csv(METADATA_PATH)
    recipient_smiles = set(metadata["canonical_smiles"])
    target_molecules = []
    for smiles in metadata["canonical_smiles"]:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited target SMILES no longer parses: {smiles}")
        target_molecules.append(molecule)
    target_x = feature_matrix(target_molecules)

    donor_raw = pd.read_csv(
        SOURCE_PATH,
        usecols=["Chromophore", *PROPERTY_SLUGS],
    )
    parsed = donor_raw["Chromophore"].map(canonicalize)
    donor_raw["canonical_smiles"] = parsed.map(lambda item: item[0])
    donor_raw["_molecule"] = parsed.map(lambda item: item[1])
    donor_raw = donor_raw[
        donor_raw["canonical_smiles"].notna()
        & ~donor_raw["canonical_smiles"].isin(recipient_smiles)
    ].copy()

    for property_name in PROPERTY_SLUGS:
        donor_raw[property_name] = transform_property(
            property_name, donor_raw[property_name]
        )

    aggregation = {
        property_name: (property_name, "median") for property_name in PROPERTY_SLUGS
    }
    donor = (
        donor_raw.groupby("canonical_smiles", as_index=False)
        .agg(**aggregation)
        .sort_values("canonical_smiles")
        .reset_index(drop=True)
    )
    donor["_molecule"] = donor["canonical_smiles"].map(Chem.MolFromSmiles)
    donor["scaffold"] = [
        scaffold_key(molecule, smiles)
        for molecule, smiles in zip(
            donor["_molecule"], donor["canonical_smiles"], strict=True
        )
    ]
    donor_x = feature_matrix(list(donor["_molecule"]))

    gate = design["donor_modeling"]["property_admission_gate"]
    feature_output = metadata[
        [
            "target_key",
            "ID",
            "split",
            "canonical_smiles",
            "scaffold",
            "max_similarity_to_development",
            "max_similarity_to_retained_donor",
            "hard_ood_40pct",
            "hard_ood_25pct",
        ]
    ].copy()
    summaries: dict[str, dict[str, object]] = {}
    oof_frames: list[pd.DataFrame] = []

    for property_index, (property_name, slug) in enumerate(PROPERTY_SLUGS.items()):
        valid = donor[property_name].notna().to_numpy()
        indices = np.flatnonzero(valid)
        x = donor_x[indices]
        y = donor.loc[valid, property_name].to_numpy(dtype=float)
        groups = donor.loc[valid, "scaffold"].astype(str).to_numpy()
        smiles = donor.loc[valid, "canonical_smiles"].astype(str).to_numpy()
        splitter = GroupKFold(n_splits=5, shuffle=True, random_state=SEED + property_index)
        oof = np.full(len(y), np.nan)
        fold_ids = np.full(len(y), -1, dtype=int)
        for fold, (train_index, test_index) in enumerate(splitter.split(x, y, groups)):
            model = donor_model(SEED + 100 * property_index + fold)
            model.fit(x[train_index], y[train_index])
            oof[test_index] = model.predict(x[test_index])
            fold_ids[test_index] = fold
        if not np.isfinite(oof).all():
            raise RuntimeError(f"Incomplete donor OOF predictions: {property_name}")

        oof_r2 = float(r2_score(y, oof))
        oof_spearman = float(stats.spearmanr(y, oof).statistic)
        spearman_ci = bootstrap_spearman_lower(
            y, oof, groups, SEED + 1000 + property_index
        )
        admitted = bool(
            len(y) >= int(gate["minimum_unique_molecules"])
            and oof_r2 > float(gate["oof_r2_greater_than"])
            and oof_spearman > float(gate["oof_spearman_greater_than"])
            and spearman_ci[0]
            > float(gate["bootstrap_95pct_lower_spearman_greater_than"])
        )

        final_model = donor_model(SEED + 10000 + property_index)
        final_model.fit(x, y)
        target_prediction = final_model.predict(target_x)
        tree_predictions = np.vstack(
            [tree.predict(target_x) for tree in final_model.estimators_]
        )
        target_uncertainty = tree_predictions.std(axis=0, ddof=1)
        feature_output[f"pred_{slug}"] = target_prediction
        feature_output[f"unc_{slug}"] = target_uncertainty

        summaries[property_name] = {
            "slug": slug,
            "unique_molecules": int(len(y)),
            "unique_scaffolds": int(len(set(groups))),
            "oof_r2": oof_r2,
            "oof_spearman": oof_spearman,
            "scaffold_bootstrap_spearman_ci95": list(spearman_ci),
            "admitted_by_source_only_gate": admitted,
            "target_prediction_quantiles": {
                key: float(value)
                for key, value in zip(
                    ["min", "q25", "median", "q75", "max"],
                    np.quantile(target_prediction, [0.0, 0.25, 0.5, 0.75, 1.0]),
                    strict=True,
                )
            },
            "target_uncertainty_quantiles": {
                key: float(value)
                for key, value in zip(
                    ["min", "q25", "median", "q75", "max"],
                    np.quantile(target_uncertainty, [0.0, 0.25, 0.5, 0.75, 1.0]),
                    strict=True,
                )
            },
        }
        oof_frames.append(
            pd.DataFrame(
                {
                    "property": property_name,
                    "canonical_smiles": smiles,
                    "scaffold": groups,
                    "fold": fold_ids,
                    "observed": y,
                    "predicted": oof,
                }
            )
        )
        print(
            f"{property_name}: n={len(y)} R2={oof_r2:.4f} "
            f"Spearman={oof_spearman:.4f} CI95=({spearman_ci[0]:.4f},"
            f"{spearman_ci[2]:.4f}) admitted={admitted}",
            flush=True,
        )

    admitted_properties = [
        name
        for name, item in summaries.items()
        if bool(item["admitted_by_source_only_gate"])
    ]
    feature_output.to_csv(FEATURE_PATH, index=False, lineterminator="\n")
    pd.concat(oof_frames, ignore_index=True).to_csv(
        OOF_PATH, index=False, lineterminator="\n"
    )

    summary = {
        "status": "source-features-ready" if admitted_properties else "source-abstained",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": current_design_hash,
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "source_sha256": file_hash(SOURCE_PATH),
        "source_training": {
            "exact_recipient_molecules_excluded": int(
                audit["donor"]["exact_recipient_overlap_molecules"]
            ),
            "retained_unique_molecules": int(len(donor)),
            "model": "ExtraTreesRegressor",
            "n_estimators": N_ESTIMATORS,
            "folds": 5,
            "group": "canonical Bemis-Murcko scaffold",
            "bootstrap_replicates": N_BOOTSTRAP,
        },
        "properties": summaries,
        "admitted_properties": admitted_properties,
        "feature_file": str(FEATURE_PATH.relative_to(ROOT)),
        "feature_sha256": file_hash(FEATURE_PATH),
        "oof_file": str(OOF_PATH.relative_to(ROOT)),
        "oof_sha256": file_hash(OOF_PATH),
        "feature_rows": int(len(feature_output)),
        "outcome_access": (
            "No recipient HER values were loaded. Feature construction used donor optical "
            "outcomes and outcome-free recipient structures only."
        ),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "rdkit": rdkit.__version__,
        },
        "next_gate": (
            "development-only recipient increment at label budget 60; blind HER remains locked"
        ),
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
