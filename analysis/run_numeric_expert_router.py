#!/usr/bin/env python3
"""Build 34 target-free expert-routing edges and evaluate a numeric router."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.data import (
    CatalystSample,
    load_ocx24_csv,
    load_seccm_archives,
    load_specgen_archive,
)
from catalyst_attention.expert_router import ExpertRouter, train_expert_pair
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.numeric_router import (
    NumericRouterEdge,
    nested_group_predictions,
    summarize_predictions,
)
from catalyst_attention.opd_router import RouterState
from catalyst_attention.policy_transfer import edge_geometry
from catalyst_attention.training import (
    TrainingConfig,
    metrics,
    set_deterministic,
    targets_array,
)

DESIGN = ROOT / "analysis" / "catalyst_numeric_expert_router_design.json"
DB_PATH = ROOT / "collaborator_workspace" / "data" / "data" / "collective.sqlite"
SPECGEN_PATH = ROOT / "research" / "data" / "specgen.zip"
OCX24_PATH = ROOT / "research" / "data" / "ocx24.csv"
SECCM_CACHE = Path.home() / ".collective_data_cache" / "catalyst_attention"
DEFAULT_OUTPUT = ROOT / "analysis" / "results" / "catalyst_numeric_expert_router.json"
SEED = 20260813


@dataclass(frozen=True)
class Programme:
    suite: str
    name: str
    samples: list[CatalystSample]
    model_config: CatalystAttentionConfig
    epochs: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)}


def _write_json(path: Path, payload: Any) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _configs() -> dict[str, CatalystAttentionConfig]:
    return {
        "composition": CatalystAttentionConfig(
            d_model=48,
            n_heads=4,
            composition_layers=3,
            curve_layers=1,
            fusion_layers=1,
            feedforward_multiplier=3,
            use_curve=False,
            use_conditions=False,
            use_surface=False,
            dropout=0.1,
        ),
        "ocx24": CatalystAttentionConfig(
            d_model=48,
            n_heads=4,
            composition_layers=3,
            curve_layers=1,
            fusion_layers=1,
            feedforward_multiplier=3,
            use_curve=False,
            use_conditions=True,
            use_surface=False,
            dropout=0.1,
        ),
        "rich": CatalystAttentionConfig(
            d_model=64,
            n_heads=4,
            composition_layers=2,
            curve_layers=3,
            fusion_layers=2,
            feedforward_multiplier=3,
            dropout=0.1,
        ),
        "seccm": CatalystAttentionConfig(
            d_model=64,
            n_heads=4,
            composition_layers=2,
            curve_layers=3,
            fusion_layers=2,
            feedforward_multiplier=3,
            use_curve=True,
            use_conditions=False,
            use_surface=True,
            dropout=0.1,
        ),
    }


def load_programmes(
    *, alloy_epochs: int, rich_epochs: int
) -> tuple[dict[str, list[Programme]], list[Path]]:
    configs = _configs()
    suites: dict[str, list[Programme]] = {}
    inputs = [DB_PATH, OCX24_PATH, SPECGEN_PATH]

    suites["alloy_yield_strength"] = [
        Programme(
            "alloy_yield_strength",
            "steels",
            load_steels(DB_PATH, "yield strength"),
            configs["composition"],
            alloy_epochs,
        ),
        Programme(
            "alloy_yield_strength",
            "mpea",
            load_mpea(DB_PATH, "YS (MPa)"),
            configs["composition"],
            alloy_epochs,
        ),
        Programme(
            "alloy_yield_strength",
            "birdshot",
            load_birdshot(DB_PATH, "Yield Strength (MPa)"),
            configs["composition"],
            alloy_epochs,
        ),
    ]

    ocx24 = load_ocx24_csv(OCX24_PATH, "fe_co")
    ocx_by_program: dict[str, list[CatalystSample]] = {}
    for sample in ocx24:
        ocx_by_program.setdefault(sample.program, []).append(sample)
    suites["ocx24_fe_co"] = [
        Programme("ocx24_fe_co", name, samples, configs["ocx24"], rich_epochs)
        for name, samples in sorted(ocx_by_program.items())
    ]

    seccm_zip = SECCM_CACHE / "SECCM_dataset.zip"
    edx_zip = SECCM_CACHE / "EDX_dataset.zip"
    xps_zip = SECCM_CACHE / "XPS_dataset.zip"
    inputs.extend([seccm_zip, edx_zip])
    if xps_zip.exists():
        inputs.append(xps_zip)
    seccm = load_seccm_archives(
        seccm_zip,
        edx_zip,
        xps_zip if xps_zip.exists() else None,
    )
    seccm_by_program: dict[str, list[CatalystSample]] = {}
    for sample in seccm:
        seccm_by_program.setdefault(sample.program, []).append(sample)
    suites["seccm_her"] = [
        Programme("seccm_her", name, samples, configs["seccm"], rich_epochs)
        for name, samples in sorted(seccm_by_program.items())
    ]

    specgen = load_specgen_archive(SPECGEN_PATH)
    specgen_by_program: dict[str, list[CatalystSample]] = {}
    for sample in specgen:
        specgen_by_program.setdefault(sample.program, []).append(sample)
    suites["specgen"] = [
        Programme("specgen", name, samples, configs["rich"], rich_epochs)
        for name, samples in sorted(specgen_by_program.items())
    ]
    return suites, inputs


def _condition_fraction(samples: list[CatalystSample]) -> float:
    return float(np.mean([np.mean(sample.condition_mask > 0) for sample in samples]))


def build_edges(suites: dict[str, list[Programme]]) -> list[dict[str, Any]]:
    device = torch.device("cpu")
    rows = []
    for suite, programmes in suites.items():
        print(f"\n{suite}: {len(programmes)} programmes", flush=True)
        for donor in programmes:
            print(
                f"Training donor {suite}:{donor.name} (n={len(donor.samples)})",
                flush=True,
            )
            training = TrainingConfig(
                seed=SEED,
                epochs=donor.epochs,
                patience=20,
                batch_size=32,
                learning_rate=8e-4,
                rank_weight=0.15,
                nll_weight=0.10,
            )
            pair = train_expert_pair(
                donor.samples,
                donor.model_config,
                training,
                device=device,
            )
            source_validation = float(
                pair.standard_report["validation_metrics"]["spearman"]
            )
            router = ExpertRouter(
                pair.standard,
                pair.mhar,
                pair.standard_calibrator,
                pair.mhar_calibrator,
                strategy="domain_preferring",
            )
            for recipient in programmes:
                if recipient.name == donor.name:
                    continue
                diagnostics = router.route(
                    recipient.samples,
                    pair.normalizer,
                    device=device,
                )
                geometry = edge_geometry(donor.samples, recipient.samples)
                state = RouterState.from_mapping(
                    {
                        "task_kind": "catalyst_ranking",
                        "source_sample_count": len(donor.samples),
                        "target_candidate_count": len(recipient.samples),
                        "source_validation_spearman": source_validation,
                        "curve_available": bool(donor.model_config.use_curve),
                        "surface_available": bool(donor.model_config.use_surface),
                        "condition_observed_fraction": _condition_fraction(
                            recipient.samples
                        ),
                        "standard_predictive_std": float(
                            np.mean(diagnostics.standard_std)
                        ),
                        "mhar_predictive_std": float(np.mean(diagnostics.mhar_std)),
                        "normalized_expert_disagreement": float(
                            np.mean(diagnostics.disagreement)
                        ),
                        "standard_domain_share": float(
                            np.mean(1.0 - diagnostics.domain_distance_ratio)
                        ),
                        "composition_support": float(geometry["coverage"]),
                    }
                )
                truth = targets_array(recipient.samples)
                standard_rho = metrics(truth, diagnostics.standard_mean)["spearman"]
                mhar_rho = metrics(truth, diagnostics.mhar_mean)["spearman"]
                ensemble_mean = (
                    diagnostics.standard_mean + diagnostics.mhar_mean
                ) / 2.0
                ensemble_rho = metrics(truth, ensemble_mean)["spearman"]
                realized = {
                    "standard_spearman": float(standard_rho),
                    "mhar_spearman": float(mhar_rho),
                    "ensemble_spearman": float(ensemble_rho),
                }
                example_id = f"{suite}:{donor.name}→{recipient.name}"
                rows.append(
                    {
                        "example_id": example_id,
                        "suite": suite,
                        "donor_group": f"{suite}:{donor.name}",
                        "recipient_group": f"{suite}:{recipient.name}",
                        "state": state.__dict__,
                        "evaluation": realized,
                    }
                )
                print(
                    f"  → {recipient.name:20s} "
                    f"std={standard_rho:+.3f} mhar={mhar_rho:+.3f} "
                    f"ens={ensemble_rho:+.3f}",
                    flush=True,
                )
    rows.sort(key=lambda row: row["example_id"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--alloy-epochs", type=int, default=100)
    parser.add_argument("--rich-epochs", type=int, default=40)
    args = parser.parse_args()

    if args.out.is_symlink():
        raise ValueError("output may not be a symlink")
    design = json.loads(args.design.read_text(encoding="utf-8"))
    set_deterministic(SEED)
    started = time.time()
    suites, input_paths = load_programmes(
        alloy_epochs=args.alloy_epochs,
        rich_epochs=args.rich_epochs,
    )
    observed_counts = {
        suite: len(programmes) * (len(programmes) - 1)
        for suite, programmes in suites.items()
    }
    if observed_counts != design["edge_inventory"]["suites"]:
        raise RuntimeError(
            f"edge inventory drift: expected={design['edge_inventory']['suites']}, "
            f"observed={observed_counts}"
        )
    edge_rows = build_edges(suites)
    expected_edges = int(design["edge_inventory"]["expected_total_edges"])
    if len(edge_rows) != expected_edges:
        raise RuntimeError(f"expected {expected_edges} edges, got {len(edge_rows)}")
    edges = [NumericRouterEdge.from_mapping(row) for row in edge_rows]
    alpha_grid = tuple(float(value) for value in design["learner"]["alpha_grid"])

    primary = nested_group_predictions(
        edges,
        outer_group=lambda edge: edge.suite,
        inner_group=lambda edge: edge.suite,
        alpha_grid=alpha_grid,
    )
    primary_summary = summarize_predictions(primary, edges)
    secondary = nested_group_predictions(
        edges,
        outer_group=lambda edge: edge.donor_group,
        inner_group=lambda edge: edge.donor_group,
        alpha_grid=alpha_grid,
    )
    secondary_summary = summarize_predictions(secondary, edges)
    both_passed = bool(
        primary_summary["qualification_gate"]["passed"]
        and secondary_summary["qualification_gate"]["passed"]
    )

    report = {
        "design_version": design["design_version"],
        "design": _manifest(args.design),
        "status": (
            "retrospective-screen-passed-await-sealed-programme"
            if both_passed
            else "retrospective-screen-failed"
        ),
        "scientific_effect_verified": False,
        "promotion_allowed": False,
        "seed": SEED,
        "wall_time_seconds": round(time.time() - started, 1),
        "inputs": [_manifest(path) for path in input_paths],
        "edge_inventory": {
            "total": len(edges),
            "suites": observed_counts,
            "unique_donor_programmes": len({edge.donor_group for edge in edges}),
            "target_outcomes_in_features": False,
            "programme_identity_in_features": False,
        },
        "edges": edge_rows,
        "primary_leave_one_suite_out": {
            "summary": primary_summary,
            "folds": primary["folds"],
            "rows": primary["rows"],
        },
        "secondary_leave_one_donor_out": {
            "summary": secondary_summary,
            "folds": secondary["folds"],
            "rows": secondary["rows"],
        },
        "qualification_gate_passed_both_splits": both_passed,
        "decision": {
            "freeze_for_sealed_external_programme": both_passed,
            "replace_existing_expert_or_router": False,
            "reason": (
                "A retrospective pass can only justify a future sealed test."
                if both_passed
                else "The numeric RouterState signal did not satisfy every frozen robustness gate."
            ),
        },
    }
    _write_json(args.out, report)
    print("\nPrimary LOSO:", json.dumps(primary_summary, indent=2), flush=True)
    print("\nSecondary LODO:", json.dumps(secondary_summary, indent=2), flush=True)
    print(f"\nWrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
