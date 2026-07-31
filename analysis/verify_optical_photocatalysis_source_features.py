"""Independently verify the donor-only optical feature artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
SUMMARY_PATH = HERE / "results" / "optical_photocatalysis_source_skill.json"
FEATURE_PATH = HERE / "results" / "optical_photocatalysis_donor_features.csv"
OOF_PATH = HERE / "results" / "optical_photocatalysis_donor_oof_predictions.csv"
VERIFIED_PATH = (
    HERE / "results" / "optical_photocatalysis_source_features_VERIFIED.json"
)
SEED = 20260724
N_BOOTSTRAP = 1000
RANK_SERIALIZATION_ATOL = 5e-5


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bootstrap_spearman_ci(
    truth: np.ndarray,
    prediction: np.ndarray,
    groups: np.ndarray,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    groups = groups.astype(str)
    unique_groups = np.asarray(sorted(set(groups)))
    group_rows = {
        group: np.flatnonzero(groups == group) for group in unique_groups
    }
    estimates = np.full(N_BOOTSTRAP, np.nan)
    for repeat in range(N_BOOTSTRAP):
        sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        indices = np.concatenate([group_rows[group] for group in sampled])
        value = stats.spearmanr(
            truth[indices], prediction[indices]
        ).statistic
        if np.isfinite(value):
            estimates[repeat] = value
    finite = estimates[np.isfinite(estimates)]
    if not len(finite):
        return np.full(3, np.nan)
    return np.quantile(finite, [0.025, 0.5, 0.975])


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    metadata = pd.read_csv(METADATA_PATH)
    features = pd.read_csv(FEATURE_PATH)
    oof = pd.read_csv(OOF_PATH)

    expected_hashes = {
        "design_sha256": file_hash(DESIGN_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "feature_sha256": file_hash(FEATURE_PATH),
        "oof_sha256": file_hash(OOF_PATH),
    }
    for field, expected in expected_hashes.items():
        if summary[field] != expected:
            raise AssertionError(f"Hash mismatch: {field}")
    if audit["design_sha256"] != expected_hashes["design_sha256"]:
        raise AssertionError("Audit design hash mismatch")
    if len(features) != len(metadata) or int(summary["feature_rows"]) != len(
        metadata
    ):
        raise AssertionError("Feature row count mismatch")
    if not features["target_key"].equals(metadata["target_key"]):
        raise AssertionError("Feature and metadata target keys do not align")
    if features["target_key"].duplicated().any():
        raise AssertionError("Duplicate target feature key")

    gate = design["donor_modeling"]["property_admission_gate"]
    recomputed_admitted: list[str] = []
    recomputed: dict[str, dict[str, object]] = {}
    for property_index, (property_name, reported) in enumerate(
        summary["properties"].items()
    ):
        rows = oof[oof["property"] == property_name].copy()
        if len(rows) != int(reported["unique_molecules"]):
            raise AssertionError(f"OOF row count mismatch: {property_name}")
        if rows["canonical_smiles"].duplicated().any():
            raise AssertionError(f"Duplicate OOF molecule: {property_name}")
        if rows["fold"].nunique() != 5:
            raise AssertionError(f"Expected five OOF folds: {property_name}")
        observed = rows["observed"].to_numpy(float)
        predicted = rows["predicted"].to_numpy(float)
        if not np.isfinite(observed).all() or not np.isfinite(predicted).all():
            raise AssertionError(f"Nonfinite OOF value: {property_name}")
        r2 = float(r2_score(observed, predicted))
        spearman = float(stats.spearmanr(observed, predicted).statistic)
        bootstrap_ci = bootstrap_spearman_ci(
            observed,
            predicted,
            rows["scaffold"].astype(str).to_numpy(),
            SEED + 1000 + property_index,
        )
        if not np.isclose(r2, float(reported["oof_r2"]), atol=1e-12):
            raise AssertionError(f"OOF R2 mismatch: {property_name}")
        spearman_delta = abs(spearman - float(reported["oof_spearman"]))
        if spearman_delta > RANK_SERIALIZATION_ATOL:
            raise AssertionError(f"OOF Spearman mismatch: {property_name}")
        reported_ci = np.asarray(
            reported["scaffold_bootstrap_spearman_ci95"], dtype=float
        )
        bootstrap_delta = float(np.max(np.abs(bootstrap_ci - reported_ci)))
        if bootstrap_delta > RANK_SERIALIZATION_ATOL:
            raise AssertionError(
                f"Bootstrap Spearman interval mismatch: {property_name}"
            )
        ci_low = float(bootstrap_ci[0])
        admitted = bool(
            len(rows) >= int(gate["minimum_unique_molecules"])
            and r2 > float(gate["oof_r2_greater_than"])
            and spearman > float(gate["oof_spearman_greater_than"])
            and ci_low
            > float(gate["bootstrap_95pct_lower_spearman_greater_than"])
        )
        if admitted != bool(reported["admitted_by_source_only_gate"]):
            raise AssertionError(f"Admission mismatch: {property_name}")
        slug = str(reported["slug"])
        for column in (f"pred_{slug}", f"unc_{slug}"):
            if column not in features:
                raise AssertionError(f"Missing feature column: {column}")
            if not np.isfinite(features[column].to_numpy(float)).all():
                raise AssertionError(f"Nonfinite feature column: {column}")
        if admitted:
            recomputed_admitted.append(property_name)
        recomputed[property_name] = {
            "oof_r2": r2,
            "oof_spearman": spearman,
            "reported_oof_spearman": float(reported["oof_spearman"]),
            "absolute_spearman_delta_after_csv": spearman_delta,
            "scaffold_bootstrap_spearman_ci95": bootstrap_ci.tolist(),
            "reported_scaffold_bootstrap_spearman_ci95": reported_ci.tolist(),
            "maximum_absolute_bootstrap_ci_delta_after_csv": bootstrap_delta,
            "admitted": admitted,
        }

    if recomputed_admitted != list(summary["admitted_properties"]):
        raise AssertionError("Admitted property list mismatch")
    expected_status = (
        "source-features-ready" if recomputed_admitted else "source-abstained"
    )
    if summary["status"] != expected_status:
        raise AssertionError("Source summary status mismatch")

    verified = {
        "status": "verified-complete",
        "verification_mode": "portable-after-remote",
        **expected_hashes,
        "source_summary_sha256": file_hash(SUMMARY_PATH),
        "feature_rows": int(len(features)),
        "oof_rows": int(len(oof)),
        "admitted_properties": recomputed_admitted,
        "recomputed_metrics": recomputed,
        "rank_serialization_absolute_tolerance": RANK_SERIALIZATION_ATOL,
        "verifier_amendment": (
            "A 5e-5 absolute tolerance is used only when comparing Spearman "
            "statistics before and after OOF CSV serialization. R2 values, file "
            "hashes, feature values, gates, and admission decisions are unchanged."
        ),
        "outcome_guard": (
            "Verification used donor optical outcomes and outcome-free recipient "
            "metadata only; recipient HER values were not loaded."
        ),
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
