"""External validation of the experimental band-gap donor.

The source model never sees a recipient DOI or an exact recipient
composition.  Recipient band gaps are used only here as an external validation
endpoint; photovoltaic outcomes are not read by this script.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neighbors import NearestNeighbors

import bandgap_borrowing_common as bg


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
AUDIT_JSON = RESULTS / "bandgap_perovskite_pair_audit.json"
SUMMARY_JSON = RESULTS / "bandgap_external_source_skill_summary.json"
PREDICTIONS_CSV = RESULTS / "bandgap_external_source_predictions.csv"
SHUFFLED_CSV = RESULTS / "bandgap_external_source_shuffled_controls.csv"
FEATURES_CSV = RESULTS / "bandgap_external_donor_features.csv"

MODEL_SEEDS = [2026072801, 2026072802, 2026072803, 2026072804, 2026072805]
SHUFFLE_SEEDS = list(range(2026072901, 2026073000))
N_ESTIMATORS = 300
CANDIDATES = (
    "experimental_text_mined",
    "calibrated_hse",
    "support_weighted_fusion",
    "retrieval_routed_fusion",
)


def directly_measured_basis(value: object) -> bool:
    text = str(value or "").strip().lower()
    if not text or text in {"composition", "literature", "unknown", "nan"}:
        return False
    return any(
        token in text
        for token in (
            "absorp",
            "tauc",
            "eqe",
            "ipce",
            "ups",
            "uv",
            "photolum",
            "pl",
        )
    )


def aggregate_validation(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(
            ["composition_key", "site_family", "element_system"],
            as_index=False,
        )
        .agg(
            band_gap=("band_gap", "median"),
            band_gap_rows=("band_gap", "size"),
            band_gap_basis=(
                "band_gap_estimation_basis",
                lambda values: "|".join(
                    sorted(
                        {
                            str(value)
                            for value in values.dropna()
                            if str(value).strip()
                        }
                    )
                ),
            ),
            composition_dict=("composition_dict", "first"),
            n_dois=("doi_norm", "nunique"),
        )
        .sort_values("composition_key")
        .reset_index(drop=True)
    )


def fit_model(seed: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=N_ESTIMATORS,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=-1,
    )


def metric_row(
    truth: np.ndarray,
    prediction: np.ndarray,
    baseline: np.ndarray,
) -> dict[str, float | int]:
    rmse = math.sqrt(mean_squared_error(truth, prediction))
    baseline_rmse = math.sqrt(mean_squared_error(truth, baseline))
    spearman = stats.spearmanr(truth, prediction, nan_policy="omit")
    return {
        "n": int(len(truth)),
        "rmse": float(rmse),
        "mae": float(mean_absolute_error(truth, prediction)),
        "r2": float(r2_score(truth, prediction)),
        "spearman_r": float(spearman.statistic),
        "spearman_p": float(spearman.pvalue),
        "donor_median_baseline_rmse": float(baseline_rmse),
        "relative_rmse_gain_over_donor_median": float(
            (baseline_rmse - rmse) / baseline_rmse
        ),
    }


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=pvalues.get)
    output: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, name in enumerate(ordered):
        adjusted = min(1.0, (total - rank) * pvalues[name])
        running = max(running, adjusted)
        output[name] = running
    return output


def compositions_from_keys(values: pd.Series) -> pd.Series:
    return values.map(
        lambda key: {
            token.split(":", 1)[0]: float(token.split(":", 1)[1])
            for token in str(key).split("|")
            if token
        }
    )


def support_scale(matrix: np.ndarray) -> float:
    if len(matrix) < 3:
        return 1.0
    neighbors = NearestNeighbors(n_neighbors=2, metric="euclidean")
    neighbors.fit(matrix)
    distances, _ = neighbors.kneighbors(matrix)
    scale = float(np.median(distances[:, 1]))
    return max(scale, 1e-6)


def support_threshold(matrix: np.ndarray, quantile: float = 0.95) -> float:
    if len(matrix) < 3:
        return float("inf")
    neighbors = NearestNeighbors(n_neighbors=2, metric="euclidean")
    neighbors.fit(matrix)
    distances, _ = neighbors.kneighbors(matrix)
    return float(np.quantile(distances[:, 1], quantile))


def main() -> None:
    if not AUDIT_JSON.exists():
        raise FileNotFoundError(
            "Run analysis/audit_bandgap_perovskite_pair.py first"
        )
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    if audit.get("status") != "eligible-for-source-skill-benchmark":
        raise RuntimeError("Pair audit did not permit a source-skill benchmark")

    target = bg.load_recipient(
        columns={
            "doi",
            "ions_json",
            "composition_long_form",
            "band_gap",
            "band_gap_estimation_basis",
        }
    )
    source_raw = bg.load_donor_raw()
    source, _ = bg.recover_donor_compositions(source_raw, target)
    strict_records = bg.robust_donor_records(
        source,
        target=target,
        exclude_target_dois=True,
        exclude_target_compositions=True,
    )
    cards_all = bg.aggregate_donor(strict_records)
    cards = cards_all[
        cards_all["n_dois"].ge(2) & cards_all["band_gap_iqr"].le(1.0)
    ].copy()
    if len(cards) < 500:
        raise RuntimeError(
            f"Only {len(cards)} replicated source cards remain"
        )
    lookup_records = bg.robust_donor_records(
        source,
        target=target,
        exclude_target_dois=True,
        exclude_target_compositions=False,
    )
    experimental_lookup = bg.aggregate_donor(lookup_records)
    experimental_lookup = experimental_lookup[
        experimental_lookup["n_dois"].ge(2)
        & experimental_lookup["band_gap_iqr"].le(1.0)
    ].copy()
    hybrid3_lookup = bg.load_hybrid3_cards(
        target=target,
        exclude_target_dois=True,
    )
    lookup_parts = [
        experimental_lookup[
            ["composition_key", "band_gap", "n_dois"]
        ].assign(source="experimental_text_mined"),
        hybrid3_lookup[
            ["composition_key", "band_gap", "n_dois"]
        ].assign(source="hybrid3_curated"),
    ]
    lookup_evidence = pd.concat(lookup_parts, ignore_index=True)
    lookup_evidence["weight"] = np.sqrt(
        lookup_evidence["n_dois"].clip(lower=1).to_numpy(float)
    )
    lookup_cards = pd.DataFrame(
        [
            {
                "composition_key": composition,
                "band_gap": float(
                    np.average(
                        group["band_gap"].to_numpy(float),
                        weights=group["weight"].to_numpy(float),
                    )
                ),
                "n_sources": int(group["source"].nunique()),
                "total_dois": int(group["n_dois"].sum()),
            }
            for composition, group in lookup_evidence.groupby(
                "composition_key", sort=True
            )
        ]
    )
    target_compositions = set(target["composition_key"]) - {""}
    hse_cards_all = bg.load_hse_cards()
    hse_cards = hse_cards_all[
        ~hse_cards_all["composition_key"].isin(target_compositions)
        & hse_cards_all["band_gap_hse_iqr"].le(1.0)
    ].copy()
    if len(hse_cards) < 5_000:
        raise RuntimeError(f"Only {len(hse_cards)} HSE source cards remain")

    calibration = cards.merge(
        hse_cards[["composition_key", "band_gap_hse"]],
        on="composition_key",
        how="inner",
        validate="one_to_one",
    )
    if len(calibration) < 200:
        raise RuntimeError(
            f"Only {len(calibration)} experimental-HSE calibration overlaps"
        )
    calibrator = HuberRegressor(
        epsilon=1.35,
        alpha=0.01,
        max_iter=1_000,
    )
    calibrator.fit(
        calibration[["band_gap_hse"]].to_numpy(float),
        calibration["band_gap"].to_numpy(float),
    )

    validation_raw = target[
        target["doi_norm"].ne("")
        & target["ions_valid"]
        & target["composition_key"].ne("")
        & target["band_gap"].between(0.2, 4.0, inclusive="both")
    ].copy()
    validation_raw["direct_measurement"] = validation_raw[
        "band_gap_estimation_basis"
    ].map(directly_measured_basis)
    validation_rows_all = aggregate_validation(validation_raw)
    validation_rows = aggregate_validation(
        validation_raw[validation_raw["direct_measurement"]]
    )
    experimental_systems = set(cards["element_system"])
    hse_systems = set(hse_cards["element_system"])
    source_systems = experimental_systems | hse_systems
    validation_rows_all["source_element_system_supported"] = (
        validation_rows_all["element_system"].isin(source_systems)
    )
    validation_rows["source_element_system_supported"] = (
        validation_rows["element_system"].isin(source_systems)
    )
    primary = validation_rows.copy()
    if len(primary) < 100:
        raise RuntimeError(
            f"Only {len(primary)} direct validation compositions"
        )

    # Cards store deterministic composition keys; reconstruction never
    # consults recipient band gaps or photovoltaic outcomes.
    experimental_x = bg.composition_matrix(
        compositions_from_keys(cards["composition_key"])
    )
    experimental_y = cards["band_gap"].to_numpy(float)
    hse_x = bg.composition_matrix(hse_cards["composition_dict"])
    hse_y = hse_cards["band_gap_hse"].to_numpy(float)
    target_x = bg.composition_matrix(primary["composition_dict"])
    target_y = primary["band_gap"].to_numpy(float)
    donor_median = float(np.median(experimental_y))
    baseline = np.full_like(target_y, donor_median)

    experimental_neighbor = NearestNeighbors(
        n_neighbors=1, metric="euclidean"
    ).fit(experimental_x)
    experimental_distances, _ = experimental_neighbor.kneighbors(target_x)
    hse_neighbor = NearestNeighbors(
        n_neighbors=1, metric="euclidean"
    ).fit(hse_x)
    hse_distances, _ = hse_neighbor.kneighbors(target_x)
    primary["experimental_source_distance"] = experimental_distances[:, 0]
    primary["hse_source_distance"] = hse_distances[:, 0]
    experimental_scale = support_scale(experimental_x)
    hse_scale = support_scale(hse_x)
    hse_threshold = support_threshold(hse_x)

    experimental_models = []
    hse_models = []
    experimental_predictions = []
    hse_predictions = []
    for seed in MODEL_SEEDS:
        experimental_model = fit_model(seed)
        experimental_model.fit(experimental_x, experimental_y)
        experimental_models.append(experimental_model)
        experimental_predictions.append(
            experimental_model.predict(target_x)
        )
        hse_model = fit_model(seed)
        hse_model.fit(hse_x, hse_y)
        hse_models.append(hse_model)
        raw_hse = hse_model.predict(target_x)
        hse_predictions.append(
            calibrator.predict(raw_hse.reshape(-1, 1))
        )
    experimental_matrix = np.vstack(experimental_predictions)
    hse_matrix = np.vstack(hse_predictions)
    experimental_mean = np.mean(experimental_matrix, axis=0)
    hse_mean = np.mean(hse_matrix, axis=0)
    experimental_weight = np.exp(
        -experimental_distances[:, 0] / experimental_scale
    )
    organic_hybrid = primary["composition_dict"].map(
        lambda item: bool({"C", "H", "N"}.intersection(item))
    ).to_numpy()
    hse_eligible = (
        ~organic_hybrid
        & (hse_distances[:, 0] <= hse_threshold)
    )
    hse_weight = (
        np.exp(-hse_distances[:, 0] / hse_scale)
        * hse_eligible.astype(float)
    )
    fusion_mean = (
        experimental_weight * experimental_mean + hse_weight * hse_mean
    ) / np.maximum(experimental_weight + hse_weight, 1e-12)
    lookup_map = dict(
        zip(
            lookup_cards["composition_key"].astype(str),
            lookup_cards["band_gap"].to_numpy(float),
            strict=True,
        )
    )
    lookup_value = primary["composition_key"].map(lookup_map)
    has_lookup = lookup_value.notna().to_numpy()
    retrieval_routed = fusion_mean.copy()
    retrieval_routed[has_lookup] = lookup_value.loc[has_lookup].to_numpy(
        float
    )
    candidate_predictions = {
        "experimental_text_mined": experimental_mean,
        "calibrated_hse": hse_mean,
        "support_weighted_fusion": fusion_mean,
        "retrieval_routed_fusion": retrieval_routed,
    }
    primary["experimental_bandgap_prediction"] = experimental_mean
    primary["experimental_bandgap_ensemble_sd"] = np.std(
        experimental_matrix, axis=0, ddof=1
    )
    primary["hse_bandgap_prediction_calibrated"] = hse_mean
    primary["hse_bandgap_ensemble_sd"] = np.std(
        hse_matrix, axis=0, ddof=1
    )
    primary["support_weighted_fusion_prediction"] = fusion_mean
    primary["retrieval_routed_fusion_prediction"] = retrieval_routed
    primary["independent_exact_lookup_available"] = has_lookup
    primary["experimental_support_weight"] = experimental_weight
    primary["hse_support_weight"] = hse_weight
    primary["hse_contract_eligible"] = hse_eligible

    all_compositions = (
        target[
            target["ions_valid"] & target["composition_key"].ne("")
        ][["composition_key", "composition_dict", "element_system"]]
        .drop_duplicates("composition_key")
        .sort_values("composition_key")
        .reset_index(drop=True)
    )
    all_x = bg.composition_matrix(all_compositions["composition_dict"])
    all_experimental_matrix = np.vstack(
        [model.predict(all_x) for model in experimental_models]
    )
    all_hse_matrix = np.vstack(
        [
            calibrator.predict(model.predict(all_x).reshape(-1, 1))
            for model in hse_models
        ]
    )
    all_experimental_mean = np.mean(all_experimental_matrix, axis=0)
    all_hse_mean = np.mean(all_hse_matrix, axis=0)
    all_experimental_distance, _ = experimental_neighbor.kneighbors(all_x)
    all_hse_distance, _ = hse_neighbor.kneighbors(all_x)
    all_experimental_weight = np.exp(
        -all_experimental_distance[:, 0] / experimental_scale
    )
    all_organic_hybrid = all_compositions["composition_dict"].map(
        lambda item: bool({"C", "H", "N"}.intersection(item))
    ).to_numpy()
    all_hse_eligible = (
        ~all_organic_hybrid
        & (all_hse_distance[:, 0] <= hse_threshold)
    )
    all_hse_weight = (
        np.exp(-all_hse_distance[:, 0] / hse_scale)
        * all_hse_eligible.astype(float)
    )
    all_fusion = (
        all_experimental_weight * all_experimental_mean
        + all_hse_weight * all_hse_mean
    ) / np.maximum(all_experimental_weight + all_hse_weight, 1e-12)
    all_lookup = all_compositions["composition_key"].map(lookup_map)
    all_has_lookup = all_lookup.notna().to_numpy()
    all_retrieval = all_fusion.copy()
    all_retrieval[all_has_lookup] = all_lookup.loc[
        all_has_lookup
    ].to_numpy(float)
    lookup_source_map = dict(
        zip(
            lookup_cards["composition_key"].astype(str),
            lookup_cards["n_sources"].to_numpy(int),
            strict=True,
        )
    )
    lookup_doi_map = dict(
        zip(
            lookup_cards["composition_key"].astype(str),
            lookup_cards["total_dois"].to_numpy(int),
            strict=True,
        )
    )
    features = pd.DataFrame(
        {
            "composition_key": all_compositions["composition_key"],
            "experimental_prediction": all_experimental_mean,
            "experimental_ensemble_sd": np.std(
                all_experimental_matrix, axis=0, ddof=1
            ),
            "experimental_distance": all_experimental_distance[:, 0],
            "hse_prediction_calibrated": all_hse_mean,
            "hse_ensemble_sd": np.std(
                all_hse_matrix, axis=0, ddof=1
            ),
            "hse_distance": all_hse_distance[:, 0],
            "hse_contract_eligible": all_hse_eligible,
            "contract_fusion_prediction": all_fusion,
            "retrieval_routed_prediction": all_retrieval,
            "exact_lookup_available": all_has_lookup,
            "exact_lookup_sources": all_compositions[
                "composition_key"
            ]
            .map(lookup_source_map)
            .fillna(0)
            .astype(int),
            "exact_lookup_dois": all_compositions[
                "composition_key"
            ]
            .map(lookup_doi_map)
            .fillna(0)
            .astype(int),
        }
    )
    features.to_csv(FEATURES_CSV, index=False)

    shuffled_rows = []
    for seed in SHUFFLE_SEEDS:
        rng = np.random.default_rng(seed)
        experimental_model = fit_model(seed)
        experimental_model.fit(
            experimental_x, rng.permutation(experimental_y)
        )
        shuffled_experimental = experimental_model.predict(target_x)
        hse_model = fit_model(seed + 10_000)
        hse_model.fit(hse_x, rng.permutation(hse_y))
        shuffled_hse_raw = hse_model.predict(target_x)
        shuffled_hse = calibrator.predict(
            shuffled_hse_raw.reshape(-1, 1)
        )
        shuffled_fusion = (
            experimental_weight * shuffled_experimental
            + hse_weight * shuffled_hse
        ) / np.maximum(experimental_weight + hse_weight, 1e-12)
        shuffled_lookup_map = dict(
            zip(
                lookup_cards["composition_key"].astype(str),
                rng.permutation(
                    lookup_cards["band_gap"].to_numpy(float)
                ),
                strict=True,
            )
        )
        shuffled_lookup_value = primary["composition_key"].map(
            shuffled_lookup_map
        )
        shuffled_retrieval = shuffled_fusion.copy()
        shuffled_retrieval[has_lookup] = shuffled_lookup_value.loc[
            has_lookup
        ].to_numpy(float)
        for candidate, prediction in {
            "experimental_text_mined": shuffled_experimental,
            "calibrated_hse": shuffled_hse,
            "support_weighted_fusion": shuffled_fusion,
            "retrieval_routed_fusion": shuffled_retrieval,
        }.items():
            metrics = metric_row(target_y, prediction, baseline)
            shuffled_rows.append(
                {"seed": seed, "candidate": candidate, **metrics}
            )
    shuffled = pd.DataFrame(shuffled_rows)

    real_metrics = {
        candidate: metric_row(target_y, prediction, baseline)
        for candidate, prediction in candidate_predictions.items()
    }
    secondary_all = validation_rows_all.copy()
    secondary_x = bg.composition_matrix(secondary_all["composition_dict"])
    secondary_experimental = np.mean(
        np.vstack(
            [model.predict(secondary_x) for model in experimental_models]
        ),
        axis=0,
    )
    secondary_hse = np.mean(
        np.vstack(
            [
                calibrator.predict(
                    model.predict(secondary_x).reshape(-1, 1)
                )
                for model in hse_models
            ]
        ),
        axis=0,
    )
    secondary_experimental_distance, _ = (
        experimental_neighbor.kneighbors(secondary_x)
    )
    secondary_hse_distance, _ = hse_neighbor.kneighbors(secondary_x)
    secondary_experimental_weight = np.exp(
        -secondary_experimental_distance[:, 0] / experimental_scale
    )
    secondary_hse_weight = np.exp(
        -secondary_hse_distance[:, 0] / hse_scale
    )
    secondary_organic_hybrid = secondary_all["composition_dict"].map(
        lambda item: bool({"C", "H", "N"}.intersection(item))
    ).to_numpy()
    secondary_hse_eligible = (
        ~secondary_organic_hybrid
        & (secondary_hse_distance[:, 0] <= hse_threshold)
    )
    secondary_hse_weight *= secondary_hse_eligible.astype(float)
    secondary_fusion = (
        secondary_experimental_weight * secondary_experimental
        + secondary_hse_weight * secondary_hse
    ) / np.maximum(
        secondary_experimental_weight + secondary_hse_weight, 1e-12
    )
    secondary_lookup_value = secondary_all["composition_key"].map(
        lookup_map
    )
    secondary_has_lookup = secondary_lookup_value.notna().to_numpy()
    secondary_retrieval = secondary_fusion.copy()
    secondary_retrieval[secondary_has_lookup] = (
        secondary_lookup_value.loc[secondary_has_lookup].to_numpy(float)
    )
    secondary_truth = secondary_all["band_gap"].to_numpy(float)
    secondary_baseline = np.full_like(
        secondary_truth, donor_median
    )
    secondary_metrics = {
        candidate: metric_row(
            secondary_truth,
            prediction,
            secondary_baseline,
        )
        for candidate, prediction in {
            "experimental_text_mined": secondary_experimental,
            "calibrated_hse": secondary_hse,
            "support_weighted_fusion": secondary_fusion,
            "retrieval_routed_fusion": secondary_retrieval,
        }.items()
    }
    empirical_p = {}
    for candidate in CANDIDATES:
        candidate_shuffled = shuffled[
            shuffled["candidate"].eq(candidate)
        ]
        empirical_p[candidate] = float(
            (
                1
                + np.sum(
                    candidate_shuffled["rmse"].to_numpy(float)
                    <= float(real_metrics[candidate]["rmse"])
                )
            )
            / (len(candidate_shuffled) + 1)
        )
    adjusted_p = holm_adjust(empirical_p)
    gates = {}
    for candidate in CANDIDATES:
        metrics = real_metrics[candidate]
        gates[candidate] = {
            "validation_compositions_at_least_100": len(primary) >= 100,
            "positive_absolute_r2": float(metrics["r2"]) > 0.0,
            "spearman_at_least_0_20": (
                float(metrics["spearman_r"]) >= 0.20
            ),
            "relative_rmse_gain_at_least_5_percent": (
                float(metrics["relative_rmse_gain_over_donor_median"])
                >= 0.05
            ),
            "holm_adjusted_shuffled_p_at_most_0_05": (
                adjusted_p[candidate] <= 0.05
            ),
        }
    candidate_pass = {
        candidate: all(gates[candidate].values())
        for candidate in CANDIDATES
    }
    pass_gate = any(candidate_pass.values())

    basis_counts = (
        validation_raw["band_gap_estimation_basis"]
        .replace("", "Unspecified")
        .fillna("Unspecified")
        .value_counts()
        .to_dict()
    )
    primary.to_csv(PREDICTIONS_CSV, index=False)
    shuffled.to_csv(SHUFFLED_CSV, index=False)
    summary = {
        "status": "source-skill-gate-passed"
        if pass_gate
        else "source-skill-gate-failed",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "experimental": {
                "cards_all": int(len(cards_all)),
                "cards_primary_replicated": int(len(cards)),
            },
            "hse": {
                "zip_sha256": bg.sha256(bg.HSE_ZIP),
                "raw_structures": int(
                    hse_cards_all.attrs["raw_structures"]
                ),
                "cards_all": int(len(hse_cards_all)),
                "cards_after_exact_recipient_exclusion": int(
                    len(hse_cards)
                ),
            },
            "experimental_hse_calibration_overlap": int(len(calibration)),
            "hse_calibration": {
                "intercept": float(calibrator.intercept_),
                "slope": float(calibrator.coef_[0]),
            },
            "retrieval_route": {
                "experimental_cards": int(len(experimental_lookup)),
                "hybrid3_cards": int(len(hybrid3_lookup)),
                "combined_cards": int(len(lookup_cards)),
                "primary_validation_compositions_with_lookup": int(
                    has_lookup.sum()
                ),
            },
        },
        "recipient_reported_validation_compositions_all": int(
            len(validation_rows_all)
        ),
        "recipient_direct_validation_compositions_all": int(
            len(validation_rows)
        ),
        "recipient_direct_validation_compositions": int(len(primary)),
        "recipient_direct_validation_compositions_with_seen_element_system": int(
            primary["source_element_system_supported"].sum()
        ),
        "recipient_direct_validation_compositions_hse_contract_eligible": int(
            hse_eligible.sum()
        ),
        "recipient_band_gap_basis_counts": {
            str(key): int(value)
            for key, value in basis_counts.items()
        },
        "exact_recipient_compositions_excluded_from_source": True,
        "all_recipient_dois_excluded_from_source": True,
        "donor_median_baseline_eV": donor_median,
        "donor_feature_rows": int(len(features)),
        "donor_features_sha256": bg.sha256(FEATURES_CSV),
        "predictions_sha256": bg.sha256(PREDICTIONS_CSV),
        "shuffled_controls_sha256": bg.sha256(SHUFFLED_CSV),
        "real": real_metrics,
        "secondary_all_reported_bandgaps": secondary_metrics,
        "shuffled_controls": {
            candidate: {
                "n": int(
                    shuffled["candidate"].eq(candidate).sum()
                ),
                "rmse_median": float(
                    shuffled.loc[
                        shuffled["candidate"].eq(candidate), "rmse"
                    ].median()
                ),
                "rmse_q05": float(
                    shuffled.loc[
                        shuffled["candidate"].eq(candidate), "rmse"
                    ].quantile(0.05)
                ),
                "empirical_one_sided_p": empirical_p[candidate],
                "holm_adjusted_p": adjusted_p[candidate],
            }
            for candidate in CANDIDATES
        },
        "gates": gates,
        "candidate_pass": candidate_pass,
        "next_action": (
            "Freeze and run the photovoltaic OOD borrowing benchmark."
            if pass_gate
            else (
                "Do not use this donor in the photovoltaic outcome model; "
                "replace it with a stronger source representation or source."
            )
        ),
        "claim_guard": (
            "This validates only donor skill for recipient-reported band gap. "
            "It is not evidence that donor knowledge improves photovoltaic "
            "OOD prediction."
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
