"""Audit an external experimental band-gap donor for perovskite OOD use.

This script does not fit a photovoltaic outcome model.  It determines whether
the proposed donor-recipient edge has enough independent, chemically aligned,
and composition-resolved evidence to justify a formal transfer benchmark.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import bandgap_borrowing_common as bg


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
AUDIT_JSON = RESULTS / "bandgap_perovskite_pair_audit.json"
SOURCE_CARDS_CSV = RESULTS / "bandgap_source_cards_strict.csv"


def fraction(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def numeric_distribution(values: pd.Series) -> dict[str, float | int]:
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric[np.isfinite(numeric)].to_numpy(float)
    if not len(numeric):
        return {"n": 0}
    return {
        "n": int(len(numeric)),
        "min": float(np.min(numeric)),
        "q05": float(np.quantile(numeric, 0.05)),
        "q25": float(np.quantile(numeric, 0.25)),
        "median": float(np.median(numeric)),
        "q75": float(np.quantile(numeric, 0.75)),
        "q95": float(np.quantile(numeric, 0.95)),
        "max": float(np.max(numeric)),
    }


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


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    target = bg.load_recipient()
    source_raw = bg.load_donor_raw()
    source, recovered_n = bg.recover_donor_compositions(
        source_raw, target
    )

    target_dois = set(target["doi_norm"]) - {""}
    source_dois = set(source["doi_norm"]) - {""}
    doi_overlap = target_dois & source_dois

    robust_all = bg.robust_donor_records(
        source,
        target=None,
        exclude_target_dois=False,
    )
    robust_independent = bg.robust_donor_records(
        source,
        target=target,
        exclude_target_dois=True,
    )
    cards = bg.aggregate_donor(robust_independent)
    cards.to_csv(SOURCE_CARDS_CSV, index=False)
    hse_cards_all = bg.load_hse_cards()
    target_compositions_all = set(target["composition_key"]) - {""}
    hse_cards = hse_cards_all[
        ~hse_cards_all["composition_key"].isin(target_compositions_all)
        & hse_cards_all["band_gap_hse_iqr"].le(1.0)
    ].copy()
    hybrid3_cards = bg.load_hybrid3_cards(
        target=target,
        exclude_target_dois=True,
    )

    target_valid = target[
        target["doi_norm"].ne("")
        & target["ions_valid"]
        & target["composition_key"].ne("")
    ].copy()
    target_valid["band_gap_valid"] = target_valid["band_gap"].between(
        0.2, 4.0, inclusive="both"
    )
    target_valid["direct_band_gap"] = (
        target_valid["band_gap_valid"]
        & target_valid["band_gap_estimation_basis"].map(
            directly_measured_basis
        )
    )
    target_valid["pce_valid"] = target_valid["pce"].between(
        0.0, 40.0, inclusive="both"
    )

    donor_compositions = set(cards["composition_key"]) - {""}
    donor_systems = (
        (
            set(cards["element_system"])
            | set(hse_cards["element_system"])
            | set(hybrid3_cards["element_system"])
        )
        - {""}
    )
    donor_formula_text = set(robust_independent["formula_text_key"]) - {""}
    target_valid["exact_composition_supported"] = target_valid[
        "composition_key"
    ].isin(donor_compositions)
    target_valid["element_system_supported"] = target_valid[
        "element_system"
    ].isin(donor_systems)
    target_valid["formula_text_supported"] = target_valid[
        "formula_text_key"
    ].isin(donor_formula_text)
    hybrid3_compositions = set(hybrid3_cards["composition_key"]) - {""}
    target_valid["hybrid3_exact_composition_supported"] = target_valid[
        "composition_key"
    ].isin(hybrid3_compositions)

    replicated_cards = cards[
        cards["n_dois"].ge(2) & cards["band_gap_iqr"].le(1.0)
    ].copy()
    replicated_compositions = set(replicated_cards["composition_key"])
    target_valid["replicated_composition_supported"] = target_valid[
        "composition_key"
    ].isin(replicated_compositions)

    target_elements = set().union(
        *(
            set(item)
            for item in target_valid["composition_dict"]
            if item
        )
    )
    halide_perovskite_like = robust_independent[
        robust_independent["composition_dict"].map(
            lambda item: bool(
                {"I", "Br", "Cl"}.intersection(item)
                and {"Pb", "Sn", "Bi", "Sb"}.intersection(item)
            )
        )
    ].copy()

    unique_target_compositions = target_valid.drop_duplicates(
        "composition_key"
    )
    unique_target_families = target_valid.drop_duplicates("site_family")
    supported_rows = int(target_valid["element_system_supported"].sum())
    supported_compositions = int(
        unique_target_compositions["element_system_supported"].sum()
    )
    supported_bandgap_rows = int(
        (
            target_valid["element_system_supported"]
            & target_valid["band_gap_valid"]
        ).sum()
    )
    direct_bandgap_compositions = int(
        target_valid.loc[
            target_valid["direct_band_gap"], "composition_key"
        ].nunique()
    )

    gate = {
        "recipient_rows_with_doi_and_composition_at_least_10000": (
            len(target_valid) >= 10_000
        ),
        "independent_donor_composition_cards_at_least_1000": (
            len(cards) >= 1_000
        ),
        "independent_hse_composition_cards_at_least_5000": (
            len(hse_cards) >= 5_000
        ),
        "independent_halide_perovskite_records_at_least_100": (
            len(halide_perovskite_like) >= 100
        ),
        "recipient_bandgap_validation_rows_at_least_1000": (
            int(target_valid["band_gap_valid"].sum()) >= 1_000
        ),
        "recipient_direct_bandgap_rows_at_least_100": (
            int(target_valid["direct_band_gap"].sum()) >= 100
        ),
        "recipient_direct_bandgap_compositions_at_least_100": (
            direct_bandgap_compositions >= 100
        ),
    }
    proceed = all(gate.values())

    audit = {
        "status": "eligible-for-source-skill-benchmark"
        if proceed
        else "insufficient-pair-support",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "donor": {
            "name": "ChemDataExtractor Band Gap Database",
            "zip": str(bg.DONOR_ZIP.relative_to(bg.ROOT)).replace("\\", "/"),
            "zip_sha256": bg.sha256(bg.DONOR_ZIP),
            "raw_rows": int(len(source_raw)),
            "raw_dois": int(len(source_dois)),
            "valid_compositions_original": int(
                source_raw["composition_key"].ne("").sum()
            ),
            "perovskite_name_compositions_recovered": recovered_n,
            "robust_rows_before_recipient_doi_exclusion": int(
                len(robust_all)
            ),
            "robust_rows_after_recipient_doi_exclusion": int(
                len(robust_independent)
            ),
            "composition_cards_after_doi_exclusion": int(len(cards)),
            "replicated_low_disagreement_cards": int(len(replicated_cards)),
            "halide_perovskite_like_rows_after_doi_exclusion": int(
                len(halide_perovskite_like)
            ),
            "band_gap_distribution": numeric_distribution(
                robust_independent["band_gap"]
            ),
        },
        "hse_donor": {
            "name": "SNUMAT hybrid-functional band-gap database",
            "zip": str(bg.HSE_ZIP.relative_to(bg.ROOT)).replace("\\", "/"),
            "zip_sha256": bg.sha256(bg.HSE_ZIP),
            "raw_structures": int(hse_cards_all.attrs["raw_structures"]),
            "composition_cards": int(len(hse_cards_all)),
            "cards_after_exact_recipient_composition_exclusion": int(
                len(hse_cards)
            ),
            "band_gap_distribution": numeric_distribution(
                hse_cards["band_gap_hse"]
            ),
        },
        "hybrid3_donor": {
            "name": "HybriD3 hybrid perovskite materials database",
            "csv_sha256": bg.sha256(bg.HYBRID3_CSV),
            "raw_rows": int(hybrid3_cards.attrs["raw_rows"]),
            "clean_rows_after_recipient_doi_exclusion": int(
                hybrid3_cards.attrs["clean_rows"]
            ),
            "composition_cards_after_recipient_doi_exclusion": int(
                len(hybrid3_cards)
            ),
            "exact_recipient_composition_rows_supported": int(
                target_valid[
                    "hybrid3_exact_composition_supported"
                ].sum()
            ),
        },
        "recipient": {
            "name": "NOMAD Perovskite Solar Cell Database",
            "csv": str(bg.RECIPIENT_CSV.relative_to(bg.ROOT)).replace(
                "\\", "/"
            ),
            "csv_sha256": bg.sha256(bg.RECIPIENT_CSV),
            "raw_rows": int(len(target)),
            "unique_dois": int(len(target_dois)),
            "rows_with_doi_and_valid_ionic_composition": int(
                len(target_valid)
            ),
            "unique_compositions": int(
                target_valid["composition_key"].nunique()
            ),
            "unique_site_families": int(
                target_valid["site_family"].nunique()
            ),
            "band_gap_validation_rows": int(
                target_valid["band_gap_valid"].sum()
            ),
            "direct_band_gap_validation_rows": int(
                target_valid["direct_band_gap"].sum()
            ),
            "direct_band_gap_validation_compositions": (
                direct_bandgap_compositions
            ),
            "pce_rows": int(target_valid["pce_valid"].sum()),
            "band_gap_distribution": numeric_distribution(
                target_valid.loc[
                    target_valid["band_gap_valid"], "band_gap"
                ]
            ),
            "pce_distribution": numeric_distribution(
                target_valid.loc[target_valid["pce_valid"], "pce"]
            ),
            "elements": sorted(target_elements),
        },
        "independence": {
            "doi_overlap_count": int(len(doi_overlap)),
            "doi_overlap_fraction_of_recipient_dois": fraction(
                len(doi_overlap), len(target_dois)
            ),
            "all_recipient_dois_removed_from_model_donor": True,
        },
        "chemical_support_after_doi_exclusion": {
            "rows_with_exact_normalized_composition": int(
                target_valid["exact_composition_supported"].sum()
            ),
            "rows_with_replicated_exact_composition": int(
                target_valid["replicated_composition_supported"].sum()
            ),
            "rows_with_exact_formula_text": int(
                target_valid["formula_text_supported"].sum()
            ),
            "rows_with_exact_hybrid3_composition": int(
                target_valid[
                    "hybrid3_exact_composition_supported"
                ].sum()
            ),
            "rows_with_supported_element_system_from_either_donor": (
                supported_rows
            ),
            "row_fraction_with_supported_element_system": fraction(
                supported_rows, len(target_valid)
            ),
            "unique_compositions_with_supported_element_system": (
                supported_compositions
            ),
            "unique_composition_support_fraction": fraction(
                supported_compositions,
                len(unique_target_compositions),
            ),
            "unique_site_families": int(len(unique_target_families)),
            "reported_bandgap_rows_with_supported_element_system": (
                supported_bandgap_rows
            ),
        },
        "feasibility_gate": gate,
        "claim_guard": (
            "Passing this audit only permits a donor band-gap skill test. "
            "It does not show improved photovoltaic OOD prediction. The "
            "recipient-reported band gap is an oracle validation endpoint and "
            "must not enter the target-only or borrowed-feature model."
        ),
    }
    temporary = AUDIT_JSON.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(AUDIT_JSON)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
