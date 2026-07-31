"""Run the development-only recipient gate without loading the blind HER file."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_photocatalysis_development_gate_config.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
SOURCE_SKILL_PATH = HERE / "results" / "optical_photocatalysis_source_skill.json"
DONOR_FEATURE_PATH = (
    HERE / "results" / "optical_photocatalysis_donor_features.csv"
)
DRAW_PATH = HERE / "results" / "optical_photocatalysis_development_draws.csv"
DRAW_MANIFEST_PATH = (
    HERE / "results" / "optical_photocatalysis_development_draws_manifest.json"
)
TARGET_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "SC-012-D1SC02150H-s005.csv"
)
METRICS_PATH = (
    HERE / "results" / "optical_photocatalysis_development_metrics.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_photocatalysis_development_gate.json"
)

SEED = 20260724
PRIMARY_BUDGET = 60
RDLogger.DisableLog("rdApp.error")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def feature_matrix(smiles_values: list[str]) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    output = np.zeros((len(smiles_values), 2048), dtype=np.uint8)
    for row, smiles in enumerate(smiles_values):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited SMILES no longer parses: {smiles}")
        output[row] = generator.GetFingerprintAsNumPy(molecule).astype(
            np.uint8, copy=False
        )
    return output


def impute_from_training(
    training: np.ndarray, evaluation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    training = training.astype(float, copy=True)
    evaluation = evaluation.astype(float, copy=True)
    medians = np.nanmedian(training, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    train_missing = ~np.isfinite(training)
    eval_missing = ~np.isfinite(evaluation)
    if train_missing.any():
        training[train_missing] = np.take(medians, np.where(train_missing)[1])
    if eval_missing.any():
        evaluation[eval_missing] = np.take(medians, np.where(eval_missing)[1])
    return training, evaluation


def rank_from_training(
    training: np.ndarray, evaluation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    train_rank = np.zeros_like(training, dtype=float)
    eval_rank = np.zeros_like(evaluation, dtype=float)
    denominator = float(len(training) + 1)
    for column in range(training.shape[1]):
        ordered = np.sort(training[:, column])
        train_rank[:, column] = (
            np.searchsorted(ordered, training[:, column], side="right")
            / denominator
        )
        eval_rank[:, column] = (
            np.searchsorted(ordered, evaluation[:, column], side="right")
            / denominator
        )
    return train_rank, eval_rank


def shuffled_features(
    training: np.ndarray, evaluation: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_output = training.copy()
    eval_output = evaluation.copy()
    for column in range(training.shape[1]):
        train_output[:, column] = training[
            rng.permutation(len(training)), column
        ]
        eval_output[:, column] = evaluation[
            rng.permutation(len(evaluation)), column
        ]
    return train_output, eval_output


def model(config: dict[str, object], seed: int) -> RandomForestRegressor:
    settings = config["recipient_model"]
    return RandomForestRegressor(
        n_estimators=int(settings["n_estimators"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        max_features=float(settings["max_features"]),
        criterion=str(settings["criterion"]),
        random_state=seed,
        n_jobs=1,
    )


def score(
    method: str,
    train_x: np.ndarray,
    eval_x: np.ndarray,
    train_y: np.ndarray,
    eval_y: np.ndarray,
    config: dict[str, object],
    seed: int,
) -> dict[str, object]:
    estimator = model(config, seed)
    estimator.fit(train_x, train_y)
    prediction = estimator.predict(eval_x)
    spearman = stats.spearmanr(eval_y, prediction).statistic
    return {
        "method": method,
        "rmse": float(math.sqrt(mean_squared_error(eval_y, prediction))),
        "mae": float(mean_absolute_error(eval_y, prediction)),
        "r2": float(r2_score(eval_y, prediction)),
        "spearman": float(spearman) if np.isfinite(spearman) else float("nan"),
        "evaluation_rows": int(len(eval_y)),
    }


def run_draw(
    budget: int,
    repeat: int,
    development: pd.DataFrame,
    structure_x: np.ndarray,
    calculated_x: np.ndarray,
    donor_x: np.ndarray,
    draw_rows: pd.DataFrame,
    config: dict[str, object],
) -> list[dict[str, object]]:
    selected = draw_rows[
        (draw_rows["budget"] == budget)
        & (draw_rows["repeat"] == repeat)
    ]
    training_keys = set(
        selected.loc[selected["role"] == "training", "target_key"].astype(str)
    )
    excluded_keys = set(
        selected.loc[
            selected["role"] == "excluded_boundary_scaffold", "target_key"
        ].astype(str)
    )
    keys = development["target_key"].astype(str)
    training_mask = keys.isin(training_keys).to_numpy()
    evaluation_mask = (~keys.isin(training_keys | excluded_keys)).to_numpy()
    if int(training_mask.sum()) != budget:
        raise RuntimeError(f"Budget drift: {budget}, repeat {repeat}")

    train_scaffolds = set(development.loc[training_mask, "scaffold"])
    eval_scaffolds = set(development.loc[evaluation_mask, "scaffold"])
    if train_scaffolds & eval_scaffolds:
        raise RuntimeError("Scaffold leakage in development gate")

    train_y = development.loc[training_mask, "log1p_her"].to_numpy(float)
    eval_y = development.loc[evaluation_mask, "log1p_her"].to_numpy(float)
    structure_train = structure_x[training_mask]
    structure_eval = structure_x[evaluation_mask]
    calc_train, calc_eval = impute_from_training(
        calculated_x[training_mask], calculated_x[evaluation_mask]
    )
    donor_train = donor_x[training_mask].astype(float, copy=True)
    donor_eval = donor_x[evaluation_mask].astype(float, copy=True)
    donor_rank_train, donor_rank_eval = rank_from_training(
        donor_train, donor_eval
    )
    shuffled_raw_train, shuffled_raw_eval = shuffled_features(
        donor_train,
        donor_eval,
        SEED + budget * 10000 + repeat * 10 + 1,
    )
    shuffled_rank_train, shuffled_rank_eval = shuffled_features(
        donor_rank_train,
        donor_rank_eval,
        SEED + budget * 10000 + repeat * 10 + 2,
    )
    rng = np.random.default_rng(SEED + budget * 10000 + repeat * 10 + 3)
    gaussian_train = rng.standard_normal((budget, donor_x.shape[1]))
    gaussian_eval = rng.standard_normal(
        (int(evaluation_mask.sum()), donor_x.shape[1])
    )

    matrices = {
        "target_structure_only": (structure_train, structure_eval),
        "target_structure_plus_calculated": (
            np.column_stack([structure_train, calc_train]),
            np.column_stack([structure_eval, calc_eval]),
        ),
        "target_structure_plus_donor_raw": (
            np.column_stack([structure_train, donor_train]),
            np.column_stack([structure_eval, donor_eval]),
        ),
        "target_structure_plus_donor_rank": (
            np.column_stack([structure_train, donor_rank_train]),
            np.column_stack([structure_eval, donor_rank_eval]),
        ),
        "target_structure_plus_calculated_plus_donor_raw": (
            np.column_stack([structure_train, calc_train, donor_train]),
            np.column_stack([structure_eval, calc_eval, donor_eval]),
        ),
        "target_structure_plus_calculated_plus_donor_rank": (
            np.column_stack([structure_train, calc_train, donor_rank_train]),
            np.column_stack([structure_eval, calc_eval, donor_rank_eval]),
        ),
        "target_structure_plus_shuffled_donor_raw": (
            np.column_stack([structure_train, shuffled_raw_train]),
            np.column_stack([structure_eval, shuffled_raw_eval]),
        ),
        "target_structure_plus_shuffled_donor_rank": (
            np.column_stack([structure_train, shuffled_rank_train]),
            np.column_stack([structure_eval, shuffled_rank_eval]),
        ),
        "target_structure_plus_gaussian_features": (
            np.column_stack([structure_train, gaussian_train]),
            np.column_stack([structure_eval, gaussian_eval]),
        ),
    }

    rows: list[dict[str, object]] = []
    for method_index, (method_name, (train_x, eval_x)) in enumerate(
        matrices.items()
    ):
        result = score(
            method_name,
            train_x,
            eval_x,
            train_y,
            eval_y,
            config,
            SEED + budget * 100000 + repeat * 100 + method_index,
        )
        result.update(
            {
                "budget": budget,
                "repeat": repeat,
                "training_rows": int(training_mask.sum()),
                "excluded_boundary_rows": int(len(excluded_keys)),
            }
        )
        rows.append(result)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1)
    arguments = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    source_skill = json.loads(SOURCE_SKILL_PATH.read_text(encoding="utf-8"))
    draw_manifest = json.loads(
        DRAW_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if file_hash(DESIGN_PATH) != audit["design_sha256"]:
        raise RuntimeError("Design changed after pair audit")
    if source_skill["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Source feature design hash mismatch")
    if source_skill["pair_audit_sha256"] != file_hash(AUDIT_PATH):
        raise RuntimeError("Source feature audit hash mismatch")
    if source_skill["target_metadata_sha256"] != file_hash(METADATA_PATH):
        raise RuntimeError("Source feature metadata hash mismatch")
    if source_skill["feature_sha256"] != file_hash(DONOR_FEATURE_PATH):
        raise RuntimeError("Source feature file hash mismatch")
    if draw_manifest["draw_sha256"] != file_hash(DRAW_PATH):
        raise RuntimeError("Frozen development draws changed")
    if draw_manifest["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Development draw design hash mismatch")
    if (
        file_hash(TARGET_PATH)
        != design["target"]["development_file"]["required_sha256"]
    ):
        raise RuntimeError("Development target file hash changed")

    admitted = list(source_skill["admitted_properties"])
    if not admitted:
        summary = {
            "status": "development-not-run-source-abstained",
            "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
            "source_skill_sha256": file_hash(SOURCE_SKILL_PATH),
            "admitted_properties": [],
            "blind_outcome_access": "The blind HER file was not loaded.",
        }
        SUMMARY_PATH.write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2))
        return

    metadata = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    donor_features = (
        pd.read_csv(DONOR_FEATURE_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    if not metadata["target_key"].equals(donor_features["target_key"]):
        raise RuntimeError("Target metadata and donor features do not align")

    calculated_columns = list(config["calculated_descriptor_columns"])
    target = pd.read_csv(
        TARGET_PATH,
        usecols=["ID", "HER (µmol/h)", *calculated_columns],
    )
    target["target_key"] = "development:" + target["ID"].astype(str)
    target = metadata[["target_key"]].merge(
        target, on="target_key", how="left", validate="one_to_one"
    )
    her = pd.to_numeric(target["HER (µmol/h)"], errors="coerce")
    if her.isna().any() or (her < 0).any():
        raise RuntimeError("Development HER contains missing or negative values")
    metadata["log1p_her"] = np.log1p(her.to_numpy(float))

    donor_columns: list[str] = []
    for property_name in admitted:
        slug = str(source_skill["properties"][property_name]["slug"])
        donor_columns.extend([f"pred_{slug}", f"unc_{slug}"])
    donor_x = donor_features[donor_columns].to_numpy(float)
    if not np.isfinite(donor_x).all():
        raise RuntimeError("Admitted donor vector contains nonfinite values")
    structure_x = feature_matrix(metadata["canonical_smiles"].astype(str).tolist())
    calculated_x = target[calculated_columns].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(float)
    draws = pd.read_csv(DRAW_PATH)
    budgets = [int(value) for value in draw_manifest["budgets"]]
    repeats = int(draw_manifest["repeats"])

    tasks = (
        (budget, repeat)
        for budget in budgets
        for repeat in range(repeats)
    )
    nested_rows = Parallel(n_jobs=arguments.jobs, verbose=10)(
        delayed(run_draw)(
            budget,
            repeat,
            metadata,
            structure_x,
            calculated_x,
            donor_x,
            draws,
            config,
        )
        for budget, repeat in tasks
    )
    metrics = pd.DataFrame(
        [row for task_rows in nested_rows for row in task_rows]
    ).sort_values(["budget", "repeat", "method"])
    metrics.to_csv(METRICS_PATH, index=False, lineterminator="\n")

    primary = metrics[metrics["budget"] == PRIMARY_BUDGET]
    mean_rmse = primary.groupby("method")["rmse"].mean()
    selected_form = (
        "raw"
        if mean_rmse["target_structure_plus_donor_raw"]
        <= mean_rmse["target_structure_plus_donor_rank"]
        else "rank"
    )
    donor_method = f"target_structure_plus_donor_{selected_form}"
    shuffled_method = (
        f"target_structure_plus_shuffled_donor_{selected_form}"
    )
    pivot = primary.pivot(index="repeat", columns="method", values="rmse")
    donor_gain = (
        pivot["target_structure_only"] - pivot[donor_method]
    ) / pivot["target_structure_only"]
    shuffled_gain = (
        pivot["target_structure_only"] - pivot[shuffled_method]
    ) / pivot["target_structure_only"]
    minimum_gain = float(
        config["development_admission"][
            "minimum_mean_paired_relative_rmse_gain"
        ]
    )
    admitted_to_blind = bool(
        donor_gain.mean() >= minimum_gain
        and donor_gain.mean() > shuffled_gain.median()
    )

    method_summary = (
        metrics.groupby(["budget", "method"])
        .agg(
            mean_rmse=("rmse", "mean"),
            median_rmse=("rmse", "median"),
            mean_mae=("mae", "mean"),
            mean_r2=("r2", "mean"),
            mean_spearman=("spearman", "mean"),
        )
        .reset_index()
    )
    summary = {
        "status": (
            "development-gate-passed"
            if admitted_to_blind
            else "development-gate-abstained"
        ),
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": file_hash(DESIGN_PATH),
        "implementation_config_sha256": file_hash(CONFIG_PATH),
        "implementation_sha256": file_hash(Path(__file__)),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "source_skill_sha256": file_hash(SOURCE_SKILL_PATH),
        "donor_feature_sha256": file_hash(DONOR_FEATURE_PATH),
        "development_draw_manifest_sha256": file_hash(DRAW_MANIFEST_PATH),
        "development_draw_sha256": file_hash(DRAW_PATH),
        "development_input_sha256": file_hash(TARGET_PATH),
        "metrics_sha256": file_hash(METRICS_PATH),
        "admitted_source_properties": admitted,
        "donor_feature_columns": donor_columns,
        "primary_budget": PRIMARY_BUDGET,
        "selected_feature_form": selected_form,
        "primary_mean_relative_rmse_gain": float(donor_gain.mean()),
        "primary_gain_quantiles": {
            key: float(value)
            for key, value in zip(
                ["q025", "median", "q975"],
                np.quantile(donor_gain, [0.025, 0.5, 0.975]),
                strict=True,
            )
        },
        "matched_shuffled_median_relative_gain": float(
            shuffled_gain.median()
        ),
        "positive_draw_fraction": float(np.mean(donor_gain > 0)),
        "admitted_to_blind": admitted_to_blind,
        "method_summary": method_summary.to_dict(orient="records"),
        "blind_outcome_access": (
            "The blind HER file was not opened, parsed, or joined."
        ),
        "claim_guard": str(config["claim_guard"]),
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
