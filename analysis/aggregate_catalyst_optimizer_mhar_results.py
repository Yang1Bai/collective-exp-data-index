"""Validate and aggregate the catalyst optimizer/MHAR experiment series."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from catalyst_attention.data import atomic_write_text


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_OUTPUT = (
    HERE / "results/catalyst_optimizer_mhar_summary.json"
)
RESULT_PATHS = {
    "initial_screening": (
        HERE / "results/catalyst_optimizer_mhar_screening.json"
    ),
    "refinement_screening": (
        HERE
        / "results/catalyst_optimizer_mhar_refinement_screening.json"
    ),
    "mhar_confirmation": (
        HERE / "results/catalyst_optimizer_mhar_confirmation.json"
    ),
    "standard_ocx24_confirmation": (
        HERE
        / "results/"
        "catalyst_optimizer_mhar_standard_ocx24_confirmation.json"
    ),
    "domain_alignment_screening": (
        HERE / "results/catalyst_mhar_domain_alignment_screening.json"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def load_result(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "complete":
        raise ValueError(f"incomplete result: {path}")
    design_path = ROOT / result["design_path"]
    if sha256(design_path) != result["design_sha256"]:
        raise ValueError(f"design hash mismatch: {path}")
    for dataset in result["datasets"].values():
        gate = dataset.get("gate")
        if not isinstance(gate, dict) or "passed" not in gate:
            raise ValueError(f"missing formal gate: {path}")
    return result


def candidate_row(result: dict, name: str) -> dict:
    return result["screening_selection"]["candidates"][name]


def ocx_spearman(result: dict, name: str) -> dict[str, float]:
    return {
        direction: float(
            row["models"][name]["ensemble"]["target"]["spearman"]
        )
        for direction, row in result["datasets"]["ocx24"][
            "directions"
        ].items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    loaded = {
        name: load_result(path)
        for name, path in RESULT_PATHS.items()
    }
    initial = loaded["initial_screening"]
    refinement = loaded["refinement_screening"]
    confirmation = loaded["mhar_confirmation"]
    standard_ocx = loaded["standard_ocx24_confirmation"]
    alignment = loaded["domain_alignment_screening"]

    artifact_manifest = {
        name: {
            "path": repository_path(RESULT_PATHS[name]),
            "sha256": sha256(RESULT_PATHS[name]),
            "design_path": result["design_path"],
            "design_sha256": result["design_sha256"],
            "stage": result["stage"],
            "seeds": result["seeds"],
        }
        for name, result in loaded.items()
    }
    mhar_spec_gate = confirmation["datasets"]["specgen"]["gate"]
    mhar_ocx_gate = confirmation["datasets"]["ocx24"]["gate"]
    standard_alignment_gate = alignment["datasets"]["specgen"][
        "gate"
    ]["candidates"]["standard_coral_adamw"]

    mhar_ocx = ocx_spearman(
        confirmation, "sublayer_delta_mhar_adamw"
    )
    standard_ocx_values = ocx_spearman(
        standard_ocx, "standard_adamw"
    )
    summary = {
        "status": "complete",
        "evidence_boundary": (
            "Retrospective method development on already inspected "
            "recipient programmes. No result is prospective evidence, "
            "and post-outcome expert routing is not promotion eligible."
        ),
        "artifact_manifest": artifact_manifest,
        "optimizer_findings": {
            "ungrafted_kl_shampoo": {
                "standard_median_transfer_gain": candidate_row(
                    initial, "standard_kl_shampoo"
                )["median_transfer_gain"],
                "mhar_median_transfer_gain": candidate_row(
                    initial, "delta_mhar_kl_shampoo"
                )["median_transfer_gain"],
                "standard_median_source_validation_spearman": (
                    candidate_row(initial, "standard_kl_shampoo")[
                        "median_source_validation_spearman"
                    ]
                ),
                "decision": "reject",
            },
            "adam_step_norm_grafted_kl_shampoo": {
                "standard_median_transfer_gain": candidate_row(
                    refinement, "standard_kl_shampoo_grafted"
                )["median_transfer_gain"],
                "mhar_median_transfer_gain": candidate_row(
                    refinement,
                    "sublayer_delta_mhar_kl_shampoo_grafted",
                )["median_transfer_gain"],
                "standard_median_source_validation_spearman": (
                    candidate_row(
                        refinement, "standard_kl_shampoo_grafted"
                    )["median_source_validation_spearman"]
                ),
                "decision": "reject-for-transfer",
            },
        },
        "mhar_confirmation": {
            "specgen": mhar_spec_gate,
            "ocx24": mhar_ocx_gate,
            "overall_median_transfer_gain": candidate_row(
                confirmation, "sublayer_delta_mhar_adamw"
            )["median_transfer_gain"],
            "decision": "retain-as-specialist-not-default",
        },
        "domain_alignment_screening": {
            "standard_coral_specgen": standard_alignment_gate,
            "standard_coral_ocx24": alignment["datasets"]["ocx24"][
                "gate"
            ]["candidates"]["standard_coral_adamw"],
            "mhar_coral_specgen": alignment["datasets"]["specgen"][
                "gate"
            ]["candidates"]["sublayer_delta_mhar_coral_adamw"],
            "mhar_coral_ocx24": alignment["datasets"]["ocx24"][
                "gate"
            ]["candidates"]["sublayer_delta_mhar_coral_adamw"],
            "decision": "reject-as-universal-transfer-method",
        },
        "ocx24_complementarity_diagnostic": {
            "standard_adamw": standard_ocx_values,
            "sublayer_delta_mhar_adamw": mhar_ocx,
            "best_per_direction_post_outcome": {
                direction: max(standard_value, mhar_ocx[direction])
                for direction, standard_value in (
                    standard_ocx_values.items()
                )
            },
            "claim_boundary": (
                "Diagnostic only. The expert choice was observed after "
                "recipient outcomes and must be frozen before testing on "
                "a new programme."
            ),
        },
        "promotion_decision": {
            "passed_all_frozen_dataset_gates": False,
            "new_universal_default": None,
            "current_default": "hierarchical_cross_attention_v1",
            "research_specialist": "sublayer_delta_mhar_adamw",
            "next_confirmatory_candidate": (
                "target-label-free standard/MHAR expert router"
            ),
        },
    }
    atomic_write_text(
        args.output,
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
