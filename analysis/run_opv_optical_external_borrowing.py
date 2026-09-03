"""Run the frozen optical-to-OPV external OOD benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
FREEZE_PATH = HERE / "opv_optical_implementation_freeze.json"
METADATA_PATH = (
    HERE / "results" / "opv_optical_target_metadata_no_outcomes.csv"
)
DRAW_PATH = HERE / "results" / "opv_optical_label_draws.csv"
DRAW_MANIFEST_PATH = (
    HERE / "results" / "opv_optical_label_draws_manifest.json"
)
SOURCE_FEATURE_PATH = HERE / "results" / "opv_optical_source_features.csv"
SOURCE_SUMMARY_PATH = HERE / "results" / "opv_optical_source_summary.json"
TARGET_ZIP = ROOT / "data" / "external" / "opv_borrowing" / "opvdb.zip"
TARGET_MEMBER = "data/opv_devices_strict_molecular_benchmark.csv"
RESULTS = HERE / "results"

OUTCOMES = ["pce", "voc", "jsc", "ff"]
METRIC_OUTCOMES = [*OUTCOMES, "pce_physics_recombined"]
CATEGORICAL_STATE = [
    "additive_canonical",
    "device_structure",
    "device_type",
    "etl_canonical",
    "htl_canonical",
    "solvent_canonical",
]
NUMERIC_STATE = [
    "d_a_ratio",
    "additive_ratio",
    "active_layer_thickness",
    "annealing_temp",
]
SCOPES = [
    "qualified_hard_ood_40pct",
    "source_qualified_external",
    "full_external",
    "source_qualified_double_scaffold_ood",
]
METHODS = [
    "structure_only",
    "state_aware_target_only",
    "state_aware_plus_real_solid_optical_card",
    "state_aware_plus_shuffled_source_card",
    "state_aware_plus_state_blind_optical_card",
    "state_aware_plus_permuted_real_card",
    "state_aware_plus_gaussian_card",
]
LEARNERS = ["extra_trees", "random_forest"]

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


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)


def parse_first_number(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    text = str(value).strip().replace(",", ".")
    if ":" in text:
        parts = text.split(":")
        try:
            left = float(parts[0])
            right = float(parts[1])
            return left / right if right else float("nan")
        except (TypeError, ValueError):
            pass
    import re

    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text)
    return float(match.group(0)) if match else float("nan")


def fingerprints(smiles_values: list[str]) -> tuple[np.ndarray, list[Any]]:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    bit_rows = np.zeros((len(smiles_values), 2048), dtype=np.float32)
    rdkit_fingerprints = []
    for row, smiles in enumerate(smiles_values):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited structure stopped parsing: {smiles}")
        fingerprint = generator.GetFingerprint(molecule)
        rdkit_fingerprints.append(fingerprint)
        bit_rows[row] = generator.GetFingerprintAsNumPy(molecule)
    return bit_rows, rdkit_fingerprints


def similarity_matrix(
    row_fingerprints: list[Any], column_fingerprints: list[Any]
) -> np.ndarray:
    output = np.empty(
        (len(row_fingerprints), len(column_fingerprints)),
        dtype=np.float32,
    )
    for row, fingerprint in enumerate(row_fingerprints):
        output[row] = DataStructs.BulkTanimotoSimilarity(
            fingerprint, column_fingerprints
        )
    return output


def numeric_state_raw(metadata: pd.DataFrame) -> np.ndarray:
    return np.column_stack(
        [
            metadata[name].map(parse_first_number).to_numpy(float)
            for name in NUMERIC_STATE
        ]
    )


def numeric_state_blocks(
    raw: np.ndarray,
    training_rows: np.ndarray,
    external_rows: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    training_columns = []
    external_columns = []
    for column in range(raw.shape[1]):
        training_values = raw[training_rows, column]
        external_values = raw[external_rows, column]
        finite = np.isfinite(training_values)
        median = (
            float(np.median(training_values[finite]))
            if finite.any()
            else 0.0
        )
        q25, q75 = (
            np.quantile(training_values[finite], [0.25, 0.75])
            if finite.any()
            else (0.0, 1.0)
        )
        scale = float(q75 - q25)
        if scale <= 0:
            scale = 1.0
        training_missing = ~np.isfinite(training_values)
        external_missing = ~np.isfinite(external_values)
        training_filled = np.where(
            training_missing, median, training_values
        )
        external_filled = np.where(
            external_missing, median, external_values
        )
        training_columns.extend(
            [
                ((training_filled - median) / scale).astype(np.float32),
                training_missing.astype(np.float32),
            ]
        )
        external_columns.extend(
            [
                ((external_filled - median) / scale).astype(np.float32),
                external_missing.astype(np.float32),
            ]
        )
    return (
        np.column_stack(training_columns).astype(np.float32),
        np.column_stack(external_columns).astype(np.float32),
    )


def state_feature_blocks(
    bundle: dict[str, Any],
    training_rows: np.ndarray,
    external_rows: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, int]:
    encoder = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=20,
        sparse_output=False,
        dtype=np.float32,
    )
    categorical_frame = bundle["categorical_frame"]
    encoder.fit(categorical_frame.iloc[training_rows])
    categorical_training = encoder.transform(
        categorical_frame.iloc[training_rows]
    ).astype(np.float32)
    categorical_external = encoder.transform(
        categorical_frame.iloc[external_rows]
    ).astype(np.float32)
    numeric_training, numeric_external = numeric_state_blocks(
        bundle["numeric_raw"], training_rows, external_rows
    )
    training = np.hstack(
        [
            bundle["structure"][training_rows],
            categorical_training,
            numeric_training,
            bundle["support"][training_rows],
        ]
    ).astype(np.float32)
    external = np.hstack(
        [
            bundle["structure"][external_rows],
            categorical_external,
            numeric_external,
            bundle["support"][external_rows],
        ]
    ).astype(np.float32)
    return training, external, int(categorical_training.shape[1])


def build_cards(
    metadata: pd.DataFrame, source: pd.DataFrame
) -> dict[str, np.ndarray]:
    source = source.set_index("canonical_smiles")
    tasks = sorted(
        {
            column.split("__")[1]
            for column in source.columns
            if column.startswith("solid_real__") and column.endswith("__mean")
        }
    )
    prefixes = {
        "real": "solid_real",
        "shuffled": "solid_shuffled",
        "global": "global_state_blind",
    }
    output: dict[str, np.ndarray] = {}
    donor_smiles = metadata["donor_smiles_canonical"].astype(str)
    acceptor_smiles = metadata["acceptor_smiles_canonical"].astype(str)
    for card_name, prefix in prefixes.items():
        columns = []
        for task in tasks:
            mean_column = f"{prefix}__{task}__mean"
            std_column = f"{prefix}__{task}__std"
            donor_mean = donor_smiles.map(source[mean_column]).to_numpy(float)
            acceptor_mean = acceptor_smiles.map(
                source[mean_column]
            ).to_numpy(float)
            donor_std = donor_smiles.map(source[std_column]).to_numpy(float)
            acceptor_std = acceptor_smiles.map(
                source[std_column]
            ).to_numpy(float)
            columns.extend(
                [
                    donor_mean,
                    acceptor_mean,
                    donor_std,
                    acceptor_std,
                    donor_mean - acceptor_mean,
                    np.abs(donor_mean - acceptor_mean),
                    donor_mean * acceptor_mean,
                ]
            )
        matrix = np.column_stack(columns).astype(np.float32)
        if not np.isfinite(matrix).all():
            raise RuntimeError(f"Nonfinite source card: {card_name}")
        output[card_name] = matrix
    dimensions = {name: value.shape[1] for name, value in output.items()}
    if len(set(dimensions.values())) != 1:
        raise RuntimeError(f"Source card dimension mismatch: {dimensions}")
    return output


def build_feature_bundle(
    metadata: pd.DataFrame, source: pd.DataFrame
) -> dict[str, Any]:
    development_mask = ~metadata["external_doi_holdout"].to_numpy(bool)
    unique_smiles = sorted(
        set(metadata["donor_smiles_canonical"].astype(str))
        | set(metadata["acceptor_smiles_canonical"].astype(str))
    )
    bit_matrix, fp_objects = fingerprints(unique_smiles)
    smiles_index = {value: row for row, value in enumerate(unique_smiles)}
    donor_indices = metadata["donor_smiles_canonical"].map(
        smiles_index
    ).to_numpy(int)
    acceptor_indices = metadata["acceptor_smiles_canonical"].map(
        smiles_index
    ).to_numpy(int)
    structure = np.hstack(
        [bit_matrix[donor_indices], bit_matrix[acceptor_indices]]
    ).astype(np.float32)

    categorical_frame = (
        metadata[CATEGORICAL_STATE]
        .fillna("__missing__")
        .astype(str)
        .apply(lambda column: column.str.strip().str.lower())
    )
    numeric_raw = numeric_state_raw(metadata)
    support = metadata[
        [
            "donor_solid_source_support",
            "acceptor_solid_source_support",
            "donor_global_source_support",
            "acceptor_global_source_support",
        ]
    ].to_numpy(np.float32)
    cards = build_cards(metadata, source)

    external_rows = np.flatnonzero(
        metadata["external_doi_holdout"].to_numpy(bool)
    )
    development_rows = np.flatnonzero(development_mask)
    external_donor_smiles = sorted(
        set(
            metadata.iloc[external_rows]["donor_smiles_canonical"].astype(str)
        )
    )
    external_acceptor_smiles = sorted(
        set(
            metadata.iloc[external_rows][
                "acceptor_smiles_canonical"
            ].astype(str)
        )
    )
    development_donor_smiles = sorted(
        set(
            metadata.iloc[development_rows][
                "donor_smiles_canonical"
            ].astype(str)
        )
    )
    development_acceptor_smiles = sorted(
        set(
            metadata.iloc[development_rows][
                "acceptor_smiles_canonical"
            ].astype(str)
        )
    )
    fp_map = {
        smiles: fp_objects[smiles_index[smiles]] for smiles in unique_smiles
    }
    donor_similarity = similarity_matrix(
        [fp_map[value] for value in external_donor_smiles],
        [fp_map[value] for value in development_donor_smiles],
    )
    acceptor_similarity = similarity_matrix(
        [fp_map[value] for value in external_acceptor_smiles],
        [fp_map[value] for value in development_acceptor_smiles],
    )
    return {
        "structure": structure,
        "categorical_frame": categorical_frame,
        "numeric_raw": numeric_raw,
        "support": support,
        "cards": cards,
        "external_rows": external_rows,
        "external_donor_row": metadata.iloc[external_rows][
            "donor_smiles_canonical"
        ]
        .map({value: row for row, value in enumerate(external_donor_smiles)})
        .to_numpy(int),
        "external_acceptor_row": metadata.iloc[external_rows][
            "acceptor_smiles_canonical"
        ]
        .map(
            {
                value: row
                for row, value in enumerate(external_acceptor_smiles)
            }
        )
        .to_numpy(int),
        "development_donor_column": {
            value: column
            for column, value in enumerate(development_donor_smiles)
        },
        "development_acceptor_column": {
            value: column
            for column, value in enumerate(development_acceptor_smiles)
        },
        "donor_similarity": donor_similarity,
        "acceptor_similarity": acceptor_similarity,
        "state_dimensions": {
            "structure": int(structure.shape[1]),
            "categorical_input_columns": int(len(CATEGORICAL_STATE)),
            "categorical_encoding": (
                "fit within each labelled target draw"
            ),
            "numeric": int(len(NUMERIC_STATE) * 2),
            "support": int(support.shape[1]),
            "card": int(cards["real"].shape[1]),
        },
    }


def load_outcomes(metadata: pd.DataFrame, synthetic: bool) -> np.ndarray:
    if synthetic:
        values = []
        for row in metadata.itertuples(index=False):
            token = (
                f"{row.id}|{row.donor_scaffold}|"
                f"{row.acceptor_scaffold}|{row.device_type}"
            )
            rng = np.random.default_rng(stable_int(token))
            pce = 5.0 + 8.0 * float(row.pair_solid_source_support) + rng.normal()
            voc = 0.4 + 0.9 * float(row.donor_global_source_support) + 0.05 * rng.normal()
            jsc = 5.0 + 25.0 * float(row.acceptor_solid_source_support) + rng.normal()
            ff = 45.0 + 20.0 * float(row.pair_global_source_support) + 2.0 * rng.normal()
            values.append([pce, voc, jsc, ff])
        return np.asarray(values, dtype=np.float32)

    with zipfile.ZipFile(TARGET_ZIP) as archive:
        target_member = portable_zip_member(archive, TARGET_MEMBER)
        outcomes = pd.read_csv(
            archive.open(target_member),
            usecols=["id", *OUTCOMES],
            dtype={"id": "string"},
            low_memory=False,
        )
    joined = metadata[["id"]].astype({"id": "string"}).merge(
        outcomes, on="id", how="left", validate="one_to_one"
    )
    values = joined[OUTCOMES].to_numpy(float)
    if not np.isfinite(values).all():
        raise RuntimeError("Strict OPV outcomes are incomplete or nonfinite")
    if (
        (values[:, 0] < 0).any()
        or (values[:, 1] < 0).any()
        or (values[:, 2] < 0).any()
        or (values[:, 3] < 0).any()
    ):
        raise RuntimeError("Negative OPV performance value")
    return values.astype(np.float32)


def model_for(name: str, trees: int, seed: int):
    common = dict(
        n_estimators=trees,
        min_samples_leaf=2,
        max_features=0.5,
        random_state=seed,
        n_jobs=1,
    )
    if name == "extra_trees":
        return ExtraTreesRegressor(**common)
    if name == "random_forest":
        return RandomForestRegressor(**common)
    raise ValueError(name)


def metric_rows(
    truth: np.ndarray,
    prediction: np.ndarray,
    mask: np.ndarray,
    metadata_external: pd.DataFrame,
    task_info: dict[str, Any],
    method: str,
    learner: str,
    scope: str,
) -> list[dict[str, Any]]:
    rows = []
    if not mask.any():
        return rows
    truth_with_physics = np.column_stack([truth, truth[:, 0]])
    recombined = (
        prediction[:, 1] * prediction[:, 2] * prediction[:, 3] / 100.0
    )
    prediction_with_physics = np.column_stack([prediction, recombined])
    for column, outcome in enumerate(METRIC_OUTCOMES):
        y_true = truth_with_physics[mask, column]
        y_pred = prediction_with_physics[mask, column]
        spearman = stats.spearmanr(y_true, y_pred).statistic
        rows.append(
            {
                **task_info,
                "learner": learner,
                "method": method,
                "scope": scope,
                "outcome": outcome,
                "rows": int(mask.sum()),
                "dois": int(
                    metadata_external.loc[
                        mask, "doi_normalized_audit"
                    ].nunique()
                ),
                "rmse": float(
                    mean_squared_error(y_true, y_pred) ** 0.5
                ),
                "mae": float(mean_absolute_error(y_true, y_pred)),
                "r2": float(r2_score(y_true, y_pred)),
                "spearman": float(spearman),
            }
        )
    return rows


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
        newline="",
    ) as handle:
        temporary = Path(handle.name)
        frame.to_csv(handle, index=False, lineterminator="\n")
    os.replace(temporary, path)


def run_task(
    budget: int,
    repeat: int,
    draws: pd.DataFrame,
    metadata: pd.DataFrame,
    y: np.ndarray,
    bundle: dict[str, Any],
    trees: int,
    checkpoint_dir: Path,
) -> str:
    metrics_path = checkpoint_dir / f"b{budget}_r{repeat}_metrics.csv"
    predictions_path = (
        checkpoint_dir / f"b{budget}_r{repeat}_primary.csv"
    )
    if metrics_path.exists() and (
        budget != 120 or predictions_path.exists()
    ):
        return str(metrics_path)

    chosen_ids = set(
        draws.loc[
            (draws["budget"] == budget) & (draws["repeat"] == repeat),
            "id",
        ].astype(str)
    )
    id_to_row = {
        str(value): row for row, value in enumerate(metadata["id"].astype(str))
    }
    training_rows = np.asarray(
        [id_to_row[value] for value in sorted(chosen_ids)], dtype=int
    )
    if len(training_rows) != budget:
        raise RuntimeError("Training draw size drift")

    external_rows = bundle["external_rows"]
    metadata_external = metadata.iloc[external_rows].reset_index(drop=True)
    y_external = y[external_rows]
    state_training, state_external, categorical_dimension = (
        state_feature_blocks(bundle, training_rows, external_rows)
    )
    training_donor_columns = sorted(
        {
            bundle["development_donor_column"][value]
            for value in metadata.iloc[training_rows][
                "donor_smiles_canonical"
            ].astype(str)
        }
    )
    training_acceptor_columns = sorted(
        {
            bundle["development_acceptor_column"][value]
            for value in metadata.iloc[training_rows][
                "acceptor_smiles_canonical"
            ].astype(str)
        }
    )
    donor_max = bundle["donor_similarity"][
        bundle["external_donor_row"]
    ][:, training_donor_columns].max(axis=1)
    acceptor_max = bundle["acceptor_similarity"][
        bundle["external_acceptor_row"]
    ][:, training_acceptor_columns].max(axis=1)
    target_similarity = np.sqrt(donor_max * acceptor_max)
    qualified = (
        metadata_external["donor_solid_source_support"].to_numpy(float)
        >= 0.20
    ) & (
        metadata_external["acceptor_solid_source_support"].to_numpy(float)
        >= 0.20
    )
    hard_count = int(np.ceil(0.40 * int(qualified.sum())))
    qualified_rows = np.flatnonzero(qualified)
    ordering = sorted(
        qualified_rows,
        key=lambda row: (
            float(target_similarity[row]),
            hashlib.sha256(
                str(metadata_external.iloc[row]["id"]).encode("utf-8")
            ).hexdigest(),
        ),
    )
    hard = np.zeros(len(external_rows), dtype=bool)
    hard[ordering[:hard_count]] = True
    training_donor_scaffolds = set(
        metadata.iloc[training_rows]["donor_scaffold"].astype(str)
    )
    training_acceptor_scaffolds = set(
        metadata.iloc[training_rows]["acceptor_scaffold"].astype(str)
    )
    double_scaffold = qualified & ~metadata_external[
        "donor_scaffold"
    ].astype(str).isin(training_donor_scaffolds).to_numpy() & ~metadata_external[
        "acceptor_scaffold"
    ].astype(str).isin(training_acceptor_scaffolds).to_numpy()
    scope_masks = {
        "qualified_hard_ood_40pct": hard,
        "source_qualified_external": qualified,
        "full_external": np.ones(len(external_rows), dtype=bool),
        "source_qualified_double_scaffold_ood": double_scaffold,
    }

    seed = 2026072700 + budget * 1000 + repeat
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(len(metadata))
    real_card = bundle["cards"]["real"]
    development_real = real_card[~metadata["external_doi_holdout"].to_numpy(bool)]
    card_mean = development_real.mean(axis=0)
    card_std = development_real.std(axis=0, ddof=1)
    card_std = np.where(card_std > 0, card_std, 1.0)
    gaussian_card = rng.normal(
        card_mean, card_std, size=real_card.shape
    ).astype(np.float32)
    method_cards = {
        "structure_only": None,
        "state_aware_target_only": None,
        "state_aware_plus_real_solid_optical_card": real_card,
        "state_aware_plus_shuffled_source_card": bundle["cards"]["shuffled"],
        "state_aware_plus_state_blind_optical_card": bundle["cards"]["global"],
        "state_aware_plus_permuted_real_card": real_card[permutation],
        "state_aware_plus_gaussian_card": gaussian_card,
    }
    y_train = y[training_rows].astype(float)
    y_mean = y_train.mean(axis=0)
    y_scale = y_train.std(axis=0, ddof=1)
    y_scale = np.where(y_scale > 0, y_scale, 1.0)
    y_standard = (y_train - y_mean) / y_scale
    task_info = {"budget": budget, "repeat": repeat, "seed": seed}
    task_info["state_categorical_dimension"] = categorical_dimension
    metrics = []
    primary_predictions = []
    for learner in LEARNERS:
        for method in METHODS:
            use_state = method != "structure_only"
            card = method_cards[method]
            if not use_state:
                x_train = bundle["structure"][training_rows]
                x_external = bundle["structure"][external_rows]
            elif card is None:
                x_train = state_training
                x_external = state_external
            else:
                x_train = np.hstack(
                    [state_training, card[training_rows]]
                )
                x_external = np.hstack(
                    [state_external, card[external_rows]]
                )
            model = model_for(
                learner,
                trees,
                (seed + stable_int(f"{learner}|{method}")) % (2**32 - 1),
            )
            model.fit(x_train, y_standard)
            prediction = model.predict(x_external) * y_scale + y_mean
            for scope, mask in scope_masks.items():
                metrics.extend(
                    metric_rows(
                        y_external,
                        prediction,
                        mask,
                        metadata_external,
                        task_info,
                        method,
                        learner,
                        scope,
                    )
                )
            if (
                budget == 120
                and learner == "extra_trees"
                and scope_masks["qualified_hard_ood_40pct"].any()
            ):
                mask = scope_masks["qualified_hard_ood_40pct"]
                selected = metadata_external.loc[
                    mask, ["id", "doi_normalized_audit"]
                ].copy()
                selected["repeat"] = repeat
                selected["method"] = method
                selected["truth_pce"] = y_external[mask, 0]
                selected["predicted_pce"] = prediction[mask, 0]
                selected["truth_voc"] = y_external[mask, 1]
                selected["truth_jsc"] = y_external[mask, 2]
                selected["truth_ff"] = y_external[mask, 3]
                selected["predicted_voc"] = prediction[mask, 1]
                selected["predicted_jsc"] = prediction[mask, 2]
                selected["predicted_ff"] = prediction[mask, 3]
                selected["predicted_pce_physics_recombined"] = (
                    prediction[mask, 1]
                    * prediction[mask, 2]
                    * prediction[mask, 3]
                    / 100.0
                )
                primary_predictions.append(selected)
    atomic_csv(pd.DataFrame(metrics), metrics_path)
    if budget == 120:
        atomic_csv(
            pd.concat(primary_predictions, ignore_index=True),
            predictions_path,
        )
    return str(metrics_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--trees", type=int, default=None)
    parser.add_argument("--limit-repeats", type=int, default=None)
    arguments = parser.parse_args()
    if arguments.formal == arguments.synthetic_smoke:
        raise RuntimeError("Choose exactly one of --formal or --synthetic-smoke")

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    draw_manifest = json.loads(
        DRAW_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    source_summary = json.loads(
        SOURCE_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    if sha256(METADATA_PATH) != design["outcome_free_audit"][
        "metadata_sha256"
    ]:
        raise RuntimeError("Outcome-free metadata drift")
    if sha256(TARGET_ZIP) != design["target"][
        "required_archive_sha256"
    ]:
        raise RuntimeError("OPV target archive drift")
    if draw_manifest["design_sha256"] != sha256(DESIGN_PATH):
        raise RuntimeError("Draw design drift")
    if draw_manifest["draw_sha256"] != sha256(DRAW_PATH):
        raise RuntimeError("Draw file drift")
    if source_summary["feature_sha256"] != sha256(SOURCE_FEATURE_PATH):
        raise RuntimeError("Source feature file drift")
    if arguments.formal:
        if source_summary["status"] != "strict-source-features-ready":
            raise RuntimeError("Strict source features are not ready")
        if source_summary["design_sha256"] != sha256(DESIGN_PATH):
            raise RuntimeError("Strict source features use a stale design")
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        if freeze["design_sha256"] != sha256(DESIGN_PATH):
            raise RuntimeError("Implementation freeze design drift")
        if freeze["run_sha256"] != sha256(Path(__file__)):
            raise RuntimeError("Run implementation changed after freeze")

    metadata = pd.read_csv(METADATA_PATH, low_memory=False)
    source = pd.read_csv(SOURCE_FEATURE_PATH)
    draws = pd.read_csv(DRAW_PATH, dtype={"id": "string"})
    y = load_outcomes(metadata, synthetic=arguments.synthetic_smoke)
    bundle = build_feature_bundle(metadata, source)
    trees = (
        int(arguments.trees)
        if arguments.trees is not None
        else int(design["models"]["n_estimators"])
    )
    budgets = [
        int(value) for value in design["split_and_ood"]["label_budgets"]
    ]
    repeats = int(design["split_and_ood"]["repeats"])
    if arguments.limit_repeats is not None:
        repeats = min(repeats, int(arguments.limit_repeats))
    mode = "formal" if arguments.formal else "synthetic_smoke"
    checkpoint_dir = RESULTS / (
        "opv_optical_external_checkpoints_"
        + mode
        + "_"
        + sha256(DESIGN_PATH)[:12]
        + "_"
        + sha256(SOURCE_FEATURE_PATH)[:12]
        + "_"
        + sha256(Path(__file__))[:12]
    )
    tasks = [(budget, repeat) for budget in budgets for repeat in range(repeats)]
    Parallel(
        n_jobs=int(arguments.jobs),
        backend="loky",
        verbose=10,
        max_nbytes="10M",
        mmap_mode="r",
    )(
        delayed(run_task)(
            budget,
            repeat,
            draws,
            metadata,
            y,
            bundle,
            trees,
            checkpoint_dir,
        )
        for budget, repeat in tasks
    )

    metric_files = sorted(checkpoint_dir.glob("*_metrics.csv"))
    expected = len(tasks)
    if len(metric_files) != expected:
        raise RuntimeError(
            f"Expected {expected} metric checkpoints, found {len(metric_files)}"
        )
    metrics = pd.concat(
        [pd.read_csv(path) for path in metric_files], ignore_index=True
    )
    prediction_files = sorted(checkpoint_dir.glob("*_primary.csv"))
    expected_predictions = repeats
    if len(prediction_files) != expected_predictions:
        raise RuntimeError(
            f"Expected {expected_predictions} primary checkpoints, "
            f"found {len(prediction_files)}"
        )
    primary_predictions = pd.concat(
        [pd.read_csv(path) for path in prediction_files], ignore_index=True
    )
    metric_path = RESULTS / f"opv_optical_external_{mode}_metrics.csv"
    prediction_path = (
        RESULTS / f"opv_optical_external_{mode}_primary_predictions.csv"
    )
    metrics.to_csv(metric_path, index=False, lineterminator="\n")
    primary_predictions.to_csv(
        prediction_path, index=False, lineterminator="\n"
    )
    summary = {
        "status": "model-run-complete",
        "mode": mode,
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "run_sha256": sha256(Path(__file__)),
        "metadata_sha256": sha256(METADATA_PATH),
        "draw_sha256": sha256(DRAW_PATH),
        "source_feature_sha256": sha256(SOURCE_FEATURE_PATH),
        "target_archive_sha256": sha256(TARGET_ZIP),
        "metrics_sha256": sha256(metric_path),
        "primary_predictions_sha256": sha256(prediction_path),
        "metric_rows": int(len(metrics)),
        "primary_prediction_rows": int(len(primary_predictions)),
        "budgets": budgets,
        "repeats": repeats,
        "trees": trees,
        "learners": LEARNERS,
        "methods": METHODS,
        "scopes": SCOPES,
        "direct_outcomes": OUTCOMES,
        "metric_outcomes": METRIC_OUTCOMES,
        "feature_dimensions": bundle["state_dimensions"],
        "claim_guard": design["claim_guard"],
    }
    summary_path = RESULTS / f"opv_optical_external_{mode}_run.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
