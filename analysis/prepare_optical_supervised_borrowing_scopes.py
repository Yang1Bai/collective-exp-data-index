"""Freeze outcome-independent dynamic OOD scopes for focused optical borrowing."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
DRAW_PATH = HERE / "results" / "optical_transfer_method_discovery_draws.csv"
SCOPE_PATH = HERE / "results" / "optical_supervised_borrowing_scopes.csv"
MANIFEST_PATH = (
    HERE / "results" / "optical_supervised_borrowing_scopes_manifest.json"
)

RDLogger.DisableLog("rdApp.error")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_tie_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_scope(
    budget: int,
    repeat: int,
    target_keys: np.ndarray,
    fingerprints: list,
    draw_rows: pd.DataFrame,
    hard_fraction: float = 0.4,
) -> pd.DataFrame:
    training_keys = set(
        draw_rows.loc[
            (draw_rows["budget"] == budget)
            & (draw_rows["repeat"] == repeat)
            & (draw_rows["role"] == "training"),
            "target_key",
        ].astype(str)
    )
    excluded_keys = set(
        draw_rows.loc[
            (draw_rows["budget"] == budget)
            & (draw_rows["repeat"] == repeat),
            "target_key",
        ].astype(str)
    )
    key_to_index = {key: index for index, key in enumerate(target_keys)}
    training_indices = [key_to_index[key] for key in sorted(training_keys)]
    evaluation_indices = [
        index
        for index, key in enumerate(target_keys)
        if key not in excluded_keys
    ]
    if len(training_indices) != budget:
        raise RuntimeError(
            f"Training count drift for budget={budget}, repeat={repeat}"
        )
    if not evaluation_indices:
        raise RuntimeError(
            f"Empty evaluation pool for budget={budget}, repeat={repeat}"
        )

    training_fingerprints = [fingerprints[index] for index in training_indices]
    similarities = []
    for index in evaluation_indices:
        values = DataStructs.BulkTanimotoSimilarity(
            fingerprints[index], training_fingerprints
        )
        similarities.append(max(values) if values else 0.0)

    output = pd.DataFrame(
        {
            "budget": int(budget),
            "repeat": int(repeat),
            "target_key": target_keys[evaluation_indices],
            "max_similarity_to_labeled_target": similarities,
        }
    )
    hard_count = max(1, int(np.ceil(hard_fraction * len(output))))
    ordering = sorted(
        range(len(output)),
        key=lambda row: (
            float(output.iloc[row]["max_similarity_to_labeled_target"]),
            stable_tie_key(str(output.iloc[row]["target_key"])),
        ),
    )
    hard_rows = set(ordering[:hard_count])
    output["dynamic_hard_ood_40pct"] = [
        row in hard_rows for row in range(len(output))
    ]
    return output.sort_values("target_key").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=1)
    arguments = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["design_sha256"] != sha256(DESIGN_PATH):
        raise RuntimeError("Pair design changed after audit")
    if audit["recipient"]["metadata_sha256"] != sha256(METADATA_PATH):
        raise RuntimeError("Outcome-free recipient metadata changed")
    expected_draw_hash = str(
        config["development"]["reused_draw_sha256"]
    )
    if sha256(DRAW_PATH) != expected_draw_hash:
        raise RuntimeError("Frozen development draws changed")

    development = (
        pd.read_csv(METADATA_PATH)
        .query("split == 'development'")
        .sort_values("target_key")
        .reset_index(drop=True)
    )
    target_keys = development["target_key"].astype(str).to_numpy()
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    fingerprints = []
    for smiles in development["canonical_smiles"].astype(str):
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise RuntimeError(f"Audited molecule no longer parses: {smiles}")
        fingerprints.append(generator.GetFingerprint(molecule))

    draws = pd.read_csv(DRAW_PATH)
    budgets = [int(value) for value in config["development"]["label_budgets"]]
    repeats = int(config["development"]["draws_per_budget"])
    tasks = [
        (budget, repeat)
        for budget in budgets
        for repeat in range(repeats)
    ]
    frames = Parallel(n_jobs=arguments.jobs, verbose=10)(
        delayed(make_scope)(
            budget,
            repeat,
            target_keys,
            fingerprints,
            draws,
        )
        for budget, repeat in tasks
    )
    scopes = pd.concat(frames, ignore_index=True)
    scopes.to_csv(SCOPE_PATH, index=False, lineterminator="\n")

    group_counts = (
        scopes.groupby(["budget", "repeat"])
        .agg(
            evaluation_rows=("target_key", "size"),
            hard_rows=("dynamic_hard_ood_40pct", "sum"),
        )
        .reset_index()
    )
    for row in group_counts.itertuples(index=False):
        expected_hard = int(np.ceil(0.4 * int(row.evaluation_rows)))
        if int(row.hard_rows) != expected_hard:
            raise RuntimeError("Dynamic OOD count drift")

    manifest = {
        "status": "outcome-independent-dynamic-ood-scopes-frozen",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "focused_config_sha256": sha256(CONFIG_PATH),
        "pair_audit_sha256": sha256(AUDIT_PATH),
        "target_metadata_sha256": sha256(METADATA_PATH),
        "draw_sha256": sha256(DRAW_PATH),
        "implementation_sha256": sha256(Path(__file__)),
        "scope_sha256": sha256(SCOPE_PATH),
        "budgets": budgets,
        "draws_per_budget": repeats,
        "scope_rows": int(len(scopes)),
        "hard_scope_rows": int(scopes["dynamic_hard_ood_40pct"].sum()),
        "outcome_access": (
            "No recipient HER value, calculated descriptor, or blind outcome "
            "was loaded."
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
