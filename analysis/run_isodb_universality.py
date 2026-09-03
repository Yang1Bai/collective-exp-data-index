"""Test whether the strong pooled ISODB compensation line has universal coefficients.

This is a post-outcome diagnostic triggered because the designated Krug gate
did not classify the pooled relation as an estimation artifact.  Inference is
clustered at DOI and the analysis is explicitly distinct from the frozen
primary artifact test.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from common import RESULTS, ensure_output_dirs, holm_adjust

SEED = 20260714
N_WILD = 4999
MIN_FAMILY_N = 8


def ols_sse(x: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, int]:
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    fitted = x @ beta
    residual = y - fitted
    rank = int(np.linalg.matrix_rank(x))
    return float(residual @ residual), fitted, residual, rank


def nested_f(x_reduced: np.ndarray, x_full: np.ndarray, y: np.ndarray) -> tuple[float, int, int]:
    sse_reduced, _, _, rank_reduced = ols_sse(x_reduced, y)
    sse_full, _, _, rank_full = ols_sse(x_full, y)
    numerator_df = rank_full - rank_reduced
    denominator_df = len(y) - rank_full
    statistic = ((sse_reduced - sse_full) / numerator_df) / (sse_full / denominator_df)
    return float(statistic), numerator_df, denominator_df


def wild_cluster_p(
    x_reduced: np.ndarray,
    x_full: np.ndarray,
    y: np.ndarray,
    clusters: np.ndarray,
    observed: float,
    seed: int,
) -> tuple[float, pd.DataFrame]:
    _, fitted, residual, _ = ols_sse(x_reduced, y)
    unique = np.unique(clusters)
    index = {cluster: position for position, cluster in enumerate(unique)}
    codes = np.asarray([index[value] for value in clusters], dtype=int)
    rng = np.random.default_rng(seed)
    rows = []
    for iteration in range(N_WILD):
        signs = rng.choice([-1.0, 1.0], size=len(unique))
        synthetic = fitted + residual * signs[codes]
        statistic, _, _ = nested_f(x_reduced, x_full, synthetic)
        rows.append({"bootstrap": iteration, "f_statistic": statistic})
    null = pd.DataFrame(rows)
    pvalue = (1 + int((null["f_statistic"] >= observed).sum())) / (len(null) + 1)
    return pvalue, null


def main() -> None:
    ensure_output_dirs()
    primary = pd.read_csv(RESULTS / "isodb_isosteric_primary_fits.csv")
    counts = primary["adsorbate_name"].value_counts()
    major_names = sorted(counts[counts >= MIN_FAMILY_N].index)
    frame = primary[primary["adsorbate_name"].isin(major_names)].copy().reset_index(drop=True)
    family = pd.Categorical(frame["adsorbate_name"], categories=major_names)
    dummies = np.eye(len(major_names))[family.codes]
    q = frame["Qst_kJ_mol"].to_numpy(float)
    y = frame["vanthoff_intercept"].to_numpy(float)
    clusters = frame["doi"].astype(str).to_numpy()

    pooled = np.column_stack([np.ones(len(frame)), q])
    family_intercepts = np.column_stack([dummies, q])
    family_slopes = np.column_stack([dummies, dummies * q[:, None]])

    f_intercepts, df_i_num, df_i_den = nested_f(pooled, family_intercepts, y)
    f_slopes, df_s_num, df_s_den = nested_f(family_intercepts, family_slopes, y)
    p_intercepts_wild, null_intercepts = wild_cluster_p(
        pooled, family_intercepts, y, clusters, f_intercepts, SEED
    )
    p_slopes_wild, null_slopes = wild_cluster_p(
        family_intercepts, family_slopes, y, clusters, f_slopes, SEED + 1
    )
    null_intercepts["test"] = "common_intercept_vs_family_intercepts"
    null_slopes["test"] = "common_slope_vs_family_slopes"
    pd.concat([null_intercepts, null_slopes], ignore_index=True).to_csv(
        RESULTS / "isodb_universality_wild_cluster_null.csv", index=False
    )

    frame["q_centered"] = q - frame.groupby("adsorbate_name")["Qst_kJ_mol"].transform("mean")
    frame["c_centered"] = y - frame.groupby("adsorbate_name")["vanthoff_intercept"].transform("mean")
    within_slope = float(
        np.sum(frame["q_centered"] * frame["c_centered"])
        / np.sum(frame["q_centered"] ** 2)
    )
    within_prediction = within_slope * frame["q_centered"]
    within_r2 = float(
        1 - np.sum((frame["c_centered"] - within_prediction) ** 2)
        / np.sum(frame["c_centered"] ** 2)
    )
    means = frame.groupby("adsorbate_name", as_index=False).agg(
        Qst_kJ_mol=("Qst_kJ_mol", "mean"),
        vanthoff_intercept=("vanthoff_intercept", "mean"),
        n_systems=("system_id", "size"),
    )
    between_slope, between_intercept = np.polyfit(
        means["Qst_kJ_mol"], means["vanthoff_intercept"], 1
    )
    between_prediction = between_intercept + between_slope * means["Qst_kJ_mol"]
    between_r2 = float(
        1 - np.sum((means["vanthoff_intercept"] - between_prediction) ** 2)
        / np.sum((means["vanthoff_intercept"] - means["vanthoff_intercept"].mean()) ** 2)
    )

    # Leave-one-adsorbate-out prediction uses no observations from the held-out
    # chemical family.  This assesses portability, not coefficient equality.
    prediction_rows = []
    for held_out in major_names:
        train = frame[frame["adsorbate_name"] != held_out]
        test = frame[frame["adsorbate_name"] == held_out]
        slope, intercept = np.polyfit(train["Qst_kJ_mol"], train["vanthoff_intercept"], 1)
        prediction = intercept + slope * test["Qst_kJ_mol"].to_numpy(float)
        for index, (_, row) in enumerate(test.iterrows()):
            prediction_rows.append({
                "held_out_adsorbate": held_out,
                "doi": row["doi"],
                "Qst_kJ_mol": row["Qst_kJ_mol"],
                "observed_intercept": row["vanthoff_intercept"],
                "predicted_intercept": prediction[index],
                "training_slope": slope,
            })
    predictions = pd.DataFrame(prediction_rows)
    predictions.to_csv(RESULTS / "isodb_leave_adsorbate_out_predictions.csv", index=False)
    family_prediction = []
    for name, group in predictions.groupby("held_out_adsorbate"):
        denominator = np.sum((group["observed_intercept"] - group["observed_intercept"].mean()) ** 2)
        sse = np.sum((group["observed_intercept"] - group["predicted_intercept"]) ** 2)
        family_prediction.append({
            "adsorbate_name": name,
            "n_systems": len(group),
            "rmse": float(np.sqrt(sse / len(group))),
            "r2_within_heldout_family": float(1 - sse / denominator) if denominator > 0 else np.nan,
            "mean_error": float((group["predicted_intercept"] - group["observed_intercept"]).mean()),
        })
    family_prediction = pd.DataFrame(family_prediction)
    family_prediction.to_csv(RESULTS / "isodb_leave_adsorbate_out_summary.csv", index=False)

    families = pd.read_csv(RESULTS / "isodb_compensation_families.csv")
    pooled_result = json.loads(
        (RESULTS / "isodb_compensation_summary.json").read_text(encoding="utf-8")
    )["primary"]
    pooled_slope = pooled_result["slope"]
    pooled_se = pooled_result["slope_se_hc3"]
    families["z_difference_from_pooled"] = (
        (families["slope"] - pooled_slope)
        / np.sqrt(families["slope_se_hc3"] ** 2 + pooled_se**2)
    )
    families["p_difference_from_pooled"] = 2 * stats.norm.sf(
        np.abs(families["z_difference_from_pooled"])
    )
    families["p_difference_from_pooled_holm"] = holm_adjust(
        families["p_difference_from_pooled"]
    )
    families.to_csv(RESULTS / "isodb_compensation_families_universality.csv", index=False)

    total_sse = np.sum(
        (predictions["observed_intercept"] - predictions["predicted_intercept"]) ** 2
    )
    total_denominator = np.sum(
        (predictions["observed_intercept"] - predictions["observed_intercept"].mean()) ** 2
    )
    summary = {
        "analysis_status": "post-primary-outcome-universality-diagnostic",
        "n_systems_major_families": len(frame),
        "n_adsorbate_families": len(major_names),
        "n_dois": int(frame["doi"].nunique()),
        "pooled_vs_family_intercepts": {
            "F": f_intercepts,
            "df_num": df_i_num,
            "df_den": df_i_den,
            "p_classical": float(stats.f.sf(f_intercepts, df_i_num, df_i_den)),
            "p_doi_wild_cluster": p_intercepts_wild,
        },
        "common_vs_family_specific_slopes": {
            "F": f_slopes,
            "df_num": df_s_num,
            "df_den": df_s_den,
            "p_classical": float(stats.f.sf(f_slopes, df_s_num, df_s_den)),
            "p_doi_wild_cluster": p_slopes_wild,
        },
        "multilevel_decomposition": {
            "pooled_slope_all_primary_systems": pooled_slope,
            "within_adsorbate_slope_major_families": within_slope,
            "within_adsorbate_r2": within_r2,
            "between_adsorbate_mean_slope": float(between_slope),
            "between_adsorbate_mean_r2": between_r2,
        },
        "leave_one_adsorbate_out": {
            "pooled_r2": float(1 - total_sse / total_denominator),
            "median_family_r2": float(family_prediction["r2_within_heldout_family"].median()),
            "families_with_negative_r2": int((family_prediction["r2_within_heldout_family"] < 0).sum()),
            "families_total": len(family_prediction),
        },
        "families_different_from_pooled_after_holm": int(
            (families["p_difference_from_pooled_holm"] < 0.05).sum()
        ),
        "interpretation": "A strong pooled association is not a universal coefficient when DOI-clustered family intercept and slope heterogeneity are retained.",
    }
    (RESULTS / "isodb_universality_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
