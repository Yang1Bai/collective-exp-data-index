"""Isosteric adsorption compensation analysis with a Krug artifact gate.

The design and inclusion rules are frozen in ``ISODB_ISOSTERIC_SPEC.md``.
The pinned archive is streamed rather than extracted because one historical
ISODB path contains characters that Windows cannot materialize.
"""
from __future__ import annotations

import hashlib
import json
import math
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import stats

from common import RESULTS, ensure_output_dirs, hc3_regression, holm_adjust

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOCK_PATH = ROOT / "scripts" / "localdb" / "sources.lock.json"
CACHE = Path.home() / ".collective_data_cache"
R_GAS = 8.31446261815324
SEED = 20260714
PRIMARY_FRACTION = 0.50
PRIMARY_R2 = 0.90
PRIMARY_SPAN = 20.0
N_BOOT = 2000
N_NULL = 1000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_archive() -> tuple[Path, dict[str, Any]]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))["sources"]["nist-isodb"]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / lock["archive_filename"]
    if not path.exists():
        request = urllib.request.Request(lock["archive_url"], headers={"User-Agent": "collective-exp-data-index/0.3"})
        with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    observed = sha256(path).lower()
    expected = lock["archive_sha256"].lower()
    if observed != expected:
        raise RuntimeError(f"ISODB archive hash mismatch: {observed} != {expected}")
    return path, lock


def clean_curve(document: dict[str, Any]) -> dict[str, Any] | None:
    adsorbates = document.get("adsorbates") or []
    if len(adsorbates) != 1 or str(document.get("pressureUnits", "")).strip().lower() != "bar":
        return None
    try:
        temperature = float(document.get("temperature"))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(temperature) or temperature <= 0:
        return None
    points = []
    for item in document.get("isotherm_data") or []:
        try:
            pressure = float(item.get("pressure"))
            uptake_value = item.get("total_adsorption")
            if uptake_value is None:
                species = item.get("species_data") or []
                uptake_value = species[0].get("adsorption") if len(species) == 1 else None
            uptake = float(uptake_value)
        except (TypeError, ValueError, IndexError):
            continue
        if pressure > 0 and uptake > 0 and math.isfinite(pressure) and math.isfinite(uptake):
            points.append((uptake, pressure))
    if len(points) < 5:
        return None
    frame = pd.DataFrame(points, columns=["uptake", "pressure"])
    frame = frame.groupby("uptake", as_index=False)["pressure"].median().sort_values("uptake")
    if len(frame) < 5:
        return None
    if frame["uptake"].nunique() < 2 or frame["pressure"].nunique() < 2:
        return None
    monotonic = stats.spearmanr(frame["uptake"], frame["pressure"]).statistic
    if not np.isfinite(monotonic) or monotonic < 0.90:
        return None
    adsorbent = document.get("adsorbent") or {}
    adsorbate = adsorbates[0]
    doi = str(document.get("DOI", "")).strip().lower()
    adsorbent_id = str(adsorbent.get("hashkey") or adsorbent.get("name") or "unknown")
    adsorbate_id = str(adsorbate.get("InChIKey") or adsorbate.get("name") or "unknown")
    adsorption_unit = str(document.get("adsorptionUnits", "")).strip()
    return {
        "key": (doi, adsorbent_id, adsorbate_id, adsorption_unit, "bar"),
        "doi": doi,
        "adsorbent_id": adsorbent_id,
        "adsorbent_name": str(adsorbent.get("name") or adsorbent_id),
        "adsorbate_id": adsorbate_id,
        "adsorbate_name": str(adsorbate.get("name") or adsorbate_id),
        "adsorption_unit": adsorption_unit,
        "temperature": temperature,
        "log_uptake": np.log(frame["uptake"].to_numpy(float)),
        "log_pressure": np.log(frame["pressure"].to_numpy(float)),
        "n_points": len(frame),
        "monotonic_spearman": float(monotonic),
    }


