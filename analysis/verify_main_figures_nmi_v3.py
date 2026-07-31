"""Semantic and artifact verification for the NMI-v3 main-figure set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "analysis" / "figures"
SOURCE = FIGURES / "source_data"
RESULTS = ROOT / "analysis" / "results"
OUT = RESULTS / "main_figures_nmi_v3_VERIFIED.json"


def close(actual: float, expected: float, atol: float = 1e-10) -> None:
    if not np.isclose(float(actual), float(expected), rtol=0, atol=atol):
        raise AssertionError(f"numeric mismatch: {actual} != {expected}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_exports() -> dict[str, dict[str, object]]:
    stems = [
        "figure2_failure_benchmark_nmi_v3",
        "figure3_relation_transfer_nmi_v3",
        "figure4_ordinal_screening_nmi_v3",
    ]
    exports: dict[str, dict[str, object]] = {}
    for stem in stems:
        exports[stem] = {}
        for suffix in [".pdf", ".svg", ".png", ".tiff"]:
            path = FIGURES / f"{stem}{suffix}"
            if not path.exists() or path.stat().st_size < 1000:
                raise AssertionError(f"missing or undersized export: {path}")
            exports[stem][suffix] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    return exports


def verify_figure2() -> dict[str, object]:
    frame = pd.read_csv(SOURCE / "figure2_failure_benchmark_nmi_v3.csv")
    panel_a = frame[frame["panel"].eq("a")].set_index("measure")["estimate"]
    close(panel_a["source_internal_r2"], 0.789886969692373)
    close(panel_a["recipient_internal_r2"], 0.06703546705476726)
    close(panel_a["transported_r2"], -3.0061494752292957)
    panel_b = frame[frame["panel"].eq("b")]
    if len(panel_b) != 40 or int(panel_b["is_designated_primary"].sum()) != 8:
        raise AssertionError("Figure 2b edge count changed")
    panel_c = frame[frame["panel"].eq("c")]
    complete_passes = int(panel_c.groupby("target")["pass"].all().sum())
    if complete_passes != 0:
        raise AssertionError("Figure 2c no longer rejects every declared edge")
    return {"real_edges": len(panel_b), "declared_edges": 8,
            "complete_passes": complete_passes}


def verify_figure3() -> dict[str, object]:
    metrics = json.loads((RESULTS / "figure3_relation_transfer_nmi_v3_metrics.json")
                         .read_text(encoding="utf-8"))
    close(metrics["raw_r2"], 0.6294395421521868)
    close(metrics["log_r2"], 0.731524435225858)
    close(metrics["spearman"], 0.8708256451064949)
    if int(metrics["n"]) != 1827:
        raise AssertionError("Figure 3 external row count changed")
    frame = pd.read_csv(SOURCE / "figure3_relation_transfer_nmi_v3.csv")
    panel_c = frame[(frame["panel"].eq("c")) & frame["comparator"].notna()]
    if set(panel_c["comparator"]) != {
        "state_only", "chemistry_permuted", "without_LiPF6", "LiPF6_only",
        "LiBOB_wrong_salt_control", "LiBF4_fluorinated_control",
    }:
        raise AssertionError("Figure 3c comparator set changed")
    panel_d = frame[frame["panel_source"].eq("d")]
    expected_rmse = {"A": .0319129678506787, "B": .1634879441228944,
                     "C": -.1037710009360328, "D": .260734871957417}
    for target, expected in expected_rmse.items():
        row = panel_d[(panel_d["target"].eq(target)) &
                      (panel_d["measure"].eq("relative_rmse_gain"))]
        if len(row) != 1:
            raise AssertionError(f"Figure 3d missing target {target}")
        close(row.iloc[0]["estimate"], expected, atol=1e-12)
    return {"external_rows": int(metrics["n"]), "comparators": len(panel_c),
            "controlled_targets": 4}


def verify_figure4() -> dict[str, object]:
    frame = pd.read_csv(SOURCE / "figure4_ordinal_screening_nmi_v3.csv")
    panel_b = frame[frame["panel"].eq("b")]
    if len(panel_b) != 15:
        raise AssertionError("Figure 4b model count changed")
    source = panel_b[panel_b["model"].eq("programme_balanced_source_portfolio")]
    best = panel_b[panel_b["model"].eq("rbf_kernel_ridge_alpha_10")]
    close(source.iloc[0]["estimate"], 0.910299826143778)
    close(best.iloc[0]["estimate"], 0.5366383640583346)
    panel_d = frame[frame["panel"].eq("d")].set_index("programme")
    close(panel_d.loc["SolventSeg", "estimate"], 0.3736614620854431)
    close(panel_d.loc["SolventSeg", "ci95_low"], 0.21257687374893036)
    close(panel_d.loc["SolventSeg", "ci95_high"], 0.5622189765440571)
    close(panel_d.loc["FINALES", "estimate"], -0.08873114463176579)
    close(panel_d.loc["FINALES", "ci95_low"], -0.2932013494453841)
    close(panel_d.loc["FINALES", "ci95_high"], 0.095926068941845)
    if panel_d.loc["SolventSeg", "decision"] != "screen":
        raise AssertionError("Primary ordinal route changed")
    if panel_d.loc["FINALES", "decision"] != "abstain":
        raise AssertionError("Frozen second-recipient route changed")
    return {"models": len(panel_b), "primary_delta": panel_d.loc["SolventSeg", "estimate"],
            "frozen_delta": panel_d.loc["FINALES", "estimate"]}


def main() -> None:
    report = {
        "status": "verified-complete",
        "figure2": verify_figure2(),
        "figure3": verify_figure3(),
        "figure4": verify_figure4(),
        "exports": require_exports(),
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
