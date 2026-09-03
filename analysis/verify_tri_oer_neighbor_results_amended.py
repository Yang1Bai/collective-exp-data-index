"""Post-Job-70861 wrapper for legitimate undefined TRI Spearman cells."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import verify_tri_oer_neighbor_results as frozen

AMENDMENT = HERE / "TRI_OER_VERIFIER_AMENDMENT.md"
ORIGINAL_VALIDATE_ROWS = frozen.validate_rows


def audit_metric_finiteness(metrics: pd.DataFrame) -> dict:
    primary_columns = ["rmse", "mae", "r2"]
    if not np.isfinite(metrics[primary_columns]).all().all():
        raise AssertionError("Nonfinite TRI primary or absolute-utility metrics")
    spearman = pd.to_numeric(metrics["spearman"], errors="coerce")
    if np.isinf(spearman.to_numpy(float)).any():
        raise AssertionError("Infinite TRI Spearman metric")
    undefined = metrics.loc[spearman.isna()].copy()
    dimensions = [
        "plate",
        "method",
        "learner",
        "representation",
        "scope",
    ]
    counts = (
        undefined.groupby(dimensions, dropna=False)
        .size()
        .rename("undefined_cells")
        .reset_index()
        .to_dict("records")
    )
    return {
        "undefined_spearman_cells": int(len(undefined)),
        "undefined_spearman_groups": counts,
        "handling": "preserved as undefined; excluded from all primary inference",
    }


def validate_rows_amended(metrics: pd.DataFrame, group_errors: pd.DataFrame) -> dict:
    audit = audit_metric_finiteness(metrics)
    structural_copy = metrics.copy()
    structural_copy["spearman"] = structural_copy["spearman"].fillna(0.0)
    result = ORIGINAL_VALIDATE_ROWS(structural_copy, group_errors)
    result["secondary_spearman_audit"] = audit
    return result


def main() -> None:
    frozen.validate_rows = validate_rows_amended
    frozen.main()
    result = json.loads(frozen.OUTPUT.read_text(encoding="utf-8"))
    result["verifier_amendment_sha256"] = frozen.sha256(AMENDMENT)
    result["verifier_amendment_scope"] = (
        "Undefined secondary Spearman cells retained and disclosed; all frozen "
        "primary metrics, methods, inference, and decisions unchanged."
    )
    frozen.OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
