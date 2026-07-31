"""Formal chemical-OOD PCE benchmark for band-gap knowledge borrowing."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_extraction import FeatureHasher
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import spearmanr

import bandgap_borrowing_common as bg


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN = HERE / "BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json"
SOURCE_SUMMARY = RESULTS / "bandgap_external_source_skill_summary.json"
SOURCE_FEATURES = RESULTS / "bandgap_external_donor_features.csv"
SPLIT_JSON = RESULTS / "bandgap_perovskite_pce_ood_split.json"
METRICS_CSV = RESULTS / "bandgap_perovskite_pce_ood_metrics.csv"
PREDICTIONS_CSV = RESULTS / "bandgap_perovskite_pce_ood_predictions.csv"
BOOTSTRAP_CSV = RESULTS / "bandgap_perovskite_pce_ood_bootstrap.csv"
SUMMARY_JSON = RESULTS / "bandgap_perovskite_pce_ood_summary.json"

EXPECTED_DESIGN_SHA256 = (
    "8d370d238e5eb2072d0625b12ca2b06d7e1d18d2c63e234f87f698d3867294e0"
)
HASH_DIMENSIONS = 256
FINITE_BUDGETS = (100, 300)
FINITE_DRAWS = 50
ALL_DRAWS = 10
BOOTSTRAP_REPLICATES = 10_000
POLICIES = (
    "experimental_text_mined",
    "calibrated_hse_with_contract",
    "support_weighted_contract_fusion",
    "retrieval_routed_contract_fusion",
)
CONTROL = "composition_permuted_borrowed_feature_control"
MODEL_SEED_BASE = 2026074000
PERMUTATION_SEED = 2026073999


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_number(value: object) -> float:
    if value is None or pd.isna(value):
        return float("nan")
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", str(value))
    if match is None:
        return float("nan")
    try:
        result = float(match.group())
    except ValueError:
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def token_parts(prefix: str, value: object) -> list[str]:
    if value is None or pd.isna(value) or not str(value).strip():
        return [f"{prefix}=<missing>"]
    text = " ".join(str(value).strip().lower().split())
    output = [f"{prefix}={text}"]
    pieces = [
        piece.strip()
        for piece in re.split(r"\s*(?:\||;|>>)\s*", text)
        if piece.strip()
    ]
    output.extend(f"{prefix}:part={piece}" for piece in pieces)
    return output


def row_tokens(row: pd.Series) -> list[str]:
    output: list[str] = []
    try:
        ions = json.loads(str(row["ions_json"]))
    except json.JSONDecodeError:
        ions = []
    if isinstance(ions, list):
        for ion in ions:
            if not isinstance(ion, dict):
                continue
            site = str(ion.get("ion_type") or "?").upper()
            name = str(ion.get("name") or "<missing>").strip()
            try:
                coefficient = float(ion.get("coefficients"))
                coefficient_text = f"{coefficient:.3f}"
            except (TypeError, ValueError):
                coefficient_text = "<missing>"
            output.append(f"site:{site}={name}")
            output.append(f"site:{site}:{name}:coefficient={coefficient_text}")
    for prefix, column in (
        ("architecture", "cell_architecture"),
        ("stack", "cell_stack_sequence"),
        ("deposition", "deposition_procedure"),
        ("solvent", "deposition_solvents"),
        ("scan", "pce_scan_direction"),
        ("light_spectrum", "light_spectra"),
    ):
        output.extend(token_parts(prefix, row.get(column)))
    return output


def state_numeric(frame: pd.DataFrame) -> np.ndarray:
    columns = (
        "cell_area_total",
        "cell_area_measured",
        "deposition_steps",
        "annealing_temperature",
        "annealing_time",
        "light_intensity",
        "test_temperature",
    )
    values = np.column_stack(
        [frame[column].map(parse_number).to_numpy(float) for column in columns]
    )
    missing = ~np.isfinite(values)
    filled = np.where(missing, -999.0, values)
    return np.hstack([filled, missing.astype(float)]).astype(np.float32)


def base_features(frame: pd.DataFrame) -> np.ndarray:
    composition = bg.composition_matrix(frame["composition_dict"]).astype(
        np.float32
    )
    hasher = FeatureHasher(
        n_features=HASH_DIMENSIONS,
        input_type="string",
        alternate_sign=True,
        dtype=np.float32,
    )
    categorical = hasher.transform(
        [row_tokens(row) for _, row in frame.iterrows()]
    ).toarray()
    numeric = state_numeric(frame)
    return np.hstack([composition, categorical, numeric]).astype(np.float32)


def family_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    family_stats = (
        frame.groupby("site_family", as_index=False)
        .agg(rows=("entry_id", "size"), dois=("doi_norm", "nunique"))
        .sort_values(["rows", "site_family"], ascending=[False, True])
        .reset_index(drop=True)
    )
    centroids: dict[str, np.ndarray] = {}
    for family, group in frame.groupby("site_family", sort=True):
        unique = group.drop_duplicates("composition_key")
        centroids[str(family)] = np.median(
            bg.composition_matrix(unique["composition_dict"]),
            axis=0,
        )
    total_rows = int(family_stats["rows"].sum())
    core: list[str] = []
    covered = 0
    for row in family_stats.itertuples(index=False):
        core.append(str(row.site_family))
        covered += int(row.rows)
        if covered >= 0.60 * total_rows:
            break
    core_matrix = np.vstack([centroids[family] for family in core])
    candidates = family_stats[
        ~family_stats["site_family"].isin(core)
        & family_stats["rows"].ge(10)
        & family_stats["dois"].ge(3)
    ].copy()
    candidates["distance_to_core"] = candidates["site_family"].map(
        lambda family: float(
            np.min(
                np.linalg.norm(
                    core_matrix - centroids[str(family)][None, :],
                    axis=1,
                )
            )
        )
    )
    candidates = candidates.sort_values(
        ["distance_to_core", "rows", "site_family"],
        ascending=[False, True, True],
    )
    selected: list[str] = []
    selected_rows = 0
    for row in candidates.itertuples(index=False):
        selected.append(str(row.site_family))
        selected_rows += int(row.rows)
        if selected_rows >= 0.20 * total_rows:
            break
    if not selected:
        raise RuntimeError("No eligible chemical-OOD family was selected")
    test = frame[frame["site_family"].isin(selected)].copy()
    test_dois = set(test["doi_norm"])
    train = frame[
        ~frame["site_family"].isin(selected)
        & ~frame["doi_norm"].isin(test_dois)
    ].copy()
    # Downstream DOI-group sampling returns positional indices for NumPy
    # feature matrices, so both partitions must use a fresh RangeIndex.
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    if set(train["site_family"]) & set(test["site_family"]):
        raise AssertionError("Chemical family leaked across OOD split")
    if set(train["doi_norm"]) & set(test["doi_norm"]):
        raise AssertionError("DOI leaked across OOD split")
    if set(train["entry_id"]) & set(test["entry_id"]):
        raise AssertionError("Entry leaked across OOD split")
    if len(train) < 1_000 or len(test) < 500:
        raise RuntimeError(
            f"Insufficient OOD split: train={len(train)}, test={len(test)}"
        )
    metadata = {
        "core_families": core,
        "selected_ood_families": selected,
        "selected_ood_family_rows": selected_rows,
        "valid_rows": total_rows,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_dois": int(train["doi_norm"].nunique()),
        "test_dois": int(test["doi_norm"].nunique()),
        "test_fraction": float(len(test) / total_rows),
        "candidate_family_table": candidates.to_dict(orient="records"),
    }
    return train, test, metadata


def sample_doi_groups(
    frame: pd.DataFrame,
    budget: int,
    seed: int,
) -> np.ndarray:
    groups = {
        doi: indices.to_numpy(int)
        for doi, indices in frame.groupby("doi_norm", sort=True).groups.items()
    }
    rng = np.random.default_rng(seed)
    order = np.asarray(sorted(groups), dtype=object)
    rng.shuffle(order)
    selected: list[int] = []
    deferred: list[str] = []
    for doi in order:
        candidate = groups[str(doi)]
        if len(selected) + len(candidate) <= budget:
            selected.extend(candidate.tolist())
        else:
            deferred.append(str(doi))
    if len(selected) < 0.8 * budget and deferred:
        best = min(
            deferred,
            key=lambda doi: abs(
                budget - len(selected) - len(groups[doi])
            ),
        )
        selected.extend(groups[best].tolist())
    if len(selected) < 30:
        raise RuntimeError(f"Only sampled {len(selected)} target rows")
    return np.asarray(sorted(selected), dtype=int)


def policy_columns() -> dict[str, list[str]]:
    return {
        "experimental_text_mined": [
            "experimental_prediction",
            "experimental_ensemble_sd",
            "experimental_distance",
        ],
        "calibrated_hse_with_contract": [
            "hse_prediction_calibrated",
            "hse_ensemble_sd",
            "hse_distance",
            "hse_contract_eligible",
        ],
        "support_weighted_contract_fusion": [
            "contract_fusion_prediction",
            "experimental_ensemble_sd",
            "experimental_distance",
            "hse_ensemble_sd",
            "hse_distance",
            "hse_contract_eligible",
        ],
        "retrieval_routed_contract_fusion": [
            "retrieval_routed_prediction",
            "experimental_ensemble_sd",
            "experimental_distance",
            "hse_ensemble_sd",
            "hse_distance",
            "hse_contract_eligible",
            "exact_lookup_available",
            "exact_lookup_sources",
            "exact_lookup_dois",
        ],
    }


def permuted_features(
    source_features: pd.DataFrame,
) -> pd.DataFrame:
    output = source_features.copy()
    borrowed = sorted(
        {
            column
            for columns in policy_columns().values()
            for column in columns
        }
    )
    rng = np.random.default_rng(PERMUTATION_SEED)
    strata = (
        output["hse_contract_eligible"].astype(str)
        + "|"
        + output["exact_lookup_available"].astype(str)
    )
    for _, indices in strata.groupby(strata).groups.items():
        indices = np.asarray(list(indices), dtype=int)
        permutation = rng.permutation(indices)
        output.loc[indices, borrowed] = output.loc[
            permutation, borrowed
        ].to_numpy()
    return output


def fit_model(seed: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=3,
        max_features=0.7,
        random_state=seed,
        n_jobs=-1,
    )


def metric_row(
    truth: np.ndarray,
    baseline: np.ndarray,
    augmented: np.ndarray,
    groups: np.ndarray | None = None,
) -> dict[str, float]:
    base_rmse = math.sqrt(mean_squared_error(truth, baseline))
    aug_rmse = math.sqrt(mean_squared_error(truth, augmented))
    base_spearman = float(spearmanr(truth, baseline).statistic)
    aug_spearman = float(spearmanr(truth, augmented).statistic)
    output = {
        "base_rmse": float(base_rmse),
        "aug_rmse": float(aug_rmse),
        "relative_rmse_gain": float((base_rmse - aug_rmse) / base_rmse),
        "mae_gain": float(
            mean_absolute_error(truth, baseline)
            - mean_absolute_error(truth, augmented)
        ),
        "base_r2": float(r2_score(truth, baseline)),
        "aug_r2": float(r2_score(truth, augmented)),
        "delta_r2": float(
            r2_score(truth, augmented) - r2_score(truth, baseline)
        ),
        "base_spearman": base_spearman,
        "aug_spearman": aug_spearman,
        "spearman_gain": aug_spearman - base_spearman,
    }
    if groups is not None:
        per_family = pd.DataFrame(
            {
                "family": groups,
                "base_sq": (truth - baseline) ** 2,
                "aug_sq": (truth - augmented) ** 2,
            }
        ).groupby("family", sort=True)[["base_sq", "aug_sq"]].mean()
        base_worst = float(np.sqrt(per_family["base_sq"]).max())
        aug_worst = float(np.sqrt(per_family["aug_sq"]).max())
        output.update(
            {
                "base_worst_family_rmse": base_worst,
                "aug_worst_family_rmse": aug_worst,
                "worst_family_rmse_gain": base_worst - aug_worst,
            }
        )
    return output


def hierarchical_bootstrap(
    test: pd.DataFrame,
    truth: np.ndarray,
    baseline: np.ndarray,
    augmented: np.ndarray,
    *,
    seed: int,
) -> np.ndarray:
    clusters: dict[str, dict[str, tuple[int, float, float]]] = defaultdict(dict)
    temporary = pd.DataFrame(
        {
            "family": test["site_family"].astype(str).to_numpy(),
            "doi": test["doi_norm"].astype(str).to_numpy(),
            "base_sq": (truth - baseline) ** 2,
            "aug_sq": (truth - augmented) ** 2,
        }
    )
    for (family, doi), group in temporary.groupby(
        ["family", "doi"], sort=True
    ):
        clusters[family][doi] = (
            int(len(group)),
            float(group["base_sq"].sum()),
            float(group["aug_sq"].sum()),
        )
    families = sorted(clusters)
    rng = np.random.default_rng(seed)
    gains = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for replicate in range(BOOTSTRAP_REPLICATES):
        sampled_families = rng.choice(
            families, size=len(families), replace=True
        )
        n = 0
        base_sum = 0.0
        aug_sum = 0.0
        for family in sampled_families:
            doi_map = clusters[str(family)]
            dois = sorted(doi_map)
            sampled_dois = rng.choice(dois, size=len(dois), replace=True)
            for doi in sampled_dois:
                count, base_sq, aug_sq = doi_map[str(doi)]
                n += count
                base_sum += base_sq
                aug_sum += aug_sq
        base_rmse = math.sqrt(base_sum / n)
        aug_rmse = math.sqrt(aug_sum / n)
        gains[replicate] = (base_rmse - aug_rmse) / base_rmse
    return gains


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=pvalues.get)
    output: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, name in enumerate(ordered):
        value = min(1.0, (total - rank) * pvalues[name])
        running = max(running, value)
        output[name] = running
    return output


def main() -> None:
    if sha256(DESIGN) != EXPECTED_DESIGN_SHA256:
        raise RuntimeError("PCE OOD design changed after its freeze")
    if not SOURCE_SUMMARY.exists() or not SOURCE_FEATURES.exists():
        raise FileNotFoundError("Verified source-skill outputs are missing")
    source_summary = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    if source_summary.get("status") != "source-skill-gate-passed":
        raise RuntimeError("No donor policy passed the source-skill gate")
    if (
        sha256(SOURCE_FEATURES)
        != source_summary.get("donor_features_sha256")
    ):
        raise RuntimeError("Donor feature hash changed after source skill")

    target = bg.load_recipient()
    target = target[
        target["entry_id"].notna()
        & target["doi_norm"].ne("")
        & target["ions_valid"]
        & target["composition_key"].ne("")
        & target["pce"].between(0.0, 40.0, inclusive="both")
    ].copy()
    target = target.sort_values("entry_id").reset_index(drop=True)
    source_features = pd.read_csv(SOURCE_FEATURES)
    target = target.merge(
        source_features,
        on="composition_key",
        how="left",
        validate="many_to_one",
    )
    required_borrowed = sorted(
        {
            column
            for columns in policy_columns().values()
            for column in columns
        }
    )
    if target[required_borrowed].isna().any().any():
        missing = target[required_borrowed].isna().sum()
        raise RuntimeError(
            f"Donor features missing after merge: "
            f"{missing[missing.gt(0)].to_dict()}"
        )

    train, test, split = family_split(target)
    split.update(
        {
            "status": "frozen-outcome-blind-split",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "design_sha256": EXPECTED_DESIGN_SHA256,
            "recipient_csv_sha256": bg.sha256(bg.RECIPIENT_CSV),
        }
    )
    SPLIT_JSON.write_text(
        json.dumps(split, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    combined = pd.concat(
        [
            train.assign(_scope="train"),
            test.assign(_scope="test"),
        ],
        ignore_index=True,
    )
    combined_x = base_features(combined)
    train_n = len(train)
    train_x = combined_x[:train_n]
    test_x = combined_x[train_n:]
    train_y = train["pce"].to_numpy(float)
    test_y = test["pce"].to_numpy(float)
    test_groups = test["site_family"].astype(str).to_numpy()

    borrowed_frame = combined[
        ["composition_key", *required_borrowed]
    ].drop_duplicates("composition_key")
    borrowed_permuted = permuted_features(
        borrowed_frame.reset_index(drop=True)
    )
    permuted_map = borrowed_permuted.set_index("composition_key")
    permuted_combined = combined["composition_key"].map(
        lambda key: key
    ).to_frame()
    permuted_combined = permuted_combined.join(
        permuted_map,
        on="composition_key",
        validate="many_to_one",
    )

    real_columns = policy_columns()
    metrics_rows: list[dict] = []
    primary_predictions: dict[str, list[np.ndarray]] = defaultdict(list)
    primary_baselines: list[np.ndarray] = []

    budgets: list[int | str] = [*FINITE_BUDGETS, "all"]
    for budget in budgets:
        draws = ALL_DRAWS if budget == "all" else FINITE_DRAWS
        for draw in range(draws):
            seed = MODEL_SEED_BASE + draw + (
                0 if budget == 100 else 1_000 if budget == 300 else 2_000
            )
            if budget == "all":
                indices = np.arange(len(train), dtype=int)
            else:
                indices = sample_doi_groups(train, int(budget), seed)
            baseline_model = fit_model(seed)
            baseline_model.fit(train_x[indices], train_y[indices])
            baseline_prediction = baseline_model.predict(test_x)
            if budget == 100:
                primary_baselines.append(baseline_prediction)

            for policy, columns in real_columns.items():
                borrowed_train = train[columns].to_numpy(np.float32)
                borrowed_test = test[columns].to_numpy(np.float32)
                model = fit_model(seed)
                model.fit(
                    np.hstack(
                        [train_x[indices], borrowed_train[indices]]
                    ),
                    train_y[indices],
                )
                prediction = model.predict(
                    np.hstack([test_x, borrowed_test])
                )
                row = {
                    "budget": str(budget),
                    "draw": draw,
                    "seed": seed,
                    "training_rows": int(len(indices)),
                    "training_dois": int(
                        train.iloc[indices]["doi_norm"].nunique()
                    ),
                    "policy": policy,
                    **metric_row(
                        test_y,
                        baseline_prediction,
                        prediction,
                        test_groups,
                    ),
                }
                metrics_rows.append(row)
                if budget == 100:
                    primary_predictions[policy].append(prediction)

            control_columns = real_columns[
                "retrieval_routed_contract_fusion"
            ]
            permuted_train = permuted_combined.iloc[:train_n][
                control_columns
            ].to_numpy(np.float32)
            permuted_test = permuted_combined.iloc[train_n:][
                control_columns
            ].to_numpy(np.float32)
            control_model = fit_model(seed)
            control_model.fit(
                np.hstack([train_x[indices], permuted_train[indices]]),
                train_y[indices],
            )
            control_prediction = control_model.predict(
                np.hstack([test_x, permuted_test])
            )
            metrics_rows.append(
                {
                    "budget": str(budget),
                    "draw": draw,
                    "seed": seed,
                    "training_rows": int(len(indices)),
                    "training_dois": int(
                        train.iloc[indices]["doi_norm"].nunique()
                    ),
                    "policy": CONTROL,
                    **metric_row(
                        test_y,
                        baseline_prediction,
                        control_prediction,
                        test_groups,
                    ),
                }
            )
            if budget == 100:
                primary_predictions[CONTROL].append(control_prediction)

    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(METRICS_CSV, index=False)
    mean_baseline = np.mean(np.vstack(primary_baselines), axis=0)
    prediction_frame = test[
        ["entry_id", "doi_norm", "site_family", "composition_key", "pce"]
    ].copy()
    prediction_frame["target_only_prediction"] = mean_baseline
    mean_predictions: dict[str, np.ndarray] = {}
    for policy in (*POLICIES, CONTROL):
        mean_prediction = np.mean(
            np.vstack(primary_predictions[policy]), axis=0
        )
        mean_predictions[policy] = mean_prediction
        prediction_frame[f"{policy}_prediction"] = mean_prediction
    prediction_frame.to_csv(PREDICTIONS_CSV, index=False)

    primary_metrics: dict[str, dict] = {}
    pvalues: dict[str, float] = {}
    bootstrap_frames: list[pd.DataFrame] = []
    for policy in POLICIES:
        gains = hierarchical_bootstrap(
            test,
            test_y,
            mean_baseline,
            mean_predictions[policy],
            seed=2026075000 + POLICIES.index(policy),
        )
        draw_rows = metrics[
            metrics["budget"].eq("100")
            & metrics["policy"].eq(policy)
        ]
        aggregate_metrics = metric_row(
            test_y,
            mean_baseline,
            mean_predictions[policy],
            test_groups,
        )
        bootstrap_frames.append(
            pd.DataFrame(
                {
                    "policy": policy,
                    "replicate": np.arange(len(gains), dtype=int),
                    "relative_rmse_gain": gains,
                }
            )
        )
        pvalue = float((1 + np.sum(gains <= 0)) / (len(gains) + 1))
        pvalues[policy] = pvalue
        primary_metrics[policy] = {
            **aggregate_metrics,
            "bootstrap_ci95": [
                float(np.quantile(gains, 0.025)),
                float(np.quantile(gains, 0.975)),
            ],
            "bootstrap_one_sided_p": pvalue,
            "positive_draw_fraction": float(
                draw_rows["relative_rmse_gain"].gt(0).mean()
            ),
            "median_draw_gain": float(
                draw_rows["relative_rmse_gain"].median()
            ),
        }
    bootstrap = pd.concat(bootstrap_frames, ignore_index=True)
    bootstrap.to_csv(BOOTSTRAP_CSV, index=False)
    adjusted = holm_adjust(pvalues)
    control_gain = metric_row(
        test_y,
        mean_baseline,
        mean_predictions[CONTROL],
        test_groups,
    )["relative_rmse_gain"]
    candidate_source_map = {
        "experimental_text_mined": "experimental_text_mined",
        "calibrated_hse_with_contract": "calibrated_hse",
        "support_weighted_contract_fusion": "support_weighted_fusion",
        "retrieval_routed_contract_fusion": "retrieval_routed_fusion",
    }
    decisions = {}
    for policy in POLICIES:
        item = primary_metrics[policy]
        item["holm_adjusted_p"] = adjusted[policy]
        source_pass = bool(
            source_summary["candidate_pass"].get(
                candidate_source_map[policy], False
            )
        )
        gates = {
            "source_skill_pass": source_pass,
            "relative_rmse_gain_at_least_0_05": (
                item["relative_rmse_gain"] >= 0.05
            ),
            "positive_bootstrap_interval": (
                item["bootstrap_ci95"][0] > 0
            ),
            "holm_p_at_most_0_05": adjusted[policy] <= 0.05,
            "gain_over_permuted_control": (
                item["relative_rmse_gain"] > control_gain
            ),
            "positive_draw_fraction_at_least_0_70": (
                item["positive_draw_fraction"] >= 0.70
            ),
            "positive_augmented_r2": item["aug_r2"] > 0,
        }
        decisions[policy] = {
            "passes": all(gates.values()),
            "gates": gates,
        }

    summary = {
        "status": "verified-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": EXPECTED_DESIGN_SHA256,
        "recipient_csv_sha256": bg.sha256(bg.RECIPIENT_CSV),
        "source_summary_sha256": sha256(SOURCE_SUMMARY),
        "source_features_sha256": sha256(SOURCE_FEATURES),
        "split_sha256": sha256(SPLIT_JSON),
        "metrics_sha256": sha256(METRICS_CSV),
        "predictions_sha256": sha256(PREDICTIONS_CSV),
        "bootstrap_sha256": sha256(BOOTSTRAP_CSV),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_families": int(test["site_family"].nunique()),
        "test_dois": int(test["doi_norm"].nunique()),
        "primary_budget": 100,
        "primary_metrics": primary_metrics,
        "permuted_control_relative_rmse_gain": control_gain,
        "decisions": decisions,
        "passing_policies": [
            policy for policy, item in decisions.items() if item["passes"]
        ],
        "claim_guard": (
            "A passing policy establishes retrospective chemical-OOD "
            "prediction improvement for this recipient programme only. It "
            "does not establish prospective laboratory discovery or universal "
            "cross-domain transfer."
        ),
    }
    temporary = SUMMARY_JSON.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(SUMMARY_JSON)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
