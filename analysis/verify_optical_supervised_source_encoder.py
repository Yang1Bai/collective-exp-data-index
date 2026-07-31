"""Independently verify focused optical source representations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
EMBEDDING_PATH = (
    HERE / "results" / "optical_supervised_source_embeddings.npz"
)
OOF_PATH = HERE / "results" / "optical_supervised_source_oof.csv"
SUMMARY_PATH = (
    HERE / "results" / "optical_supervised_source_summary.json"
)
IMPLEMENTATION_PATH = HERE / "pretrain_optical_source_chemprop.py"
CHECKPOINT_DIR = (
    HERE / "results" / "optical_supervised_source_checkpoints"
)
VERIFIED_PATH = (
    HERE / "results" / "optical_supervised_source_VERIFIED.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float, tolerance: float = 1e-7) -> bool:
    return bool(
        np.isclose(left, right, atol=tolerance, rtol=tolerance)
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    if summary["focused_config_sha256"] != sha256(CONFIG_PATH):
        raise AssertionError("Source summary predates focused config")
    if summary["embedding_sha256"] != sha256(EMBEDDING_PATH):
        raise AssertionError("Source embedding hash mismatch")
    if summary["oof_sha256"] != sha256(OOF_PATH):
        raise AssertionError("Source OOF hash mismatch")
    if summary["implementation_sha256"] != sha256(IMPLEMENTATION_PATH):
        raise AssertionError("Source encoder implementation hash mismatch")
    if summary["environment"]["chemprop"] != "2.1.2":
        raise AssertionError("Chemprop version mismatch")
    if not bool(summary["primary_scope_gate_passed"]):
        raise AssertionError("Primary source skill gate did not pass")

    checkpoint_hashes = summary["checkpoint_sha256"]
    for name, expected in checkpoint_hashes.items():
        path = CHECKPOINT_DIR / name
        if not path.exists() or sha256(path) != expected:
            raise AssertionError(f"Checkpoint mismatch: {name}")

    metadata = pd.read_csv(METADATA_PATH).sort_values("target_key")
    settings = config["source_encoder"]
    final_seeds = [int(value) for value in settings["final_seeds"]]
    shuffled_seeds = [
        int(value) for value in settings["shuffled_control_seeds"]
    ]
    latent = int(settings["latent_dimension"])
    # The archive hash is checked above before pickle-enabled loading. Pandas
    # 2.3 serializes its string-backed target-key array with NumPy object
    # dtype, even though every member is a plain string. Permit that one
    # trusted representation, then reject any non-string object immediately.
    with np.load(EMBEDDING_PATH, allow_pickle=True) as arrays:
        raw_keys = arrays["target_key"]
        if raw_keys.dtype.kind not in {"O", "U", "S"}:
            raise AssertionError("Unexpected target-key dtype")
        if raw_keys.dtype.kind == "O" and not all(
            isinstance(value, str) for value in raw_keys.tolist()
        ):
            raise AssertionError("Non-string object in target-key array")
        keys = raw_keys.astype(str)
        if list(keys) != list(metadata["target_key"].astype(str)):
            raise AssertionError("Embedding target-key order mismatch")
        expected_arrays = {
            **{
                f"aligned_seed_{seed}": (len(metadata), 2 * latent)
                for seed in final_seeds
            },
            **{
                f"global_seed_{seed}": (len(metadata), latent)
                for seed in final_seeds
            },
            **{
                f"shuffled_seed_{seed}": (len(metadata), 2 * latent)
                for seed in shuffled_seeds
            },
        }
        for name, shape in expected_arrays.items():
            if name not in arrays.files:
                raise AssertionError(f"Missing embedding array: {name}")
            if arrays[name].shape != shape:
                raise AssertionError(f"Embedding shape drift: {name}")
            if arrays[name].dtype.kind not in {"f", "i", "u"}:
                raise AssertionError(f"Nonnumeric embedding dtype: {name}")
            if not np.isfinite(arrays[name]).all():
                raise AssertionError(f"Nonfinite embedding: {name}")
            if float(np.std(arrays[name])) <= 1e-6:
                raise AssertionError(f"Collapsed embedding: {name}")

        aqueous_raw = arrays["support_aqueous_small_alcohol"]
        solid_raw = arrays["support_self_host_solid"]
        reliability_raw = arrays["state_aligned_reliability"]
        for name in [
            "support_aqueous_small_alcohol",
            "support_self_host_solid",
            "state_aligned_reliability",
        ]:
            if arrays[name].dtype.kind not in {"f", "i", "u"}:
                raise AssertionError(f"Nonnumeric support dtype: {name}")
        low = float(
            config["source_reliability"]["zero_support_tanimoto"]
        )
        high = float(
            config["source_reliability"]["full_support_tanimoto"]
        )
        # Reproduce the producer's float32 threshold arithmetic before any
        # diagnostic upcast. Upcasting first turns float32 values representing
        # the exact 0.2 boundary into tiny positives and the subsequent square
        # root amplifies that representation artifact.
        expected_reliability = np.sqrt(
            np.clip((aqueous_raw - low) / (high - low), 0.0, 1.0)
            * np.clip((solid_raw - low) / (high - low), 0.0, 1.0)
        ).astype(np.float32)
        if not np.array_equal(
            reliability_raw.astype(np.float32), expected_reliability
        ):
            raise AssertionError("State-aligned reliability mismatch")
        reliability = reliability_raw.astype(float)
        if (reliability < 0).any() or (reliability > 1).any():
            raise AssertionError("Reliability outside [0, 1]")

    oof = pd.read_csv(OOF_PATH)
    required_columns = {
        "scope",
        "task",
        "canonical_smiles",
        "scaffold",
        "fold",
        "observed",
        "predicted",
        "shuffled",
    }
    if not required_columns.issubset(oof.columns):
        raise AssertionError("Source OOF schema drift")
    for scope in [
        "aqueous_small_alcohol",
        "self_host_solid",
        "global_state_blind",
    ]:
        scope_rows = oof[(oof["scope"] == scope) & ~oof["shuffled"]]
        scope_summary = summary["source_scopes"][scope]
        admitted = 0
        for task, task_summary in scope_summary["tasks"].items():
            rows = scope_rows[scope_rows["task"] == task]
            if len(rows) != int(task_summary["unique_molecules"]):
                raise AssertionError(f"Source OOF row drift: {scope}/{task}")
            r2 = float(r2_score(rows["observed"], rows["predicted"]))
            spearman = float(
                stats.spearmanr(
                    rows["observed"], rows["predicted"]
                ).statistic
            )
            if not close(r2, float(task_summary["oof_r2"])):
                raise AssertionError(f"Source OOF R2 mismatch: {scope}/{task}")
            if not close(
                spearman, float(task_summary["oof_spearman"])
            ):
                raise AssertionError(
                    f"Source OOF Spearman mismatch: {scope}/{task}"
                )
            gate = settings["source_skill_gate"]
            expected_admitted = bool(
                r2 > float(gate["oof_r2_greater_than"])
                and spearman > float(gate["oof_spearman_greater_than"])
                and float(
                    task_summary[
                        "scaffold_bootstrap_spearman_ci95"
                    ][0]
                )
                > float(
                    gate[
                        "bootstrap_95pct_lower_spearman_greater_than"
                    ]
                )
            )
            if bool(task_summary["admitted"]) != expected_admitted:
                raise AssertionError(
                    f"Source task gate mismatch: {scope}/{task}"
                )
            admitted += int(expected_admitted)
        if admitted != int(scope_summary["admitted_task_count"]):
            raise AssertionError(f"Admitted task count mismatch: {scope}")
        expected_final_tasks = [
            task
            for task, item in scope_summary["tasks"].items()
            if bool(item["admitted"])
        ]
        if scope_summary["final_training_tasks"] != expected_final_tasks:
            raise AssertionError(
                f"Failed source task entered final encoder: {scope}"
            )
        if scope in {"aqueous_small_alcohol", "self_host_solid"}:
            shuffled_summary = summary["source_scopes"][
                f"{scope}_shuffled"
            ]
            if list(shuffled_summary["tasks"]) != expected_final_tasks:
                raise AssertionError(
                    f"Shuffled control task mismatch: {scope}"
                )
            if int(shuffled_summary["final_epoch"]) != int(
                scope_summary["final_epoch"]
            ):
                raise AssertionError(
                    f"Shuffled control epoch mismatch: {scope}"
                )

    script_text = (
        IMPLEMENTATION_PATH.read_text(encoding="utf-8")
    )
    if "SC-012-D1SC02150H-s006.csv" in script_text:
        raise AssertionError("Blind target path appears in source encoder")
    verified = {
        "status": "verified-complete-source-representation",
        "focused_config_sha256": sha256(CONFIG_PATH),
        "source_summary_sha256": sha256(SUMMARY_PATH),
        "embedding_sha256": sha256(EMBEDDING_PATH),
        "oof_sha256": sha256(OOF_PATH),
        "checkpoint_count": len(checkpoint_hashes),
        "target_rows": int(len(metadata)),
        "blind_outcome_access": (
            "No blind HER outcome was opened or required for verification."
        ),
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
