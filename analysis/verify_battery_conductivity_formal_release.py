"""Verify the frozen numeric release without changing its row set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "battery_conductivity_borrowing_design.json"
IMPLEMENTATION = HERE / "battery_conductivity_implementation.json"
AUDIT = HERE / "results" / "battery_conductivity_preoutcome_audit.json"
RELEASE = HERE / "results" / "battery_conductivity_formal_release.csv"
MANIFEST = (
    HERE / "results" / "battery_conductivity_formal_release_manifest.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    frame = pd.read_csv(RELEASE, low_memory=False)
    if manifest["design_sha256"] != sha256(DESIGN):
        raise AssertionError("Design hash changed after numeric release")
    if manifest["implementation_sha256"] != sha256(IMPLEMENTATION):
        raise AssertionError("Implementation hash changed after release")
    if manifest["preoutcome_audit_sha256"] != sha256(AUDIT):
        raise AssertionError("Pre-outcome audit changed after release")
    if manifest["release_sha256"] != sha256(RELEASE):
        raise AssertionError("Formal release hash mismatch")
    if len(frame) != manifest["release_rows"]:
        raise AssertionError("Formal release row count mismatch")
    if frame["record_id"].duplicated().any():
        raise AssertionError("Formal release record IDs are not unique")
    if not np.isfinite(frame["normalized_value"]).all():
        raise AssertionError("Formal release contains nonfinite outcomes")
    if (frame["doi_normalized"].astype(str).str.len() == 0).any():
        raise AssertionError("Formal release contains missing DOI")
    if (frame["material_normalized"].astype(str).str.len() == 0).any():
        raise AssertionError("Formal release contains missing material")

    target = frame.loc[frame["property_class"].eq("capacity")]
    donor = frame.loc[frame["property_class"].eq("conductivity")]
    if len(target) < 300 or target["doi_normalized"].nunique() < 30:
        raise AssertionError("Released target is below the frozen gate")
    if len(donor) < 500 or donor["doi_normalized"].nunique() < 50:
        raise AssertionError("Released donor is below the frozen gate")

    output = {
        "status": "verified-formal-release",
        "design_sha256": manifest["design_sha256"],
        "implementation_sha256": manifest["implementation_sha256"],
        "release_sha256": manifest["release_sha256"],
        "release_rows": len(frame),
        "target_rows": len(target),
        "donor_rows": len(donor),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

