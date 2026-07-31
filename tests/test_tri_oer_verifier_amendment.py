import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.verify_tri_oer_neighbor_results_amended import audit_metric_finiteness

ROOT = Path(__file__).resolve().parents[1]


def _metrics():
    return pd.DataFrame(
        {
            "plate": ["3496", "3496"],
            "method": ["target_only", "source_only_calibrated"],
            "learner": ["extra_trees", "ridge"],
            "representation": ["element_fraction", "element_fraction"],
            "scope": ["dynamic_ood_q4", "dynamic_ood_q4"],
            "rmse": [0.1, 0.2],
            "mae": [0.08, 0.15],
            "r2": [0.4, -0.1],
            "spearman": [0.3, np.nan],
        }
    )


def test_undefined_secondary_spearman_is_counted_not_relabelled():
    audit = audit_metric_finiteness(_metrics())
    assert audit["undefined_spearman_cells"] == 1
    assert audit["undefined_spearman_groups"][0]["method"] == "source_only_calibrated"


def test_nonfinite_primary_metric_still_fails():
    metrics = _metrics()
    metrics.loc[0, "rmse"] = np.nan
    with pytest.raises(AssertionError, match="primary or absolute-utility"):
        audit_metric_finiteness(metrics)


def test_infinite_spearman_still_fails():
    metrics = _metrics()
    metrics.loc[0, "spearman"] = np.inf
    with pytest.raises(AssertionError, match="Infinite TRI Spearman"):
        audit_metric_finiteness(metrics)


def test_amended_verifier_can_start_as_a_direct_script():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "analysis" / "verify_tri_oer_neighbor_results_amended.py"),
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--portable" in result.stdout
