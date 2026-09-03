"""Freeze target-label draws using OPV metadata only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
METADATA_PATH = (
    HERE / "results" / "opv_optical_target_metadata_no_outcomes.csv"
)
DRAW_PATH = HERE / "results" / "opv_optical_label_draws.csv"
MANIFEST_PATH = HERE / "results" / "opv_optical_label_draws_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if sha256(METADATA_PATH) != design["outcome_free_audit"][
        "metadata_sha256"
    ]:
        raise RuntimeError("Outcome-free OPV metadata changed")
    metadata = pd.read_csv(METADATA_PATH, low_memory=False)
    development = metadata.loc[~metadata["external_doi_holdout"]].copy()
    representatives = (
        development.assign(
            representative_order=development["id"].astype(str).map(stable)
        )
        .sort_values(["doi_pair_key", "representative_order"])
        .drop_duplicates("doi_pair_key")
        .reset_index(drop=True)
    )
    budgets = [
        int(value) for value in design["split_and_ood"]["label_budgets"]
    ]
    repeats = int(design["split_and_ood"]["repeats"])
    rows = []
    for budget in budgets:
        if budget > len(representatives):
            raise RuntimeError("Label budget exceeds candidate units")
        for repeat in range(repeats):
            seed = 2026072700 + budget * 1000 + repeat
            rng = np.random.default_rng(seed)
            chosen = rng.choice(len(representatives), budget, replace=False)
            for rank, row_index in enumerate(chosen):
                row = representatives.iloc[int(row_index)]
                rows.append(
                    {
                        "budget": budget,
                        "repeat": repeat,
                        "seed": seed,
                        "draw_rank": rank,
                        "id": str(row["id"]),
                        "doi_normalized_audit": str(
                            row["doi_normalized_audit"]
                        ),
                        "doi_pair_key": str(row["doi_pair_key"]),
                    }
                )
    draws = pd.DataFrame(rows).sort_values(
        ["budget", "repeat", "draw_rank"]
    )
    if draws["id"].isin(
        set(
            metadata.loc[
                metadata["external_doi_holdout"], "id"
            ].astype(str)
        )
    ).any():
        raise AssertionError("External DOI entered a label draw")
    counts = draws.groupby(["budget", "repeat"])["id"].nunique()
    for (budget, _), count in counts.items():
        if int(count) != int(budget):
            raise AssertionError("Draw size or uniqueness drift")
    DRAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    draws.to_csv(DRAW_PATH, index=False, lineterminator="\n")
    manifest = {
        "status": "outcome-free-label-draws-frozen",
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "metadata_sha256": sha256(METADATA_PATH),
        "implementation_sha256": sha256(Path(__file__)),
        "draw_sha256": sha256(DRAW_PATH),
        "budgets": budgets,
        "repeats": repeats,
        "rows": int(len(draws)),
        "development_candidate_units": int(len(representatives)),
        "outcome_access": "No OPV outcome or target energy annotation was read.",
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
