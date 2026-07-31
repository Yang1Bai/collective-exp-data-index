"""Build source-only state-matched optical features without recipient outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
import sklearn
from joblib import Parallel, delayed
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

import prepare_optical_photocatalysis_donor_features as base

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_transfer_method_discovery_config.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
SOURCE_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "DB for chromophore_Sci_Data_rev02.csv"
)
BASE_SOURCE_SCRIPT = (
    HERE / "prepare_optical_photocatalysis_donor_features.py"
)
FEATURE_PATH = (
    HERE / "results" / "optical_state_matched_donor_features.csv"
)
OOF_PATH = (
    HERE / "results" / "optical_state_matched_donor_oof_predictions.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_state_matched_donor_summary.json"
)

SEED = 20260726
RDLogger.DisableLog("rdApp.error")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_model(settings: dict[str, object], seed: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=int(settings["n_estimators"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        max_features=float(settings["max_features"]),
        random_state=seed,
        n_jobs=1,
    )


def fit_property(
    scope_index: int,
    property_index: int,
    scope_name: str,
    property_name: str,
    slug: str,
    scope_rows: pd.DataFrame,
    target_x: np.ndarray,
    settings: dict[str, object],
) -> dict[str, object]:
    grouped = (
        scope_rows.loc[
            scope_rows[property_name].notna(),
            ["canonical_smiles", property_name],
        ]
        .groupby("canonical_smiles", as_index=False)[property_name]
        .median()
        .sort_values("canonical_smiles")
        .reset_index(drop=True)
    )
    molecules = grouped["canonical_smiles"].map(Chem.MolFromSmiles)
    groups = np.asarray(
        [
            base.scaffold_key(molecule, smiles)
            for molecule, smiles in zip(
                molecules, grouped["canonical_smiles"], strict=True
            )
        ],
        dtype=object,
    )
    n_molecules = int(len(grouped))
    n_scaffolds = int(len(set(groups.astype(str))))
    gate = settings["property_gate"]
    minimum = int(gate["minimum_unique_molecules"])
    if n_molecules < minimum or n_scaffolds < int(settings["folds"]):
        return {
            "scope": scope_name,
            "property": property_name,
            "slug": slug,
            "status": "size-gate-failed",
            "unique_molecules": n_molecules,
            "unique_scaffolds": n_scaffolds,
            "admitted": False,
            "prediction": None,
            "uncertainty": None,
            "oof": None,
        }

    x = base.feature_matrix(list(molecules))
    y = grouped[property_name].to_numpy(float)
    splitter = GroupKFold(
        n_splits=int(settings["folds"]),
        shuffle=True,
        random_state=SEED + 100 * scope_index + property_index,
    )
    oof = np.full(len(y), np.nan)
    folds = np.full(len(y), -1, dtype=int)
    for fold, (train_index, test_index) in enumerate(
        splitter.split(x, y, groups)
    ):
        estimator = source_model(
            settings,
            SEED
            + 100000 * scope_index
            + 1000 * property_index
            + fold,
        )
        estimator.fit(x[train_index], y[train_index])
        oof[test_index] = estimator.predict(x[test_index])
        folds[test_index] = fold
    if not np.isfinite(oof).all():
        raise RuntimeError(f"Incomplete OOF predictions for {scope_name}/{property_name}")

    r2 = float(r2_score(y, oof))
    spearman = float(stats.spearmanr(y, oof).statistic)
    ci = base.bootstrap_spearman_lower(
        y,
        oof,
        groups,
        SEED + 1000000 + 100 * scope_index + property_index,
    )
    admitted = bool(
        r2 > float(gate["oof_r2_greater_than"])
        and spearman > float(gate["oof_spearman_greater_than"])
        and ci[0]
        > float(gate["bootstrap_95pct_lower_spearman_greater_than"])
    )

    final_estimator = source_model(
        settings, SEED + 2000000 + 100 * scope_index + property_index
    )
    final_estimator.fit(x, y)
    prediction = final_estimator.predict(target_x)
    tree_predictions = np.vstack(
        [tree.predict(target_x) for tree in final_estimator.estimators_]
    )
    uncertainty = tree_predictions.std(axis=0, ddof=1)
    oof_frame = pd.DataFrame(
        {
            "scope": scope_name,
            "property": property_name,
            "canonical_smiles": grouped["canonical_smiles"].astype(str),
            "scaffold": groups.astype(str),
            "fold": folds,
            "observed": y,
            "predicted": oof,
        }
    )
    return {
        "scope": scope_name,
        "property": property_name,
        "slug": slug,
        "status": "modeled",
        "unique_molecules": n_molecules,
        "unique_scaffolds": n_scaffolds,
        "oof_r2": r2,
        "oof_spearman": spearman,
        "scaffold_bootstrap_spearman_ci95": list(ci),
        "admitted": admitted,
        "prediction": prediction,
        "uncertainty": uncertainty,
        "oof": oof_frame,
    }


def scope_support(
    target_molecules: list[Chem.Mol],
    source_molecules: list[Chem.Mol],
) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    source_fingerprints = [
        generator.GetFingerprint(molecule) for molecule in source_molecules
    ]
    output = np.zeros(len(target_molecules), dtype=float)
    for row, molecule in enumerate(target_molecules):
        target_fingerprint = generator.GetFingerprint(molecule)
        similarities = DataStructs.BulkTanimotoSimilarity(
            target_fingerprint, source_fingerprints
        )
        output[row] = max(similarities) if similarities else 0.0
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1)
    arguments = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Design changed after pair audit")
    if audit["recipient"]["metadata_sha256"] != file_hash(METADATA_PATH):
        raise RuntimeError("Target metadata changed after pair audit")
    if design["source"]["required_sha256"] != file_hash(SOURCE_PATH):
        raise RuntimeError("Donor file changed")

    metadata = pd.read_csv(METADATA_PATH)
    recipient_smiles = set(metadata["canonical_smiles"].astype(str))
    target_molecules = [
        Chem.MolFromSmiles(smiles)
        for smiles in metadata["canonical_smiles"].astype(str)
    ]
    if any(molecule is None for molecule in target_molecules):
        raise RuntimeError("Audited target structure no longer parses")
    target_x = base.feature_matrix(target_molecules)

    raw = pd.read_csv(
        SOURCE_PATH,
        usecols=["Chromophore", "Solvent", *base.PROPERTY_SLUGS],
    )
    parsed = raw["Chromophore"].map(base.canonicalize)
    raw["canonical_smiles"] = parsed.map(lambda value: value[0])
    raw["_molecule"] = parsed.map(lambda value: value[1])
    raw = raw[
        raw["canonical_smiles"].notna()
        & ~raw["canonical_smiles"].isin(recipient_smiles)
    ].copy()
    for property_name in base.PROPERTY_SLUGS:
        raw[property_name] = base.transform_property(
            property_name, raw[property_name]
        )
    solvent = raw["Solvent"].fillna("").astype(str).str.strip()
    chromophore = raw["Chromophore"].fillna("").astype(str).str.strip()
    scope_definitions = config["source_state_scopes"]
    masks = {
        "water_methanol": solvent.isin(
            scope_definitions["water_methanol"]["solvent_tokens"]
        ),
        "aqueous_small_alcohol": solvent.isin(
            scope_definitions["aqueous_small_alcohol"]["solvent_tokens"]
        ),
        "self_host_solid": solvent.eq(chromophore),
    }

    feature_output = metadata[
        [
            "target_key",
            "ID",
            "split",
            "canonical_smiles",
            "scaffold",
            "max_similarity_to_development",
            "hard_ood_40pct",
            "hard_ood_25pct",
        ]
    ].copy()
    scope_counts: dict[str, dict[str, int]] = {}
    tasks = []
    settings = config["source_modeling"]
    for scope_index, (scope_name, mask) in enumerate(masks.items()):
        rows = raw.loc[mask].copy()
        unique_rows = rows.drop_duplicates("canonical_smiles")
        feature_output[f"support_{scope_name}"] = scope_support(
            target_molecules, list(unique_rows["_molecule"])
        )
        scope_counts[scope_name] = {
            "rows": int(len(rows)),
            "unique_molecules": int(rows["canonical_smiles"].nunique()),
        }
        for property_index, (property_name, slug) in enumerate(
            base.PROPERTY_SLUGS.items()
        ):
            tasks.append(
                (
                    scope_index,
                    property_index,
                    scope_name,
                    property_name,
                    slug,
                    rows,
                )
            )

    results = Parallel(n_jobs=arguments.jobs, verbose=10)(
        delayed(fit_property)(
            scope_index,
            property_index,
            scope_name,
            property_name,
            slug,
            rows,
            target_x,
            settings,
        )
        for (
            scope_index,
            property_index,
            scope_name,
            property_name,
            slug,
            rows,
        ) in tasks
    )

    summaries: dict[str, dict[str, object]] = {
        scope_name: {} for scope_name in masks
    }
    admitted_columns: dict[str, list[str]] = {
        scope_name: [] for scope_name in masks
    }
    oof_frames: list[pd.DataFrame] = []
    for result in results:
        scope_name = str(result["scope"])
        property_name = str(result["property"])
        slug = str(result["slug"])
        summary_item = {
            key: value
            for key, value in result.items()
            if key not in {"prediction", "uncertainty", "oof"}
        }
        summaries[scope_name][property_name] = summary_item
        if result["prediction"] is not None:
            prediction_column = f"pred_{scope_name}_{slug}"
            uncertainty_column = f"unc_{scope_name}_{slug}"
            feature_output[prediction_column] = result["prediction"]
            feature_output[uncertainty_column] = result["uncertainty"]
            if bool(result["admitted"]):
                admitted_columns[scope_name].extend(
                    [prediction_column, uncertainty_column]
                )
        if result["oof"] is not None:
            oof_frames.append(result["oof"])

    feature_output.to_csv(FEATURE_PATH, index=False, lineterminator="\n")
    pd.concat(oof_frames, ignore_index=True).to_csv(
        OOF_PATH, index=False, lineterminator="\n"
    )
    summary = {
        "status": "state-source-features-ready",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "source_sha256": file_hash(SOURCE_PATH),
        "implementation_sha256": file_hash(Path(__file__)),
        "scope_counts": scope_counts,
        "properties": summaries,
        "admitted_feature_columns_by_scope": admitted_columns,
        "feature_sha256": file_hash(FEATURE_PATH),
        "oof_sha256": file_hash(OOF_PATH),
        "feature_rows": int(len(feature_output)),
        "outcome_access": (
            "Only donor optical outcomes and outcome-free recipient structures "
            "were loaded; recipient HER values were not accessed."
        ),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "rdkit": rdkit.__version__,
        },
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
