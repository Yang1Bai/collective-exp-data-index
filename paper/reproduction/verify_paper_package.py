#!/usr/bin/env python3
"""Fail-closed audit of the manuscript-facing evidence package."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]


def load_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def json_value(document: Any, dotted_path: str) -> Any:
    value = document
    for token in dotted_path.split("."):
        if isinstance(value, list):
            value = value[int(token)]
        else:
            value = value[token]
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: Any, expected: float, label: str, tolerance: float = 1e-12) -> None:
    require(isinstance(actual, (int, float)), f"{label}: expected a number")
    require(
        math.isclose(float(actual), expected, rel_tol=tolerance, abs_tol=tolerance),
        f"{label}: {actual!r} != {expected!r}",
    )


def iter_paths(value: str) -> Iterable[str]:
    for item in value.split(";"):
        item = item.strip()
        if item:
            yield item


def verify_claim_paths() -> int:
    manifest = ROOT / "paper/claims/claim_manifest.csv"
    fields = ("model_definition", "design", "result", "verification", "source_data", "figure")
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 6, f"claim manifest: expected 6 rows, found {len(rows)}")
    for row in rows:
        for field in fields:
            for relative in iter_paths(row[field]):
                require((ROOT / relative).exists(), f"missing {row['claim_id']} {field}: {relative}")
    return len(rows)


def verify_dataset_ledger() -> int:
    with (ROOT / "research/data/ANALYSED_RESOURCE_LEDGER.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        ledger = {row["resource_id"]: row for row in csv.DictReader(handle)}
    with (ROOT / "paper/data/datasets.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 14, f"dataset manifest: expected 14 rows, found {len(rows)}")
    for row in rows:
        source = ledger.get(row["resource_id"])
        require(source is not None, f"dataset absent from ledger: {row['resource_id']}")
        for field in ("primary_url", "doi", "upstream_license"):
            require(
                row[field] == source[field],
                f"{row['resource_id']} {field} differs from resource ledger",
            )
        for relative in iter_paths(row["repository_representation"]):
            require((ROOT / relative).exists(), f"missing repository data representation: {relative}")
    return len(rows)


def verify_figure_manifest() -> int:
    manifest = ROOT / "analysis/figures/final_manuscript_svgs/source_manifest.csv"
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 12, f"figure manifest: expected 12 rows, found {len(rows)}")
    for row in rows:
        require((ROOT / row["tracked_svg"]).is_file(), f"missing tracked SVG: {row['tracked_svg']}")
        for relative in iter_paths(row["evidence_source"]):
            require((ROOT / relative).exists(), f"missing figure evidence source: {relative}")
    return len(rows)


def verify_markdown_links() -> int:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    count = 0
    for document in sorted((ROOT / "paper").rglob("*.md")):
        for target in pattern.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            relative = target.split("#", 1)[0]
            require((document.parent / relative).exists(), f"broken link in {document}: {target}")
            count += 1
    return count


def verify_article_source_data() -> int:
    interval_paths = {
        ("broad_scalar_screen", "programme_mean_OOD_gain"): "programme_inference.ci95",
        ("liasf6_external", "relative_log_RMSE_gain_vs_state_only"): (
            "corrected_contrasts.state_only.relative_log_rmse_gain_ci95"
        ),
        ("solventseg_rank", "five_anchor_Spearman_gain"): (
            "solventseg.five_anchor_contrasts."
            "programme_balanced_rank_consensus_frozen.spearman_gain_ci95"
        ),
        ("solventseg_rank", "absolute_log_RMSE_gain_vs_state_only"): (
            "solventseg.routing.prediction_gate."
            "portfolio_vs_state_relative_log_rmse_gain_ci95"
        ),
        ("finales_boundary", "concordance_difference"): "primary.bootstrap_ci95",
    }
    cache: dict[str, Any] = {}
    with (ROOT / "paper/data/article_source_data.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        artifact = row["artifact"]
        if artifact not in cache:
            cache[artifact] = load_json(artifact)
        document = cache[artifact]
        actual = json_value(document, row["json_path"])
        if row["metric"] == "recipient_models_tested":
            actual = len(actual)
        close(actual, float(row["value"]), f"{row['claim_id']}::{row['metric']}")
        key = (row["claim_id"], row["metric"])
        if row["interval_low"] or row["interval_high"]:
            require(key in interval_paths, f"interval source path missing for {key}")
            interval = json_value(document, interval_paths[key])
            close(interval[0], float(row["interval_low"]), f"{key} interval low")
            close(interval[1], float(row["interval_high"]), f"{key} interval high")
    return len(rows)


def verify_headlines() -> None:
    broad = load_json("analysis/results/multi_target_ood_summary.json")
    require(broad["targets"] == 8, "broad screen target count changed")
    require(broad["real_edges"] == 40, "broad screen edge count changed")
    require(
        broad["programme_inference"]["programme_clusters_with_full_pass"] == 0,
        "broad screen complete-pass count changed",
    )
    close(
        broad["programme_inference"]["mean_primary_ood_gain"],
        0.009247991733308742,
        "broad programme mean gain",
    )

    specgen = load_json("analysis/results/transfer_screening.json")
    comparison = {row["method"]: row for row in specgen["aggregate"]["comparison"]}
    require(specgen["screening_config"]["epochs"] == 40, "SpecGen screening epoch count changed")
    require(specgen["screening_config"]["seed"] == 20260802, "SpecGen screening seed changed")
    close(
        comparison["contrastive"]["median_spearman"],
        0.5994560361010429,
        "SpecGen contrastive median Spearman",
    )
    close(
        comparison["baseline"]["median_spearman"],
        0.5836792647722425,
        "SpecGen baseline median Spearman",
    )
    require(
        comparison["contrastive"]["positive_directions"] == 3,
        "SpecGen positive-direction count changed",
    )

    liasf6 = load_json("analysis/results/bamboomixer_LiAsF6_only_summary.json")
    close(liasf6["corrected_external_metrics"]["raw_r2"], 0.60708008274443, "LiAsF6 raw R2")
    close(
        liasf6["corrected_external_metrics"]["spearman"],
        0.8639511089469837,
        "LiAsF6 Spearman",
    )
    close(
        liasf6["corrected_contrasts"]["state_only"]["relative_log_rmse_gain_mean"],
        0.2740993466742442,
        "LiAsF6 log-RMSE gain",
    )

    solventseg = load_json("analysis/results/bamboomixer_cross_database_interaction_summary.json")
    ss = solventseg["solventseg"]
    close(
        ss["five_anchor_macro"]["programme_balanced_rank_consensus_frozen"]["spearman"],
        0.8853229607297355,
        "SolventSeg formal source Spearman",
    )
    close(
        ss["five_anchor_macro"]["target_only_ridge"]["spearman"],
        0.16189172532352053,
        "SolventSeg prespecified Ridge Spearman",
    )
    close(
        ss["routing"]["prediction_gate"]["portfolio_vs_state_relative_log_rmse_gain"],
        -0.1800366403692153,
        "SolventSeg absolute-prediction contrast",
    )

    stress = load_json("analysis/results/bamboomixer_recipient_baseline_stress_test_summary.json")
    require(len(stress["five_anchor"]["recipient_macro"]) == 13, "SolventSeg stress-test model count changed")
    close(
        stress["five_anchor"]["source_portfolio"]["spearman"],
        0.910299826143778,
        "SolventSeg stress-test source Spearman",
    )
    close(
        stress["five_anchor"]["recipient_macro"][0]["spearman"],
        0.5366383640583346,
        "SolventSeg strongest tested target Spearman",
    )

    finales = load_json("analysis/results/finales_rank_replication_summary.json")
    require(finales["decision"] == "not-replicated", "FINALES decision changed")
    require(finales["success_gate_passed"] is False, "FINALES success gate changed")
    close(finales["primary"]["concordance_advantage"], -0.08873114463176579, "FINALES difference")
    close(finales["primary"]["permutation_p"], 0.13093453273363317, "FINALES permutation P")
    verify_finales_compact_outputs(finales)


def pairwise_concordance(
    rows: list[dict[str, str]], score_column: str, tolerance: float
) -> tuple[float, int]:
    agreements = 0
    eligible = 0
    for left, right in itertools.combinations(rows, 2):
        if abs(float(left["temperature_C"]) - float(right["temperature_C"])) > tolerance:
            continue
        outcome_delta = float(left["conductivity"]) - float(right["conductivity"])
        score_delta = float(left[score_column]) - float(right[score_column])
        if outcome_delta == 0.0 or score_delta == 0.0:
            continue
        eligible += 1
        agreements += (outcome_delta > 0.0) == (score_delta > 0.0)
    require(eligible > 0, f"FINALES has no eligible pairs for {score_column}")
    return agreements / eligible, eligible


def verify_finales_compact_outputs(summary: Any) -> None:
    with (ROOT / "analysis/results/finales_rank_replication_candidates.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = [row for row in csv.DictReader(handle) if row["split"] == "evaluation"]
    require(len(rows) == 16, f"FINALES evaluation count changed: {len(rows)}")
    tolerance = float(summary["primary"]["temperature_tolerance_C"])
    donor, donor_pairs = pairwise_concordance(rows, "calisol_rank_score", tolerance)
    baseline_name = str(summary["primary"]["strongest_recipient_baseline"])
    baseline, baseline_pairs = pairwise_concordance(rows, baseline_name, tolerance)
    close(donor, float(summary["primary"]["donor_concordance"]), "FINALES compact donor concordance")
    close(
        baseline,
        float(summary["primary"]["strongest_baseline_concordance"]),
        "FINALES compact baseline concordance",
    )
    require(donor_pairs == int(summary["primary"]["eligible_pairs"]), "FINALES eligible-pair count changed")
    complete = load_json("analysis/results/finales_rank_replication_complete.json")
    require(
        baseline_pairs == int(complete["baseline_eligible_pairs"]),
        "FINALES baseline eligible-pair count changed",
    )
    with (ROOT / "analysis/results/finales_rank_replication_shuffled_null.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        shuffled = [float(row["shuffled_donor_concordance"]) for row in csv.DictReader(handle)]
    require(len(shuffled) == 2000, f"FINALES shuffled-control count changed: {len(shuffled)}")
    permutation_p = (1 + sum(value >= donor for value in shuffled)) / (len(shuffled) + 1)
    close(permutation_p, float(summary["primary"]["permutation_p"]), "FINALES compact permutation P")


def verify_checksums() -> int:
    checksum_file = ROOT / "paper/artifact_checksums.sha256"
    count = 0
    for raw in checksum_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split(None, 1)
        relative = relative.lstrip(" *")
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        require(digest == expected, f"checksum changed: {relative}")
        count += 1
    require(count >= 20, f"checksum manifest unexpectedly short: {count}")
    return count


def main() -> None:
    claims = verify_claim_paths()
    datasets = verify_dataset_ledger()
    figures = verify_figure_manifest()
    links = verify_markdown_links()
    metrics = verify_article_source_data()
    verify_headlines()
    checksums = verify_checksums()
    print(
        "Submission package verified: "
        f"{claims} claims, {datasets} datasets, {figures} figure files, "
        f"{metrics} source-data values, {links} relative links, {checksums} checksums."
    )


if __name__ == "__main__":
    main()
