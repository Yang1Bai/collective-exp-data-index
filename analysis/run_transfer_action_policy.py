#!/usr/bin/env python3
"""Generate current transfer-action and synthesis-route-readiness artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from build_transferability_evidence_cards import build_cards
from transfer_action_policy import build_policy_summary


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"


def main() -> None:
    readiness = json.loads(
        (ROOT / "analysis" / "xrd_to_synthesis_readiness.json").read_text(
            encoding="utf-8"
        )
    )
    summary = build_policy_summary(build_cards(), readiness)
    json_path = RESULTS / "transfer_action_policy_summary.json"
    json_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    csv_path = RESULTS / "transfer_action_policy_actions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "recipient",
                "action",
                "endpoint",
                "synthesis_route_selection",
                "bridge_status",
                "reason_codes",
            ),
            lineterminator="\n",
        )
        writer.writeheader()
        for row in summary["transfer_actions"]:
            writer.writerow(
                {**row, "reason_codes": ";".join(row["reason_codes"])}
            )

    readiness_csv = RESULTS / "synthesis_route_readiness_checklist.csv"
    with readiness_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("requirement", "status"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary["synthesis_route_readiness"]["checklist"])

    for path in (json_path, csv_path, readiness_csv):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
