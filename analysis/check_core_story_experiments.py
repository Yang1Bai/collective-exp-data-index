"""Validate the machine-readable experiment gate for the paper's core claim."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "analysis" / "core_story_experiment_registry.json"
ALLOWED_STATUSES = {
    "complete",
    "complete-boundary",
    "method-development-complete",
    "partial",
    "planned-frozen",
    "preoutcome-frozen",
    "missing",
}
REQUIRED_FIELDS = {
    "id",
    "name",
    "paper_submission_required",
    "status",
    "design_paths",
    "evidence_paths",
    "primary_endpoints",
    "required_controls",
    "compute",
}


def validate_registry(require_complete: bool = False) -> dict:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    accepted = set(payload["accepted_complete_statuses"])
    experiments = payload["experiments"]
    errors: list[str] = []
    blockers: list[dict[str, str]] = []
    seen: set[str] = set()

    for experiment in experiments:
        missing_fields = REQUIRED_FIELDS - set(experiment)
        if missing_fields:
            errors.append(
                f"{experiment.get('id', '<unknown>')}: missing fields "
                f"{sorted(missing_fields)}"
            )
            continue
        experiment_id = experiment["id"]
        if experiment_id in seen:
            errors.append(f"duplicate experiment id: {experiment_id}")
        seen.add(experiment_id)
        status = experiment["status"]
        if status not in ALLOWED_STATUSES:
            errors.append(f"{experiment_id}: invalid status {status!r}")

        for design_path in experiment["design_paths"]:
            if not (ROOT / design_path).is_file():
                errors.append(f"{experiment_id}: missing design {design_path}")

        if status in accepted:
            if not experiment["evidence_paths"]:
                errors.append(f"{experiment_id}: complete status without evidence")
            for evidence_path in experiment["evidence_paths"]:
                if not (ROOT / evidence_path).is_file():
                    errors.append(f"{experiment_id}: missing evidence {evidence_path}")

        if experiment["paper_submission_required"] and status not in accepted:
            blockers.append(
                {
                    "id": experiment_id,
                    "name": experiment["name"],
                    "status": status,
                }
            )

    if require_complete and blockers:
        errors.append(
            "paper submission gate is open: "
            + ", ".join(f"{b['id']}={b['status']}" for b in blockers)
        )

    return {
        "status": "valid" if not errors else "invalid",
        "registry": str(REGISTRY.relative_to(ROOT)),
        "experiments": len(experiments),
        "submission_blockers": blockers,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail until every paper-submission experiment is complete.",
    )
    args = parser.parse_args()
    result = validate_registry(require_complete=args.require_complete)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "valid" else 1)


if __name__ == "__main__":
    main()
