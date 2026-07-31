"""Pretrain state-aligned Chemprop encoders without recipient outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import shutil
import tempfile
from pathlib import Path
from typing import Any

import chemprop
import lightning
import numpy as np
import pandas as pd
import rdkit
import sklearn
import torch
from chemprop import data, featurizers, models, nn
from lightning import pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy import stats
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold

import prepare_optical_photocatalysis_donor_features as base

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
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
EMBEDDING_PATH = (
    HERE / "results" / "optical_supervised_source_embeddings.npz"
)
OOF_PATH = HERE / "results" / "optical_supervised_source_oof.csv"
SUMMARY_PATH = (
    HERE / "results" / "optical_supervised_source_summary.json"
)
CHECKPOINT_DIR = (
    HERE / "results" / "optical_supervised_source_checkpoints"
)

RDLogger.DisableLog("rdApp.error")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    pl.seed_everything(seed, workers=True)
    torch.use_deterministic_algorithms(True, warn_only=True)


def support_values(
    target_smiles: list[str], source_smiles: list[str]
) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    source_fingerprints = []
    for smiles in source_smiles:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Source structure no longer parses: {smiles}")
        source_fingerprints.append(generator.GetFingerprint(molecule))
    output = np.zeros(len(target_smiles), dtype=np.float32)
    for row, smiles in enumerate(target_smiles):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Target structure no longer parses: {smiles}")
        values = DataStructs.BulkTanimotoSimilarity(
            generator.GetFingerprint(molecule), source_fingerprints
        )
        output[row] = max(values) if values else 0.0
    return output


def scale_support(values: np.ndarray, low: float, high: float) -> np.ndarray:
    if high <= low:
        raise ValueError("Support upper bound must exceed lower bound")
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def source_frame(
    raw: pd.DataFrame,
    mask: pd.Series,
    task_names: list[str],
    minimum_molecules: int,
) -> tuple[pd.DataFrame, list[str]]:
    rows = raw.loc[mask, ["canonical_smiles", *task_names]].copy()
    grouped = (
        rows.groupby("canonical_smiles", as_index=False)[task_names]
        .median()
        .sort_values("canonical_smiles")
        .reset_index(drop=True)
    )
    retained_tasks = [
        task
        for task in task_names
        if int(grouped[task].notna().sum()) >= minimum_molecules
    ]
    if not retained_tasks:
        raise RuntimeError("No source task passed the size gate")
    grouped = grouped[
        grouped[retained_tasks].notna().any(axis=1)
    ].reset_index(drop=True)
    return grouped[["canonical_smiles", *retained_tasks]], retained_tasks


def scaffold_groups(smiles_values: list[str]) -> np.ndarray:
    output = []
    for smiles in smiles_values:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Source structure no longer parses: {smiles}")
        output.append(base.scaffold_key(molecule, smiles))
    return np.asarray(output, dtype=object)


def shuffled_labels(values: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    output = values.copy()
    for column in range(values.shape[1]):
        observed = np.flatnonzero(np.isfinite(values[:, column]))
        output[observed, column] = values[
            rng.permutation(observed), column
        ]
    return output


def make_dataset(
    smiles: list[str],
    targets: np.ndarray,
    graph_featurizer: featurizers.SimpleMoleculeMolGraphFeaturizer,
) -> data.MoleculeDataset:
    datapoints = [
        data.MoleculeDatapoint.from_smi(smi, target)
        for smi, target in zip(smiles, targets, strict=True)
    ]
    return data.MoleculeDataset(datapoints, graph_featurizer)


def build_model(
    tasks: int,
    scaler,
    settings: dict[str, Any],
) -> models.MPNN:
    hidden = int(settings["hidden_dimension"])
    message_passing = nn.BondMessagePassing(
        d_h=hidden,
        depth=int(settings["message_passing_depth"]),
        dropout=float(settings["dropout"]),
    )
    aggregation = nn.MeanAggregation()
    output_transform = nn.transforms.UnscaleTransform.from_standard_scaler(
        scaler
    )
    predictor = nn.RegressionFFN(
        n_tasks=tasks,
        input_dim=hidden,
        hidden_dim=hidden,
        n_layers=1,
        dropout=float(settings["dropout"]),
        output_transform=output_transform,
    )
    return models.MPNN(
        message_passing,
        aggregation,
        predictor,
        batch_norm=bool(settings["batch_normalization"]),
        warmup_epochs=2,
        init_lr=float(settings["learning_rate"]) / 10.0,
        max_lr=float(settings["learning_rate"]),
        final_lr=float(settings["learning_rate"]) / 10.0,
    )


def trainer_for(
    accelerator: str,
    maximum_epochs: int,
    minimum_epochs: int,
    callbacks: list,
    has_validation: bool,
) -> pl.Trainer:
    return pl.Trainer(
        accelerator=accelerator,
        devices=1,
        max_epochs=maximum_epochs,
        min_epochs=minimum_epochs,
        callbacks=callbacks,
        logger=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        enable_checkpointing=bool(callbacks),
        deterministic=True,
        num_sanity_val_steps=0 if has_validation else 0,
        log_every_n_steps=50,
    )


def train_model(
    train_smiles: list[str],
    train_y: np.ndarray,
    validation_smiles: list[str] | None,
    validation_y: np.ndarray | None,
    settings: dict[str, Any],
    seed: int,
    accelerator: str,
    fixed_epochs: int | None = None,
) -> tuple[models.MPNN, int, float]:
    set_seed(seed)
    graph_featurizer = (
        featurizers.SimpleMoleculeMolGraphFeaturizer()
    )
    training = make_dataset(train_smiles, train_y, graph_featurizer)
    scaler = training.normalize_targets()
    training_loader = data.build_dataloader(
        training,
        batch_size=int(settings["batch_size"]),
        num_workers=0,
        seed=seed,
        shuffle=True,
    )
    model = build_model(train_y.shape[1], scaler, settings)
    if fixed_epochs is not None:
        trainer = trainer_for(
            accelerator,
            int(fixed_epochs),
            int(fixed_epochs),
            [],
            has_validation=False,
        )
        trainer.fit(model, training_loader)
        return model, int(fixed_epochs), float("nan")

    if validation_smiles is None or validation_y is None:
        raise ValueError("Validation data are required for early stopping")
    validation = make_dataset(
        validation_smiles, validation_y, graph_featurizer
    )
    validation.normalize_targets(scaler)
    validation_loader = data.build_dataloader(
        validation,
        batch_size=int(settings["batch_size"]),
        num_workers=0,
        shuffle=False,
    )
    checkpoint_root = Path(
        tempfile.mkdtemp(
            prefix=f"chemprop-{seed}-",
            dir=os.environ.get("JOBLIB_TEMP_FOLDER"),
        )
    )
    checkpoint = ModelCheckpoint(
        dirpath=checkpoint_root,
        filename="best",
        monitor="val_loss",
        mode="min",
        save_top_k=1,
    )
    early_stopping = EarlyStopping(
        monitor="val_loss",
        mode="min",
        patience=int(settings["early_stopping_patience"]),
        min_delta=1e-6,
    )
    trainer = trainer_for(
        accelerator,
        int(settings["maximum_epochs"]),
        int(settings["minimum_epochs"]),
        [checkpoint, early_stopping],
        has_validation=True,
    )
    try:
        trainer.fit(model, training_loader, validation_loader)
        if not checkpoint.best_model_path:
            raise RuntimeError("Chemprop did not write a best checkpoint")
        payload = torch.load(
            checkpoint.best_model_path,
            map_location="cpu",
        )
        model.load_state_dict(payload["state_dict"])
        best_epoch = int(payload["epoch"]) + 1
        best_loss = float(checkpoint.best_model_score)
    finally:
        shutil.rmtree(checkpoint_root, ignore_errors=True)
    return model, best_epoch, best_loss


def predict_and_encode(
    model: models.MPNN,
    smiles: list[str],
    tasks: int,
    accelerator: str,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    device = torch.device("cuda" if accelerator == "gpu" else "cpu")
    graph_featurizer = (
        featurizers.SimpleMoleculeMolGraphFeaturizer()
    )
    dummy = np.zeros((len(smiles), tasks), dtype=np.float32)
    dataset = make_dataset(smiles, dummy, graph_featurizer)
    loader = data.build_dataloader(
        dataset,
        batch_size=batch_size,
        num_workers=0,
        shuffle=False,
    )
    model = model.to(device)
    model.eval()
    predictions = []
    encodings = []
    with torch.no_grad():
        for batch in loader:
            batch_graph = batch.bmg
            batch_graph.to(device)
            atom_descriptors = (
                batch.V_d.to(device) if batch.V_d is not None else None
            )
            extra_descriptors = (
                batch.X_d.to(device) if batch.X_d is not None else None
            )
            predictions.append(
                model(
                    batch_graph,
                    atom_descriptors,
                    extra_descriptors,
                )
                .cpu()
                .numpy()
            )
            encodings.append(
                model.encoding(
                    batch_graph,
                    atom_descriptors,
                    extra_descriptors,
                    i=0,
                )
                .cpu()
                .numpy()
            )
    return np.vstack(predictions), np.vstack(encodings)


def portable_state_dict(model: models.MPNN) -> dict[str, torch.Tensor]:
    return {
        key: value.detach().cpu()
        for key, value in model.state_dict().items()
    }


def fit_scope(
    scope_name: str,
    frame: pd.DataFrame,
    task_names: list[str],
    target_smiles: list[str],
    settings: dict[str, Any],
    accelerator: str,
    final_seeds: list[int],
) -> tuple[list[np.ndarray], dict[str, Any], pd.DataFrame]:
    smiles = frame["canonical_smiles"].astype(str).tolist()
    y = frame[task_names].to_numpy(dtype=np.float32)
    groups = scaffold_groups(smiles)
    splitter = GroupKFold(
        n_splits=int(settings["validation_folds"]),
        shuffle=True,
        random_state=20260726,
    )
    oof = np.full_like(y, np.nan, dtype=np.float32)
    fold_labels = np.full(len(y), -1, dtype=int)
    best_epochs = []
    best_losses = []
    for fold, (train_rows, validation_rows) in enumerate(
        splitter.split(np.zeros(len(y)), groups=groups)
    ):
        model, best_epoch, best_loss = train_model(
            [smiles[row] for row in train_rows],
            y[train_rows],
            [smiles[row] for row in validation_rows],
            y[validation_rows],
            settings,
            seed=2026072600 + 100 * fold + 1,
            accelerator=accelerator,
        )
        prediction, _ = predict_and_encode(
            model,
            [smiles[row] for row in validation_rows],
            len(task_names),
            accelerator,
            int(settings["batch_size"]),
        )
        oof[validation_rows] = prediction
        fold_labels[validation_rows] = fold
        best_epochs.append(best_epoch)
        best_losses.append(best_loss)
    if not np.isfinite(oof[np.isfinite(y)]).all():
        raise RuntimeError(f"Incomplete source OOF predictions for {scope_name}")

    task_summary: dict[str, Any] = {}
    admitted_columns = []
    for column, task in enumerate(task_names):
        observed = np.isfinite(y[:, column])
        r2 = float(r2_score(y[observed, column], oof[observed, column]))
        spearman = float(
            stats.spearmanr(
                y[observed, column], oof[observed, column]
            ).statistic
        )
        bootstrap_seed = int(
            hashlib.sha256(
                f"{scope_name}|{task}".encode("utf-8")
            ).hexdigest()[:8],
            16,
        )
        bootstrap_ci = base.bootstrap_spearman_lower(
            y[observed, column],
            oof[observed, column],
            groups[observed],
            bootstrap_seed,
        )
        gate = settings["source_skill_gate"]
        admitted = bool(
            r2 > float(gate["oof_r2_greater_than"])
            and spearman > float(gate["oof_spearman_greater_than"])
            and bootstrap_ci[0]
            > float(
                gate[
                    "bootstrap_95pct_lower_spearman_greater_than"
                ]
            )
        )
        task_summary[task] = {
            "unique_molecules": int(observed.sum()),
            "oof_r2": r2,
            "oof_spearman": spearman,
            "scaffold_bootstrap_spearman_ci95": list(bootstrap_ci),
            "admitted": admitted,
        }
        if admitted:
            admitted_columns.append(column)
    if not admitted_columns:
        raise RuntimeError(f"No source task admitted for {scope_name}")
    final_tasks = [task_names[column] for column in admitted_columns]
    final_y = y[:, admitted_columns]
    final_epoch = max(
        int(settings["minimum_epochs"]),
        int(np.median(best_epochs)),
    )

    embeddings = []
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    for seed in final_seeds:
        model, _, _ = train_model(
            smiles,
            final_y,
            None,
            None,
            settings,
            seed=seed,
            accelerator=accelerator,
            fixed_epochs=final_epoch,
        )
        _, encoding = predict_and_encode(
            model,
            target_smiles,
            len(final_tasks),
            accelerator,
            int(settings["batch_size"]),
        )
        embeddings.append(encoding.astype(np.float32))
        checkpoint_path = CHECKPOINT_DIR / f"{scope_name}_seed{seed}.pt"
        torch.save(
            {
                "state_dict": portable_state_dict(model),
                "scope": scope_name,
                "tasks": final_tasks,
                "epochs": final_epoch,
                "seed": seed,
                "shuffled": False,
                "chemprop_version": chemprop.__version__,
                "config_sha256": sha256(CONFIG_PATH),
            },
            checkpoint_path,
        )

    oof_frames = []
    for column, task in enumerate(task_names):
        observed = np.isfinite(y[:, column])
        oof_frames.append(
            pd.DataFrame(
                {
                    "scope": scope_name,
                    "task": task,
                    "canonical_smiles": np.asarray(smiles)[observed],
                    "scaffold": groups[observed],
                    "fold": fold_labels[observed],
                    "observed": y[observed, column],
                    "predicted": oof[observed, column],
                    "shuffled": False,
                }
            )
        )
    summary = {
        "rows": int(len(frame)),
        "unique_scaffolds": int(len(set(groups.astype(str)))),
        "tasks": task_summary,
        "best_epochs_by_fold": best_epochs,
        "best_validation_losses_by_fold": best_losses,
        "final_epoch": final_epoch,
        "admitted_task_count": int(len(admitted_columns)),
        "final_training_tasks": final_tasks,
    }
    return embeddings, summary, pd.concat(oof_frames, ignore_index=True)


def fit_shuffled_scope(
    scope_name: str,
    frame: pd.DataFrame,
    task_names: list[str],
    target_smiles: list[str],
    settings: dict[str, Any],
    accelerator: str,
    final_seeds: list[int],
    fixed_epoch: int,
) -> tuple[list[np.ndarray], dict[str, Any]]:
    smiles = frame["canonical_smiles"].astype(str).tolist()
    y = frame[task_names].to_numpy(dtype=np.float32)
    embeddings = []
    for seed in final_seeds:
        shuffled_y = shuffled_labels(y, seed)
        model, _, _ = train_model(
            smiles,
            shuffled_y,
            None,
            None,
            settings,
            seed=seed,
            accelerator=accelerator,
            fixed_epochs=fixed_epoch,
        )
        _, encoding = predict_and_encode(
            model,
            target_smiles,
            len(task_names),
            accelerator,
            int(settings["batch_size"]),
        )
        embeddings.append(encoding.astype(np.float32))
        checkpoint_path = (
            CHECKPOINT_DIR / f"{scope_name}_shuffled_seed{seed}.pt"
        )
        torch.save(
            {
                "state_dict": portable_state_dict(model),
                "scope": f"{scope_name}_shuffled",
                "tasks": task_names,
                "epochs": int(fixed_epoch),
                "seed": seed,
                "shuffled": True,
                "chemprop_version": chemprop.__version__,
                "config_sha256": sha256(CONFIG_PATH),
            },
            checkpoint_path,
        )
    summary = {
        "rows": int(len(frame)),
        "tasks": {
            task: {
                "unique_molecules": int(frame[task].notna().sum())
            }
            for task in task_names
        },
        "final_epoch": int(fixed_epoch),
        "control": (
            "Source labels were independently permuted within each task; "
            "the molecular graphs, architecture, task masks, epochs and "
            "recipient structures match the real source expert."
        ),
    }
    return embeddings, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device", choices=["auto", "cpu", "cuda"], default="auto"
    )
    arguments = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["design_sha256"] != sha256(DESIGN_PATH):
        raise RuntimeError("Pair design changed after audit")
    if audit["recipient"]["metadata_sha256"] != sha256(METADATA_PATH):
        raise RuntimeError("Outcome-free target metadata changed")
    if design["source"]["required_sha256"] != sha256(SOURCE_PATH):
        raise RuntimeError("Source data changed")
    if arguments.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    accelerator = (
        "gpu"
        if arguments.device == "cuda"
        or (arguments.device == "auto" and torch.cuda.is_available())
        else "cpu"
    )

    metadata = pd.read_csv(METADATA_PATH).sort_values("target_key")
    recipient_smiles = set(metadata["canonical_smiles"].astype(str))
    target_smiles = metadata["canonical_smiles"].astype(str).tolist()
    task_names = list(config["source_tasks"])
    raw = pd.read_csv(
        SOURCE_PATH,
        usecols=["Chromophore", "Solvent", *task_names],
    )
    parsed = raw["Chromophore"].map(base.canonicalize)
    raw["canonical_smiles"] = parsed.map(lambda value: value[0])
    raw = raw[
        raw["canonical_smiles"].notna()
        & ~raw["canonical_smiles"].isin(recipient_smiles)
    ].copy()
    for task in task_names:
        raw[task] = base.transform_property(task, raw[task])

    solvent = raw["Solvent"].fillna("").astype(str).str.strip()
    chromophore = raw["Chromophore"].fillna("").astype(str).str.strip()
    aqueous_tokens = set(
        config["source_scopes"]["aqueous_small_alcohol"][
            "solvent_tokens"
        ]
    )
    scope_masks = {
        "aqueous_small_alcohol": solvent.isin(aqueous_tokens),
        "self_host_solid": solvent.eq(chromophore),
        "global_state_blind": pd.Series(True, index=raw.index),
    }
    minimum = int(config["source_task_minimum_unique_molecules"])
    scope_frames: dict[str, pd.DataFrame] = {}
    scope_tasks: dict[str, list[str]] = {}
    for scope, mask in scope_masks.items():
        frame, tasks = source_frame(raw, mask, task_names, minimum)
        scope_frames[scope] = frame
        scope_tasks[scope] = tasks

    settings = config["source_encoder"]
    if str(settings["implementation"]) != "Chemprop 2.1.2":
        raise RuntimeError("Source encoder implementation drift")
    if chemprop.__version__ != "2.1.2":
        raise RuntimeError("Chemprop version drift")
    if int(
        settings["source_skill_gate"]["scaffold_bootstrap_replicates"]
    ) != int(base.N_BOOTSTRAP):
        raise RuntimeError("Source bootstrap implementation/config drift")
    final_seeds = [int(value) for value in settings["final_seeds"]]
    shuffled_seeds = [
        int(value) for value in settings["shuffled_control_seeds"]
    ]
    output_arrays: dict[str, np.ndarray] = {
        "target_key": metadata["target_key"].astype(str).to_numpy(),
    }
    summaries: dict[str, Any] = {}
    oof_frames = []
    fitted: dict[str, list[np.ndarray]] = {}
    for scope in [
        "aqueous_small_alcohol",
        "self_host_solid",
        "global_state_blind",
    ]:
        embeddings, summary, oof = fit_scope(
            scope,
            scope_frames[scope],
            scope_tasks[scope],
            target_smiles,
            settings,
            accelerator,
            final_seeds,
        )
        fitted[scope] = embeddings
        summaries[scope] = summary
        oof_frames.append(oof)

    shuffled: dict[str, list[np.ndarray]] = {}
    for scope in ["aqueous_small_alcohol", "self_host_solid"]:
        admitted_tasks = [
            task
            for task, item in summaries[scope]["tasks"].items()
            if bool(item["admitted"])
        ]
        embeddings, summary = fit_shuffled_scope(
            scope,
            scope_frames[scope],
            admitted_tasks,
            target_smiles,
            settings,
            accelerator,
            shuffled_seeds,
            fixed_epoch=int(summaries[scope]["final_epoch"]),
        )
        shuffled[scope] = embeddings
        summaries[f"{scope}_shuffled"] = summary

    for seed_index, seed in enumerate(final_seeds):
        output_arrays[f"aligned_seed_{seed}"] = np.hstack(
            [
                fitted["aqueous_small_alcohol"][seed_index],
                fitted["self_host_solid"][seed_index],
            ]
        ).astype(np.float32)
        output_arrays[f"global_seed_{seed}"] = fitted[
            "global_state_blind"
        ][seed_index].astype(np.float32)
    for seed_index, seed in enumerate(shuffled_seeds):
        output_arrays[f"shuffled_seed_{seed}"] = np.hstack(
            [
                shuffled["aqueous_small_alcohol"][seed_index],
                shuffled["self_host_solid"][seed_index],
            ]
        ).astype(np.float32)

    aqueous_support = support_values(
        target_smiles,
        scope_frames["aqueous_small_alcohol"][
            "canonical_smiles"
        ].astype(str).tolist(),
    )
    solid_support = support_values(
        target_smiles,
        scope_frames["self_host_solid"][
            "canonical_smiles"
        ].astype(str).tolist(),
    )
    reliability_settings = config["source_reliability"]
    low = float(reliability_settings["zero_support_tanimoto"])
    high = float(reliability_settings["full_support_tanimoto"])
    reliability = np.sqrt(
        scale_support(aqueous_support, low, high)
        * scale_support(solid_support, low, high)
    )
    output_arrays["support_aqueous_small_alcohol"] = aqueous_support
    output_arrays["support_self_host_solid"] = solid_support
    output_arrays["state_aligned_reliability"] = reliability.astype(
        np.float32
    )
    np.savez_compressed(EMBEDDING_PATH, **output_arrays)
    pd.concat(oof_frames, ignore_index=True).to_csv(
        OOF_PATH, index=False, lineterminator="\n"
    )

    minimum_tasks = int(
        settings["source_skill_gate"]["minimum_admitted_tasks_per_scope"]
    )
    primary_scope_gate = all(
        summaries[scope]["admitted_task_count"] >= minimum_tasks
        for scope in ["aqueous_small_alcohol", "self_host_solid"]
    )
    checkpoints = sorted(CHECKPOINT_DIR.glob("*.pt"))
    summary = {
        "status": (
            "source-representation-ready"
            if primary_scope_gate
            else "source-skill-gate-failed"
        ),
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "focused_config_sha256": sha256(CONFIG_PATH),
        "pair_audit_sha256": sha256(AUDIT_PATH),
        "target_metadata_sha256": sha256(METADATA_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "implementation_sha256": sha256(Path(__file__)),
        "embedding_sha256": sha256(EMBEDDING_PATH),
        "oof_sha256": sha256(OOF_PATH),
        "checkpoint_sha256": {
            path.name: sha256(path) for path in checkpoints
        },
        "target_rows": int(len(metadata)),
        "source_scopes": summaries,
        "primary_scope_gate_passed": primary_scope_gate,
        "embedding_arrays": {
            key: list(value.shape)
            for key, value in output_arrays.items()
            if key != "target_key"
        },
        "outcome_access": (
            "Only donor optical outcomes and outcome-free recipient "
            "structures were loaded; no recipient HER outcome was accessed."
        ),
        "environment": {
            "python": platform.python_version(),
            "chemprop": chemprop.__version__,
            "lightning": lightning.__version__,
            "torch": torch.__version__,
            "accelerator": accelerator,
            "cuda_available": bool(torch.cuda.is_available()),
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
    if not primary_scope_gate:
        raise SystemExit("Primary state-aligned source skill gate failed")


if __name__ == "__main__":
    main()