def load_systems(archive: Path) -> tuple[dict[tuple[str, ...], list[dict[str, Any]]], dict[str, int]]:
    systems: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    counts = defaultdict(int)
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            if not member.isfile() or not member.name.lower().endswith(".json"):
                continue
            counts["json_files"] += 1
            try:
                stream = handle.extractfile(member)
                if stream is None:
                    continue
                document = json.load(stream)
            except (json.JSONDecodeError, UnicodeDecodeError):
                counts["json_parse_failures"] += 1
                continue
            curve = clean_curve(document)
            if curve is None:
                counts["ineligible_isotherms"] += 1
                continue
            systems[curve["key"]].append(curve)
            counts["eligible_isotherms"] += 1
    return dict(systems), dict(counts)


def fit_system(curves: list[dict[str, Any]], fraction: float) -> dict[str, Any] | None:
    temperatures = sorted({curve["temperature"] for curve in curves})
    if len(temperatures) < 3 or max(temperatures) - min(temperatures) < PRIMARY_SPAN:
        return None
    lower = max(float(curve["log_uptake"].min()) for curve in curves)
    upper = min(float(curve["log_uptake"].max()) for curve in curves)
    if not np.isfinite(lower + upper) or upper <= lower:
        return None
    target_log_uptake = lower + fraction * (upper - lower)
    by_temperature: dict[float, list[float]] = defaultdict(list)
    for curve in curves:
        pressure = float(np.interp(target_log_uptake, curve["log_uptake"], curve["log_pressure"]))
        by_temperature[curve["temperature"]].append(pressure)
    temperature = np.asarray(sorted(by_temperature), dtype=float)
    log_pressure = np.asarray([np.median(by_temperature[value]) for value in temperature], dtype=float)
    if len(temperature) < 3:
        return None
    x = 1.0 / temperature
    slope, intercept = np.polyfit(x, log_pressure, 1)
    prediction = intercept + slope * x
    residual = log_pressure - prediction
    denominator = np.sum((log_pressure - log_pressure.mean()) ** 2)
    r2 = 1 - np.sum(residual**2) / denominator if denominator > 0 else np.nan
    qst = -slope * R_GAS / 1000.0
    first = curves[0]
    system_text = "||".join(first["key"])
    return {
        "system_id": hashlib.sha256(system_text.encode("utf-8")).hexdigest()[:20],
        "doi": first["doi"],
        "adsorbent_id": first["adsorbent_id"],
        "adsorbent_name": first["adsorbent_name"],
        "adsorbate_id": first["adsorbate_id"],
        "adsorbate_name": first["adsorbate_name"],
        "adsorption_unit": first["adsorption_unit"],
        "uptake_log_fraction": fraction,
        "target_uptake": float(np.exp(target_log_uptake)),
        "n_temperatures": len(temperature),
        "n_isotherms": len(curves),
        "temperature_min_K": float(temperature.min()),
        "temperature_max_K": float(temperature.max()),
        "temperature_span_K": float(temperature.max() - temperature.min()),
        "temperature_harmonic_K": float(len(temperature) / np.sum(1 / temperature)),
        "Qst_kJ_mol": float(qst),
        "vanthoff_intercept": float(intercept),
        "vanthoff_slope": float(slope),
        "vanthoff_r2": float(r2),
        "residual_sd": float(np.sqrt(np.sum(residual**2) / max(1, len(temperature) - 2))),
        "temperatures_json": json.dumps(temperature.tolist(), separators=(",", ":")),
    }


def select_fits(fits: pd.DataFrame, r2_cutoff: float, span_cutoff: float) -> pd.DataFrame:
    return fits[
        (fits["uptake_log_fraction"] == PRIMARY_FRACTION)
        & (fits["vanthoff_r2"] >= r2_cutoff)
        & (fits["temperature_span_K"] >= span_cutoff)
        & (fits["Qst_kJ_mol"] > 0)
        & (fits["Qst_kJ_mol"] < 200)
    ].copy()


def regression_summary(frame: pd.DataFrame) -> dict[str, float]:
    result = hc3_regression(
        frame["Qst_kJ_mol"].to_numpy(float), frame["vanthoff_intercept"].to_numpy(float)
    )
    t_iso = 1000 / (R_GAS * result["slope"]) if result["slope"] > 0 else np.nan
    return {
        "n_systems": len(frame),
        "n_dois": frame["doi"].nunique(),
        **result,
        "T_iso_K": float(t_iso),
        "temperature_harmonic_median_K": float(frame["temperature_harmonic_K"].median()),
        "temperature_min_K": float(frame["temperature_min_K"].min()),
        "temperature_max_K": float(frame["temperature_max_K"].max()),
        "T_iso_relative_to_harmonic": float(t_iso / frame["temperature_harmonic_K"].median()),
    }


