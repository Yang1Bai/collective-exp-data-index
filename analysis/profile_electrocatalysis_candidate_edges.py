"""Structural and quality audit for electrocatalysis transfer candidates.

This script intentionally profiles schema, provenance, support, missingness,
and overlap before fitting recipient-outcome models.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, cross_val_predict


ROOT = Path(__file__).resolve().parents[1] / "Dataset"
HER_PATH = ROOT / "Ref8" / "her_catalysts_dataset_v1.csv"
OER_PATH = ROOT / "ref6" / "Data.xlsx"
RUNZE_INITIAL_PATH = ROOT / "Runze" / "Initialdataset.csv"
RUNZE_FOLLOWUPS = {
    "best": ROOT / "Runze" / "Best_performing.csv",
    "high_confidence": ROOT / "Runze" / "High_confidence.csv",
    "low_confidence": ROOT / "Runze" / "Low_confidence.csv",
}
FORMATE_PATH = ROOT / "Ref2" / "41586_2025_9640_MOESM6_ESM.xlsx"
SOLGEL_PATH = ROOT / "Sol-gel synthesis-Re activity_Sissi.csv"

HER_ELEMENTS = [
    "Ag", "Al", "Au", "Co", "Cr", "Cu", "Fe", "Ir", "Mg", "Mn",
    "Mo", "Ni", "Pd", "Pt", "Rh", "Ru", "W", "Zn",
]
OER_ELEMENTS = ["Co", "Ni", "Cu", "Mg", "Cd", "Zn"]
RUNZE_ELEMENT_COLUMNS = {
    "Fe": ["FeCl3_mmol", "Fe(NO3)3_mmol", "Fe2(SO4)3_mmol", "FeCl2_mmol", "Fe(NO3)2_mmol", "FeSO4_mmol"],
    "Ni": ["NiCl2_mmol", "Ni(NO3)2_mmol", "NiSO4_mmol"],
    "Cr": ["CrCl3_mmol", "Cr(NO3)3_mmol", "Cr2(SO4)3_mmol"],
    "Zn": ["ZnCl2_mmol", "Zn(NO3)2_mmol", "ZnSO4_mmol"],
    "Cu": ["CuCl2_mmol", "Cu(NO3)2_mmol", "CuSO4_mmol"],
    "Co": ["CoCl2_mmol", "Co(NO3)2_mmol", "CoSO4_mmol"],
    "Mn": ["MnCl2_mmol", "Mn(NO3)2_mmol", "MnSO4_mmol"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_summary(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    return {
        "nonnull": int(finite.size),
        "min": float(finite.min()) if len(finite) else None,
        "median": float(finite.median()) if len(finite) else None,
        "max": float(finite.max()) if len(finite) else None,
    }


def composition_key(frame: pd.DataFrame, columns: list[str], decimals: int = 6) -> pd.Series:
    numeric = frame[columns].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    totals = numeric.sum(axis=1).replace(0, np.nan)
    normalized = numeric.div(totals, axis=0).fillna(0.0).round(decimals)
    return normalized.astype(str).agg("|".join, axis=1)


def add_runze_elements(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    for element, columns in RUNZE_ELEMENT_COLUMNS.items():
        available = [column for column in columns if column in work.columns]
        work[element] = (
            work[available].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(axis=1)
            if available
            else 0.0
        )
    totals = work[list(RUNZE_ELEMENT_COLUMNS)].sum(axis=1).replace(0, np.nan)
    for element in RUNZE_ELEMENT_COLUMNS:
        work[f"frac_{element}"] = work[element] / totals
    return work


def parse_formula(formula: object) -> dict[str, float]:
    if not isinstance(formula, str) or not formula.strip():
        return {}
    parts = re.findall(r"([A-Z][a-z]?)([0-9]*\.?[0-9]*)", formula.strip())
    if not parts:
        return {}
    values = {
        element: float(amount) if amount else 1.0
        for element, amount in parts
    }
    total = sum(values.values())
    return {element: value / total for element, value in values.items()} if total > 0 else {}


def main() -> None:
    her = pd.read_csv(HER_PATH)
    oer = pd.read_excel(OER_PATH, sheet_name="Sheet1")
    runze_initial = add_runze_elements(pd.read_csv(RUNZE_INITIAL_PATH))
    runze_followups = {
        name: add_runze_elements(pd.read_csv(path))
        for name, path in RUNZE_FOLLOWUPS.items()
    }
    formate = pd.read_excel(FORMATE_PATH, sheet_name="Fig. 1d-e", header=1)
    solgel = pd.read_csv(SOLGEL_PATH)
    solgel["parsed_formula"] = solgel["Formula"].map(parse_formula)

    her_key = composition_key(her, HER_ELEMENTS)
    oer_key = composition_key(oer, OER_ELEMENTS)
    runze_columns = [f"frac_{element}" for element in RUNZE_ELEMENT_COLUMNS]
    initial_key = composition_key(runze_initial, runze_columns)

    her_alkaline = her.loc[her["pH"].astype(str).str.strip().str.lower() == "alkaline"].copy()
    her_alkaline_key = composition_key(her_alkaline, HER_ELEMENTS)
    target_elements_in_her = {}
    for element in sorted(set(OER_ELEMENTS) | set(RUNZE_ELEMENT_COLUMNS)):
        values = (
            pd.to_numeric(her_alkaline[element], errors="coerce").fillna(0)
            if element in her_alkaline
            else pd.Series(0.0, index=her_alkaline.index)
        )
        target_elements_in_her[element] = int((values > 0).sum())
    target_rows_fully_supported_by_her = int(
        (
            oer[OER_ELEMENTS]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .apply(
                lambda row: all(
                    value <= 0 or target_elements_in_her[element] > 0
                    for element, value in row.items()
                ),
                axis=1,
            )
        ).sum()
    )
    her_reliably_supported_runze_elements = {
        element
        for element in RUNZE_ELEMENT_COLUMNS
        if target_elements_in_her.get(element, 0) >= 10
    }
    her_strict_runze_source_mask = (
        her_alkaline[
            [
                element
                for element in HER_ELEMENTS
                if element not in her_reliably_supported_runze_elements
            ]
        ]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .abs()
        .sum(axis=1)
        == 0
    )
    her_strict_runze_source = her_alkaline.loc[her_strict_runze_source_mask].copy()
    runze_supported_by_her_mask = pd.Series(True, index=runze_initial.index)
    for element in RUNZE_ELEMENT_COLUMNS:
        if element not in her_reliably_supported_runze_elements:
            runze_supported_by_her_mask &= runze_initial[element].fillna(0) == 0

    source_x = her_alkaline[HER_ELEMENTS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    source_y = pd.to_numeric(her_alkaline["onset_potential"], errors="coerce")
    source_groups = her_alkaline["Reference"].astype(str)
    source_skill = {}
    source_models = {
        "extra_trees": ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            max_features=1.0,
            random_state=20260730,
            n_jobs=-1,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            min_samples_leaf=10,
            random_state=20260730,
        ),
    }
    splitter = GroupKFold(n_splits=5)
    for name, model in source_models.items():
        prediction = cross_val_predict(
            model,
            source_x,
            source_y,
            groups=source_groups,
            cv=splitter,
            n_jobs=1,
        )
        source_skill[name] = {
            "grouped_oof_r2": float(r2_score(source_y, prediction)),
            "grouped_oof_spearman": float(stats.spearmanr(source_y, prediction).statistic),
        }

    strict_source_skill = {}
    if her_strict_runze_source["Reference"].nunique() >= 3:
        strict_x = her_strict_runze_source[
            sorted(her_reliably_supported_runze_elements)
        ].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        strict_y = pd.to_numeric(
            her_strict_runze_source["onset_potential"], errors="coerce"
        )
        strict_groups = her_strict_runze_source["Reference"].astype(str)
        strict_splitter = GroupKFold(
            n_splits=min(5, strict_groups.nunique())
        )
        for name, model in source_models.items():
            prediction = cross_val_predict(
                model,
                strict_x,
                strict_y,
                groups=strict_groups,
                cv=strict_splitter,
                n_jobs=1,
            )
            strict_source_skill[name] = {
                "grouped_oof_r2": float(r2_score(strict_y, prediction)),
                "grouped_oof_spearman": float(
                    stats.spearmanr(strict_y, prediction).statistic
                ),
            }

    donor_supported_elements = set(OER_ELEMENTS)
    runze_element_amounts = runze_initial[list(RUNZE_ELEMENT_COLUMNS)].fillna(0)
    unsupported_runze = [
        element for element in RUNZE_ELEMENT_COLUMNS if element not in donor_supported_elements
    ]
    runze_supported_mask = (runze_element_amounts[unsupported_runze].sum(axis=1) == 0)

    solgel_activity = solgel.loc[
        pd.to_numeric(solgel["OP (10mA/cm2)"], errors="coerce").notna()
        & solgel["parsed_formula"].map(bool)
    ].copy()
    solgel_elements = sorted(
        {element for composition in solgel_activity["parsed_formula"] for element in composition}
    )
    solgel_element_counts = {
        element: int(
            solgel_activity["parsed_formula"].map(lambda composition: composition.get(element, 0) > 0).sum()
        )
        for element in solgel_elements
    }
    solgel_reliably_supported = {
        element for element, count in solgel_element_counts.items() if count >= 10
    }
    runze_supported_by_solgel_mask = pd.Series(True, index=runze_initial.index)
    for element in RUNZE_ELEMENT_COLUMNS:
        if element not in solgel_reliably_supported:
            runze_supported_by_solgel_mask &= runze_initial[element].fillna(0) == 0

    solgel_supported_by_ref6_mask = solgel_activity["parsed_formula"].map(
        lambda composition: bool(composition)
        and all(element in donor_supported_elements for element in composition)
    )
    solgel_supported_by_runze_mask = solgel_activity["parsed_formula"].map(
        lambda composition: bool(composition)
        and all(element in RUNZE_ELEMENT_COLUMNS for element in composition)
    )

    followup_profiles = {}
    for name, frame in runze_followups.items():
        key = composition_key(frame, runze_columns)
        overlap = key.isin(set(initial_key))
        unsupported = [
            element for element in RUNZE_ELEMENT_COLUMNS if element not in donor_supported_elements
        ]
        support_mask = frame[unsupported].fillna(0).sum(axis=1) == 0
        followup_profiles[name] = {
            "rows": int(len(frame)),
            "exact_composition_overlap_with_initial": int(overlap.sum()),
            "source_element_supported_rows": int(support_mask.sum()),
            "lsv": finite_summary(frame["lsv"]),
            "target_model_prediction_nonnull": int(
                pd.to_numeric(frame.get("lsv_model_pred"), errors="coerce").notna().sum()
            ),
        }

    output = {
        "status": "structural-audit-before-recipient-outcome-modeling",
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [
                HER_PATH,
                OER_PATH,
                RUNZE_INITIAL_PATH,
                *RUNZE_FOLLOWUPS.values(),
                FORMATE_PATH,
                SOLGEL_PATH,
            ]
        },
        "datasets": {
            "her_literature": {
                "rows": int(len(her)),
                "references": int(her["Reference"].nunique()),
                "unique_formulas": int(her["Formula"].nunique()),
                "unique_composition_keys": int(her_key.nunique()),
                "pH_counts": her["pH"].astype(str).str.strip().value_counts().to_dict(),
                "onset_potential": finite_summary(her["onset_potential"]),
                "tafel_slope": finite_summary(her["tafel_slope"]),
                "exact_duplicate_rows": int(her.duplicated().sum()),
                "formula_pH_duplicate_rows": int(
                    her.duplicated(["Formula", "pH"], keep=False).sum()
                ),
            },
            "her_alkaline_primary_source": {
                "rows": int(len(her_alkaline)),
                "references": int(her_alkaline["Reference"].nunique()),
                "unique_formulas": int(her_alkaline["Formula"].nunique()),
                "unique_composition_keys": int(her_alkaline_key.nunique()),
                "onset_potential": finite_summary(her_alkaline["onset_potential"]),
                "tafel_slope": finite_summary(her_alkaline["tafel_slope"]),
                "target_element_row_support": target_elements_in_her,
                "composition_only_grouped_source_skill": source_skill,
                "strict_runze_chemistry_source": {
                    "allowed_elements": sorted(
                        her_reliably_supported_runze_elements
                    ),
                    "rows": int(len(her_strict_runze_source)),
                    "references": int(
                        her_strict_runze_source["Reference"].nunique()
                    ),
                    "unique_formulas": int(
                        her_strict_runze_source["Formula"].nunique()
                    ),
                    "composition_only_grouped_source_skill": strict_source_skill,
                },
            },
            "oer_high_entropy_recipient": {
                "rows": int(len(oer)),
                "unique_composition_keys": int(oer_key.nunique()),
                "duplicate_composition_rows": int(oer_key.duplicated(keep=False).sum()),
                "composition_sum": finite_summary(oer[OER_ELEMENTS].sum(axis=1)),
                "overpotential_mV": finite_summary(oer["η10 (mV)"]),
                "rows_with_all_six_elements_positive": int((oer[OER_ELEMENTS] > 0).all(axis=1).sum()),
                "rows_element_supported_by_alkaline_her": target_rows_fully_supported_by_her,
            },
            "runze_initial_recipient": {
                "rows": int(len(runze_initial)),
                "unique_composition_keys": int(initial_key.nunique()),
                "duplicate_composition_rows": int(initial_key.duplicated(keep=False).sum()),
                "lsv": finite_summary(runze_initial["lsv"]),
                "source_element_supported_rows": int(runze_supported_mask.sum()),
                "unsupported_elements": unsupported_runze,
                "temperature_counts": runze_initial["Temperature"].value_counts().to_dict(),
            },
            "runze_followups": followup_profiles,
            "formate_oxidation_control": {
                "rows": int(len(formate)),
                "elements": [
                    column for column in ["Cr", "Pd", "Pt", "Cu", "Au", "Ir", "Ce", "Nb"]
                    if column in formate.columns
                ],
                "target": finite_summary(formate["Experiment (mW/cm2)"]),
            },
            "solgel_oer": {
                "rows": int(len(solgel)),
                "formula_nonnull": int(solgel["Formula"].notna().sum()),
                "unique_formulas": int(solgel["Formula"].nunique(dropna=True)),
                "overpotential_nonnull": int(
                    pd.to_numeric(solgel["OP (10mA/cm2)"], errors="coerce").notna().sum()
                ),
                "stability_nonnull": int(
                    pd.to_numeric(solgel["ICP-2h (%)"], errors="coerce").notna().sum()
                ),
                "synthesis_label_counts": solgel["Synthesis"].astype(str).value_counts().head(10).to_dict(),
                "activity_formula_element_counts": solgel_element_counts,
                "reliably_supported_elements_at_least_10_activity_rows": sorted(
                    solgel_reliably_supported
                ),
                "activity_rows_strictly_supported_by_ref6_elements": int(
                    solgel_supported_by_ref6_mask.sum()
                ),
                "activity_rows_strictly_supported_by_runze_elements": int(
                    solgel_supported_by_runze_mask.sum()
                ),
            },
        },
        "candidate_edges": {
            "alkaline_HER_to_high_entropy_OER": {
                "distance": "cross-reaction, cross-database",
                "shared_target_elements": OER_ELEMENTS,
                "recipient_rows_supported_at_element-presence_level": target_rows_fully_supported_by_her,
                "primary_risk": "literature HER condition and morphology heterogeneity",
            },
            "alkaline_HER_to_runze_OER": {
                "distance": "cross-reaction, cross-database",
                "shared_reliably_supported_elements": sorted(
                    her_reliably_supported_runze_elements
                ),
                "recipient_initial_rows_strictly_within_source_element_set": int(
                    runze_supported_by_her_mask.sum()
                ),
                "recipient_unique_compositions_in_supported_scope": int(
                    initial_key[runze_supported_by_her_mask].nunique()
                ),
                "eligibility": (
                    "reject"
                    if (
                        len(her_strict_runze_source) < 40
                        or her_strict_runze_source["Reference"].nunique() < 10
                        or strict_source_skill.get("extra_trees", {}).get(
                            "grouped_oof_spearman", -1.0
                        )
                        <= 0
                    )
                    else "eligible"
                ),
                "primary_risk": "HER labels aggregate literature-specific surface, pH, and protocol variation",
            },
            "high_entropy_OER_to_runze_OER": {
                "distance": "same endpoint, cross-programme",
                "shared_elements": sorted(donor_supported_elements & set(RUNZE_ELEMENT_COLUMNS)),
                "recipient_initial_rows_strictly_within_source_element_set": int(runze_supported_mask.sum()),
                "primary_risk": "precursor recipe is not measured catalyst composition",
            },
            "solgel_OER_to_runze_OER": {
                "distance": "same endpoint, cross-programme",
                "shared_reliably_supported_elements": sorted(
                    solgel_reliably_supported & set(RUNZE_ELEMENT_COLUMNS)
                ),
                "recipient_initial_rows_strictly_within_source_element_set": int(
                    runze_supported_by_solgel_mask.sum()
                ),
                "primary_risk": "formula fractions and precursor molar amounts are imperfectly aligned representations",
            },
            "high_entropy_OER_to_solgel_OER": {
                "distance": "same endpoint, cross-programme",
                "recipient_activity_rows_strictly_within_source_element_set": int(
                    solgel_supported_by_ref6_mask.sum()
                ),
                "primary_risk": "high-entropy source contains every element in every sample and cannot learn zero-element boundaries",
            },
            "runze_OER_to_solgel_OER": {
                "distance": "same endpoint, cross-programme",
                "recipient_activity_rows_strictly_within_source_element_set": int(
                    solgel_supported_by_runze_mask.sum()
                ),
                "primary_risk": "small source and process-dependent electrodeposition outcomes",
            },
            "formate_to_OER": {
                "distance": "cross-reaction, cross-database",
                "shared_elements_with_high_entropy_OER": sorted(
                    set(OER_ELEMENTS) & set(formate.columns)
                ),
                "eligibility": "reject if fewer than three shared active elements",
            },
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