def doi_cluster_bootstrap(frame: pd.DataFrame, seed: int, n_boot: int) -> pd.DataFrame:
    grouped = {doi: group for doi, group in frame.groupby("doi")}
    dois = sorted(grouped)
    rng = np.random.default_rng(seed)
    rows = []
    for iteration in range(n_boot):
        selected = rng.choice(dois, size=len(dois), replace=True)
        pieces = []
        for cluster_index, doi in enumerate(selected):
            piece = grouped[doi].copy()
            piece["bootstrap_cluster"] = cluster_index
            pieces.append(piece)
        sample = pd.concat(pieces, ignore_index=True)
        if sample["Qst_kJ_mol"].nunique() < 3:
            continue
        x = sample["Qst_kJ_mol"].to_numpy(float)
        y = sample["vanthoff_intercept"].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1)
        prediction = intercept + slope * x
        r2 = 1 - np.sum((y - prediction) ** 2) / np.sum((y - y.mean()) ** 2)
        rows.append({
            "bootstrap": iteration,
            "slope": slope,
            "r2": r2,
            "T_iso_K": 1000 / (R_GAS * slope) if slope > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def krug_null(frame: pd.DataFrame, seed: int, n_null: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    q_true = frame["Qst_kJ_mol"].to_numpy(float)
    intercepts = frame["vanthoff_intercept"].to_numpy(float)
    residual_sd = frame["residual_sd"].to_numpy(float)
    temperature_grids = [np.asarray(json.loads(value), dtype=float) for value in frame["temperatures_json"]]
    rows = []
    for iteration in range(n_null):
        c_true = rng.permutation(intercepts)
        fitted_q = np.empty(len(frame), dtype=float)
        fitted_c = np.empty(len(frame), dtype=float)
        for index, temperature in enumerate(temperature_grids):
            log_pressure = c_true[index] - q_true[index] * 1000 / (R_GAS * temperature)
            if residual_sd[index] > 0:
                log_pressure = log_pressure + rng.normal(0, residual_sd[index], size=len(temperature))
            slope, fitted_c[index] = np.polyfit(1 / temperature, log_pressure, 1)
            fitted_q[index] = -slope * R_GAS / 1000
        slope, intercept = np.polyfit(fitted_q, fitted_c, 1)
        prediction = intercept + slope * fitted_q
        r2 = 1 - np.sum((fitted_c - prediction) ** 2) / np.sum((fitted_c - fitted_c.mean()) ** 2)
        rows.append({
            "simulation": iteration,
            "slope": slope,
            "r2": r2,
            "T_iso_K": 1000 / (R_GAS * slope) if slope > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def main() -> None:
    ensure_output_dirs()
    archive, lock = ensure_archive()
    print("Streaming pinned ISODB archive", flush=True)
    systems, ingestion_counts = load_systems(archive)
    print(f"Eligible curve groups: {len(systems)}", flush=True)
    fit_rows = []
    for fraction in (0.25, 0.50, 0.75):
        for curves in systems.values():
            result = fit_system(curves, fraction)
            if result is not None:
                fit_rows.append(result)
    fits = pd.DataFrame(fit_rows)
    fits.to_csv(RESULTS / "isodb_isosteric_all_fits.csv", index=False)

    sensitivity_rows = []
    for fraction in (0.25, 0.50, 0.75):
        fraction_fits = fits[fits["uptake_log_fraction"] == fraction]
        for r2_cutoff in (0.80, 0.90, 0.95):
            for span_cutoff in (20.0, 40.0, 60.0):
                selected = fraction_fits[
                    (fraction_fits["vanthoff_r2"] >= r2_cutoff)
                    & (fraction_fits["temperature_span_K"] >= span_cutoff)
                    & (fraction_fits["Qst_kJ_mol"] > 0)
                    & (fraction_fits["Qst_kJ_mol"] < 200)
                ]
                if len(selected) < 10:
                    continue
                row = regression_summary(selected)
                row.update({
                    "uptake_log_fraction": fraction,
                    "vanthoff_r2_cutoff": r2_cutoff,
                    "temperature_span_cutoff_K": span_cutoff,
                })
                sensitivity_rows.append(row)
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(RESULTS / "isodb_compensation_sensitivity.csv", index=False)

    primary = fits[
        (fits["uptake_log_fraction"] == PRIMARY_FRACTION)
        & (fits["vanthoff_r2"] >= PRIMARY_R2)
        & (fits["temperature_span_K"] >= PRIMARY_SPAN)
        & (fits["Qst_kJ_mol"] > 0)
        & (fits["Qst_kJ_mol"] < 200)
    ].copy()
    primary.to_csv(RESULTS / "isodb_isosteric_primary_fits.csv", index=False)
    observed = regression_summary(primary)
    print("DOI-cluster bootstrap", flush=True)
    bootstrap = doi_cluster_bootstrap(primary, SEED, N_BOOT)
    bootstrap.to_csv(RESULTS / "isodb_compensation_cluster_bootstrap.csv", index=False)

    family_rows = []
    for adsorbate, group in primary.groupby("adsorbate_name"):
        if len(group) < 8 or group["doi"].nunique() < 3:
            continue
        item = regression_summary(group)
        item["adsorbate_name"] = adsorbate
        family_rows.append(item)
    families = pd.DataFrame(family_rows)
    if not families.empty:
        families["p_holm"] = holm_adjust(families["p_hc3"])
    families.to_csv(RESULTS / "isodb_compensation_families.csv", index=False)

    print("Krug independent-parameter null", flush=True)
    null = krug_null(primary, SEED + 1, N_NULL)
    null.to_csv(RESULTS / "isodb_compensation_krug_null.csv", index=False)
    t_iso = observed["T_iso_K"]
    harmonic = observed["temperature_harmonic_median_K"]
    summary = {
        "source_commit": lock["commit"],
        "source_archive_sha256": lock["archive_sha256"],
        "ingestion": ingestion_counts,
        "candidate_systems": len(systems),
        "fit_systems_primary_fraction": int((fits["uptake_log_fraction"] == PRIMARY_FRACTION).sum()),
        "primary": observed,
        "bootstrap_95": {
            "slope": bootstrap["slope"].quantile([0.025, 0.975]).tolist(),
            "r2": bootstrap["r2"].quantile([0.025, 0.975]).tolist(),
            "T_iso_K": bootstrap["T_iso_K"].replace([np.inf, -np.inf], np.nan).dropna().quantile([0.025, 0.975]).tolist(),
        },
        "artifact_gate": {
            "T_iso_inside_pooled_temperature_range": bool(observed["temperature_min_K"] <= t_iso <= observed["temperature_max_K"]),
            "T_iso_within_10pct_of_median_harmonic_temperature": bool(abs(t_iso / harmonic - 1) <= 0.10),
            "artifact_consistent": bool(
                observed["temperature_min_K"] <= t_iso <= observed["temperature_max_K"]
                and abs(t_iso / harmonic - 1) <= 0.10
            ),
        },
        "krug_null": {
            "p_null_r2_at_least_observed": float((1 + (null["r2"] >= observed["r2"]).sum()) / (len(null) + 1)),
            "r2_median": float(null["r2"].median()),
            "r2_q025": float(null["r2"].quantile(0.025)),
            "r2_q975": float(null["r2"].quantile(0.975)),
            "T_iso_median_K": float(null["T_iso_K"].replace([np.inf, -np.inf], np.nan).median()),
        },
        "interpretation": "Artifact gate and null are diagnostic; no universal adsorption compensation mechanism is inferred.",
    }
    (RESULTS / "isodb_compensation_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8"
    )

    print("\nPrimary pooled compensation")
    print(pd.DataFrame([observed]).to_string(index=False))
    print("\nArtifact gate")
    print(json.dumps(summary["artifact_gate"], indent=2))
    print("\nKrug null")
    print(json.dumps(summary["krug_null"], indent=2))
    print("\nSensitivity R2 range", sensitivity["r2"].min(), sensitivity["r2"].max())


if __name__ == "__main__":
    main()
