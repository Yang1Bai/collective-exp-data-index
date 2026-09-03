#!/usr/bin/env python3
"""Raw-source cross-laboratory degradation-parameter transfer.

Stages are intentionally separated:

  boundary     Build an analyst-visible cycles<=100 release and a sealed
               recipient outcome release. No recipient outcome statistic is
               printed or written to the audit.
  donor-check  Fit and validate the MATR donor mapping only.
  formal       Open the sealed recipient outcomes exactly once and evaluate the
               frozen transfer family.

Scientific contract:
  analysis/crosslab_fade_transfer_design.json
  analysis/CROSSLAB_FADE_RAW_SOURCE_RESTORATION_AMENDMENT.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import platform
import re
import sys
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.signal import medfilt
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "crosslab_fade_transfer_design.json"
AMENDMENT = HERE / "CROSSLAB_FADE_RAW_SOURCE_RESTORATION_AMENDMENT.md"

EARLY = 100
SOH_EOL = 0.80
GRID = np.linspace(2.0, 3.5, 900)
LIFE_CLIP = (100.0, 100000.0)
TAU = 5.0
BUDGETS = (0, 5, 10)
N_DRAWS = 200
N_BOOT = 10000
N_PERM = 100000
N_INTERVAL = 1000
SEEDS = {
    "master": 20260729,
    "shuffle": 2026072901,
    "draws": 2026072902,
    "bootstrap": 2026072903,
    "gaussian": 2026072904,
}

RESPONSE_FEATURES = [
    "log10_var_delta_qv",
    "log10_abs_min_delta_qv",
    "capacity_slope_2_100",
    "capacity_intercept_2_100",
    "qd100_over_qref",
    "ce_mean_10_100",
    "ce_std_10_100",
]
NORMALIZED_RESPONSE_FEATURES = [
    "log10_var_delta_qv_normalized",
    "log10_abs_min_delta_qv_normalized",
    "capacity_slope_over_qref",
    "capacity_intercept_over_qref",
    "qd100_over_qref",
    "ce_std_10_100",
]
PRIMARY_FEATURES = NORMALIZED_RESPONSE_FEATURES
PROTOCOL_FEATURES = ["mean_charge_c_rate", "mean_discharge_c_rate"]
MAPPING_FEATURES = RESPONSE_FEATURES + PROTOCOL_FEATURES

HUST_DISCHARGE_RATES = {
    "1-1": [5, 1, 1], "1-2": [5, 1, 2], "1-3": [5, 1, 3],
    "1-4": [5, 1, 4], "1-5": [5, 1, 5], "1-6": [5, 2, 1],
    "1-7": [5, 2, 2], "1-8": [5, 2, 3], "2-2": [5, 2, 5],
    "2-3": [5, 3, 1], "2-4": [5, 3, 2], "2-5": [5, 3, 3],
    "2-6": [5, 3, 4], "2-7": [5, 3, 5], "2-8": [5, 4, 1],
    "3-1": [5, 4, 2], "3-2": [5, 4, 3], "3-3": [5, 4, 4],
    "3-4": [5, 4, 5], "3-5": [5, 5, 1], "3-6": [5, 5, 2],
    "3-7": [5, 5, 3], "3-8": [5, 5, 4], "4-1": [5, 5, 5],
    "4-2": [4, 1, 1], "4-3": [4, 1, 2], "4-4": [4, 1, 3],
    "4-5": [4, 1, 4], "4-6": [4, 1, 5], "4-7": [4, 2, 1],
    "4-8": [4, 2, 2], "5-1": [4, 2, 3], "5-2": [4, 2, 4],
    "5-3": [4, 2, 5], "5-4": [4, 3, 1], "5-5": [4, 3, 2],
    "5-6": [4, 3, 3], "5-7": [4, 3, 4], "6-1": [4, 4, 1],
    "6-2": [4, 4, 2], "6-3": [4, 4, 3], "6-4": [4, 4, 4],
    "6-5": [4, 4, 5], "6-6": [4, 5, 1], "6-8": [4, 5, 3],
    "7-1": [4, 5, 4], "7-2": [4, 5, 5], "7-3": [3, 1, 1],
    "7-4": [3, 1, 2], "7-5": [3, 1, 3], "7-6": [3, 1, 4],
    "7-7": [3, 1, 5], "7-8": [3, 2, 1], "8-1": [3, 2, 2],
    "8-2": [3, 2, 3], "8-3": [3, 2, 4], "8-4": [3, 2, 5],
    "8-5": [3, 3, 1], "8-6": [3, 3, 2], "8-7": [3, 3, 3],
    "8-8": [3, 3, 4], "9-1": [3, 3, 5], "9-2": [3, 4, 1],
    "9-3": [3, 4, 2], "9-4": [3, 4, 3], "9-5": [3, 4, 4],
    "9-6": [3, 4, 5], "9-7": [3, 5, 1], "9-8": [3, 5, 2],
    "10-1": [3, 5, 3], "10-2": [3, 5, 4], "10-3": [3, 5, 5],
    "10-4": [2, 4, 1], "10-5": [2, 5, 2], "10-6": [2, 3, 3],
    "10-7": [2, 2, 4], "10-8": [2, 1, 5],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def smooth(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, float)
    return medfilt(values, 5) if len(values) >= 5 else values


def q_reference(capacity: np.ndarray) -> float:
    x = smooth(capacity)
    return float(np.nanmax(x[: min(50, len(x))]))


def life_label(capacity: np.ndarray) -> tuple[float, bool]:
    cap = smooth(capacity)
    qref = q_reference(cap)
    hit = np.flatnonzero(cap / qref <= SOH_EOL)
    if len(hit):
        return float(hit[0] + 1), False
    return float(len(cap)), True


def wls_powerlaw(capacity: np.ndarray, stop: int | None = None):
    cap = smooth(capacity)
    qr = q_reference(cap)
    nmax = min(int(stop) if stop is not None else len(cap), len(cap))
    n = np.arange(1, nmax + 1, dtype=float)
    qloss = np.maximum(1.0 - cap[:nmax] / qr, 1e-5)
    keep = n >= 10
    n, qloss = n[keep], qloss[keep]
    if len(n) < 10:
        return None, None
    x = np.log10(n)
    y = np.log10(qloss)
    w = np.where(qloss > 1e-4, 1.0, 0.1)
    X = np.column_stack([np.ones_like(x), x])
    xtwx = X.T @ (w[:, None] * X)
    try:
        inv = np.linalg.inv(xtwx + 1e-10 * np.eye(2))
    except np.linalg.LinAlgError:
        return None, None
    theta = inv @ X.T @ (w * y)
    residual = y - X @ theta
    dof = max(len(y) - 2, 1)
    sigma2 = float(np.sum(w * residual**2) / max(np.sum(w) * dof / len(y), 1e-9))
    return theta, sigma2 * inv


def life_from_theta(theta: np.ndarray) -> float:
    log_a, beta = map(float, theta)
    if not np.isfinite(log_a + beta) or beta <= 0.01:
        return LIFE_CLIP[1]
    value = 10 ** ((math.log10(1.0 - SOH_EOL) - log_a) / beta)
    return float(np.clip(value, *LIFE_CLIP))


def integrate_capacity(current: np.ndarray, time_s: np.ndarray, charge: bool):
    current = np.asarray(current, float)
    time_s = np.asarray(time_s, float)
    q = np.zeros_like(current, float)
    if len(q) < 2:
        return q
    dt = np.maximum(np.diff(time_s), 0.0)
    inc = current[1:] * dt / 3600.0
    inc = np.where(current[1:] > 0, inc, 0.0) if charge else np.where(
        current[1:] < 0, -inc, 0.0
    )
    q[1:] = np.cumsum(inc)
    return q


def relative_qv(
    voltage: np.ndarray, qd: np.ndarray, current: np.ndarray | None = None
) -> np.ndarray:
    voltage = np.asarray(voltage, float)
    qd = np.asarray(qd, float)
    good = np.isfinite(voltage) & np.isfinite(qd) & (voltage >= GRID[0] - 0.05) & (
        voltage <= GRID[-1] + 0.05
    )
    if current is not None:
        current = np.asarray(current, float)
        good &= np.isfinite(current) & (current < -1e-6)
    voltage, qd = voltage[good], qd[good]
    if len(voltage) < 30:
        return np.full_like(GRID, np.nan)
    order = np.argsort(voltage)
    voltage, qd = voltage[order], qd[order]
    uniq, inverse = np.unique(voltage, return_inverse=True)
    qsum = np.zeros(len(uniq))
    count = np.zeros(len(uniq))
    np.add.at(qsum, inverse, qd)
    np.add.at(count, inverse, 1)
    curve = np.interp(GRID, uniq, qsum / np.maximum(count, 1))
    return curve - curve[-1]


def make_features(
    qd: np.ndarray,
    qc: np.ndarray,
    qv10: np.ndarray,
    qv100: np.ndarray,
    charge_rate: float,
    discharge_rate: float,
) -> dict:
    qd = np.asarray(qd, float)
    qc = np.asarray(qc, float)
    if len(qd) < EARLY:
        return {}
    delta = np.asarray(qv100) - np.asarray(qv10)
    normalized_delta = (
        np.asarray(qv100) / max(abs(qd[99]), 1e-8)
        - np.asarray(qv10) / max(abs(qd[9]), 1e-8)
    )
    if not np.all(np.isfinite(delta)):
        return {}
    cap = smooth(qd[:EARLY])
    cyc = np.arange(1, EARLY + 1, dtype=float)
    slope, intercept = np.polyfit(cyc[1:], cap[1:], 1)
    qr = q_reference(cap)
    ce = qd[:EARLY] / np.where(qc[:EARLY] > 1e-8, qc[:EARLY], np.nan)
    ce = ce[9:100]
    return {
        "log10_var_delta_qv": float(np.log10(np.var(delta) + 1e-14)),
        "log10_abs_min_delta_qv": float(np.log10(abs(np.min(delta)) + 1e-14)),
        "log10_var_delta_qv_normalized": float(
            np.log10(np.var(normalized_delta) + 1e-14)
        ),
        "log10_abs_min_delta_qv_normalized": float(
            np.log10(abs(np.min(normalized_delta)) + 1e-14)
        ),
        "capacity_slope_2_100": float(slope),
        "capacity_intercept_2_100": float(intercept),
        "capacity_slope_over_qref": float(slope / qr),
        "capacity_intercept_over_qref": float(intercept / qr),
        "qd100_over_qref": float(cap[99] / qr),
        "ce_mean_10_100": float(np.nanmean(ce)),
        "ce_std_10_100": float(np.nanstd(ce)),
        "mean_charge_c_rate": float(charge_rate),
        "mean_discharge_c_rate": float(discharge_rate),
    }


def frame_cycle_metrics(frame: pd.DataFrame):
    current = frame["Current (mA)"].to_numpy(float) / 1000.0
    time_s = frame["Time (s)"].to_numpy(float)
    voltage = frame["Voltage (V)"].to_numpy(float)
    qd = integrate_capacity(current, time_s, False)
    qc = integrate_capacity(current, time_s, True)
    return (
        float(np.nanmax(qd)),
        float(np.nanmax(qc)),
        relative_qv(voltage, qd, current),
    )


def hust_records(raw_zip: Path):
    with zipfile.ZipFile(raw_zip) as archive:
        members = sorted(name for name in archive.namelist() if name.lower().endswith(".pkl"))
        for member in members:
            payload = pickle.loads(archive.read(member))
            cell = Path(member).stem
            if cell not in payload and len(payload) == 1:
                cell = next(iter(payload))
            data = payload[cell]["data"]
            keys = sorted(data, key=lambda value: int(value))
            frames = [data[key] for key in keys]
            if cell == "7-5":
                frames = frames[2:]
            yield cell, frames


def hust_feature_and_outcome(cell: str, frames: list[pd.DataFrame]):
    if len(frames) < EARLY:
        return {}, np.array([]), np.array([]), np.full(2, np.nan), np.full((2, 2), np.nan)
    qd, qc = [], []
    qv10 = qv100 = None
    for index, frame in enumerate(frames):
        d, c, curve = frame_cycle_metrics(frame)
        qd.append(d)
        qc.append(c)
        if index == 9:
            qv10 = curve
        if index == 99:
            qv100 = curve
    rates = HUST_DISCHARGE_RATES[cell]
    discharge_rate = 0.4 * rates[0] + 0.2 * rates[1] + 0.2 * rates[2] + 0.2
    features = make_features(
        np.asarray(qd), np.asarray(qc), qv10, qv100, 4.2, discharge_rate
    )
    theta, cov = wls_powerlaw(np.asarray(qd), EARLY)
    return features, np.asarray(qd), np.asarray(qc), theta, cov


def _ref_vector(handle: h5py.File, reference) -> np.ndarray:
    return np.hstack(handle[reference][:].tolist()).astype(float)


def _summary_vector(dataset) -> np.ndarray:
    return np.hstack(dataset[0, :].tolist()).astype(float)


def _matlab_string(handle: h5py.File, reference) -> str:
    raw = handle[reference][:].tobytes()
    try:
        return raw[::2].decode(errors="ignore").strip("\x00")
    except Exception:
        return raw.decode(errors="ignore").strip("\x00")


def matr_charge_rate(policy: str) -> float:
    stages = [x for x in policy.split("-") if x and "new" not in x.lower()]
    rates, weights = [], []
    for stage in stages:
        match = re.search(r"([0-9.]+)C(?:\(([0-9.]+)%\))?", stage)
        if match:
            rates.append(float(match.group(1)))
            weights.append(float(match.group(2) or 20.0) / 100.0)
    if not rates:
        # The Attia closed-loop batch stores four numeric C-rates without the
        # literal "C"; each controls one equal 20%-SOC segment.
        plain = [float(value) for value in re.findall(r"[0-9.]+", policy)]
        return float(np.mean(plain)) if plain else np.nan
    weights = np.asarray(weights, float)
    weights = weights / weights.sum()
    return float(np.dot(rates, weights))


def matr_batch(raw_file: Path, batch_index: int):
    records = {}
    with h5py.File(raw_file, "r") as handle:
        batch = handle["batch"]
        ncell = batch["summary"].shape[0]
        for index in range(ncell):
            summary_group = handle[batch["summary"][index, 0]]
            # MATR summary position zero is a formation/diagnostic placeholder
            # and BatteryML likewise excludes raw cycle zero.
            qd = _summary_vector(summary_group["QDischarge"])[1:]
            qc = _summary_vector(summary_group["QCharge"])[1:]
            reported_life = float(
                np.asarray(handle[batch["cycle_life"][index, 0]][:]).reshape(-1)[0]
            )
            policy = _matlab_string(handle, batch["policy_readable"][index, 0])
            cycles = handle[batch["cycles"][index, 0]]
            curves = {}
            for wanted in (10, 100):
                use = wanted if wanted < cycles["V"].shape[0] else wanted - 1
                voltage = _ref_vector(handle, cycles["V"][use, 0])
                qdis = _ref_vector(handle, cycles["Qd"][use, 0])
                current = _ref_vector(handle, cycles["I"][use, 0])
                curves[wanted] = relative_qv(voltage, qdis, current)
            records[f"b{batch_index}c{index}"] = {
                "batch": f"batch{batch_index}",
                "qd": qd,
                "qc": qc,
                "policy": policy,
                "qv10": curves[10],
                "qv100": curves[100],
                "reported_life": reported_life,
            }
    return records


def load_matr(raw_dir: Path):
    names = [
        "MATR_batch_20170512.mat",
        "MATR_batch_20170630.mat",
        "MATR_batch_20180412.mat",
        "MATR_batch_20190124.mat",
    ]
    batches = [matr_batch(raw_dir / name, i + 1) for i, name in enumerate(names)]
    batch2_keys = ["b2c7", "b2c8", "b2c9", "b2c15", "b2c16"]
    batch1_keys = ["b1c0", "b1c1", "b1c2", "b1c3", "b1c4"]
    continuation_offsets = [662, 981, 1060, 208, 482]
    for first, second, offset in zip(batch1_keys, batch2_keys, continuation_offsets):
        batches[0][first]["qd"] = np.hstack([batches[0][first]["qd"], batches[1][second]["qd"]])
        batches[0][first]["qc"] = np.hstack([batches[0][first]["qc"], batches[1][second]["qc"]])
        batches[0][first]["reported_life"] += offset
    rows = []
    for batch in batches:
        for cell, record in batch.items():
            if cell in batch2_keys:
                continue
            features = make_features(
                record["qd"],
                record["qc"],
                record["qv10"],
                record["qv100"],
                matr_charge_rate(record["policy"]),
                4.0,
            )
            reported = float(record["reported_life"])
            censored = not np.isfinite(reported)
            life = float(len(record["qd"])) if censored else reported
            theta, cov = wls_powerlaw(
                record["qd"], None if censored else min(int(life), len(record["qd"]))
            )
            early_theta, _ = wls_powerlaw(record["qd"], EARLY)
            row = {
                "cell_id": cell,
                "batch": record["batch"],
                "life": life,
                "censored": censored,
                "theta_log10_a": np.nan if theta is None else theta[0],
                "theta_beta": np.nan if theta is None else theta[1],
                "own_theta_log10_a": np.nan if early_theta is None else early_theta[0],
                "own_theta_beta": np.nan if early_theta is None else early_theta[1],
                "own_log10_life": (
                    np.nan
                    if early_theta is None
                    else math.log10(life_from_theta(early_theta))
                ),
            }
            row.update(features)
            rows.append(row)
    return pd.DataFrame(rows)


def atomic_json(path: Path, payload: dict):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def stage_boundary(raw_dir: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    raw_zip = raw_dir / "hust_data.zip"
    early_rows = []
    sealed_cells, sealed_life, sealed_censored = [], [], []
    for cell, frames in hust_records(raw_zip):
        features, qd, _, own_theta, own_cov = hust_feature_and_outcome(cell, frames)
        early = {
            "cell_id": cell,
            "has_at_least_100_cycles": len(qd) >= EARLY,
            "features_computable": bool(features) and all(np.isfinite(list(features.values()))),
            "own_theta_log10_a": np.nan if own_theta is None else own_theta[0],
            "own_theta_beta": np.nan if own_theta is None else own_theta[1],
            "own_cov_00": np.nan if own_cov is None else own_cov[0, 0],
            "own_cov_01": np.nan if own_cov is None else own_cov[0, 1],
            "own_cov_11": np.nan if own_cov is None else own_cov[1, 1],
        }
        early.update(features)
        early_rows.append(early)
        life, censored = life_label(qd)
        sealed_cells.append(cell)
        sealed_life.append(life)
        sealed_censored.append(censored)

    early_df = pd.DataFrame(early_rows).sort_values("cell_id")
    early_path = out / "crosslab_fade_raw_recipient_early_release.csv"
    early_df.to_csv(early_path, index=False)
    sealed_path = out / "crosslab_fade_raw_recipient_outcomes_SEALED.npz"
    np.savez_compressed(
        sealed_path,
        cell_id=np.asarray(sealed_cells),
        life=np.asarray(sealed_life, float),
        censored=np.asarray(sealed_censored, bool),
    )
    meta_path = out / "crosslab_fade_raw_recipient_metadata_no_outcomes.csv"
    early_df[["cell_id", "has_at_least_100_cycles", "features_computable"]].to_csv(
        meta_path, index=False
    )

    required = list(dict.fromkeys(MAPPING_FEATURES + PRIMARY_FEATURES))
    usable = early_df["has_at_least_100_cycles"] & early_df["features_computable"]
    audit = {
        "status": None,
        "design_sha256": sha256(DESIGN),
        "raw_restoration_amendment_sha256": sha256(AMENDMENT),
        "recipient": "HUST LFP/graphite, 77 cells",
        "candidate_time_boundary": "cycles 1-100 only",
        "recipient_outcome_statistics_reported": False,
        "recipient_total_cycle_counts_reported": False,
        "recipient_cells": int(len(early_df)),
        "recipient_cells_with_usable_early_release": int(usable.sum()),
        "realized_feature_intersection": required,
        "excluded_noncommon_features": ["temperature", "internal_resistance"],
        "gate_checks": {
            "recipient_cells_at_least_20": bool(len(early_df) >= 20),
            "usable_early_fraction_at_least_0_90": bool(usable.mean() >= 0.90),
            "delta_qv_available_at_least_0_95": bool(
                early_df["log10_var_delta_qv_normalized"].notna().mean() >= 0.95
            ),
            "protocol_descriptors_available_at_least_0_95": bool(
                early_df[PROTOCOL_FEATURES].notna().all(axis=1).mean() >= 0.95
            ),
        },
        "early_release_sha256": sha256(early_path),
        "sealed_outcomes_sha256": sha256(sealed_path),
        "metadata_sha256": sha256(meta_path),
    }
    audit["status"] = (
        "eligible-preoutcome"
        if all(audit["gate_checks"].values())
        else "audit-gate-failed-abstain"
    )
    atomic_json(out / "crosslab_fade_raw_preoutcome_audit.json", audit)
    print(json.dumps(audit, indent=2))
    return audit


def fit_mapping(X, theta, seed):
    model = RandomForestRegressor(
        n_estimators=500, min_samples_leaf=2, random_state=seed, n_jobs=-1
    )
    model.fit(X, theta)
    return model


def oof_by_batch(X, theta, life, batches):
    pred = np.full_like(theta, np.nan)
    for block in sorted(set(batches)):
        test = np.asarray(batches) == block
        if test.sum() == 0 or (~test).sum() < 10:
            continue
        pred[test] = fit_mapping(X[~test], theta[~test], SEEDS["master"]).predict(X[test])
    valid = np.all(np.isfinite(pred), axis=1)
    residual = theta[valid] - pred[valid]
    covariance = np.cov(residual.T) + 1e-8 * np.eye(2)
    life_pred = np.asarray([life_from_theta(item) for item in pred[valid]])
    rho = spearmanr(np.log10(life_pred), np.log10(life[valid])).statistic
    return pred, covariance, float(rho)


def donor_table(raw_dir: Path, out: Path):
    path = out / "crosslab_fade_raw_donor_table.csv"
    if path.exists():
        return pd.read_csv(path)
    table = load_matr(raw_dir)
    table.to_csv(path, index=False)
    return table


def valid_donor(table: pd.DataFrame):
    cols = MAPPING_FEATURES + ["theta_log10_a", "theta_beta", "life"]
    valid = table[cols].notna().all(axis=1)
    valid &= ~table["censored"].astype(bool)
    valid &= table["theta_beta"] > 0.01
    return table.loc[valid].reset_index(drop=True)


def stage_donor_check(raw_dir: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    table = donor_table(raw_dir, out)
    valid = valid_donor(table)
    scaler = StandardScaler().fit(valid[MAPPING_FEATURES])
    X = scaler.transform(valid[MAPPING_FEATURES])
    theta = valid[["theta_log10_a", "theta_beta"]].to_numpy(float)
    life = valid["life"].to_numpy(float)
    _, covariance, rho = oof_by_batch(X, theta, life, valid["batch"].tolist())
    result = {
        "status": None,
        "donor_cells_total": int(len(table)),
        "donor_cells_valid": int(len(valid)),
        "valid_by_batch": valid["batch"].value_counts().sort_index().to_dict(),
        "batch_out_oof_life_spearman": rho,
        "oof_residual_covariance": covariance.tolist(),
        "gate_checks": {
            "donor_valid_at_least_150": bool(len(valid) >= 150),
            "batch_out_oof_spearman_at_least_0_5": bool(rho >= 0.5),
        },
        "donor_table_sha256": sha256(out / "crosslab_fade_raw_donor_table.csv"),
    }
    result["status"] = (
        "donor-selfcheck-passed"
        if all(result["gate_checks"].values())
        else "donor-selfcheck-failed-abstain"
    )
    atomic_json(out / "crosslab_fade_raw_donor_selfcheck.json", result)
    print(json.dumps(result, indent=2))
    return result


class DonorArm:
    def __init__(self, table: pd.DataFrame, name: str, shuffle=False, gaussian=False):
        self.name = name
        self.map_scaler = StandardScaler().fit(table[MAPPING_FEATURES])
        X = self.map_scaler.transform(table[MAPPING_FEATURES])
        theta = table[["theta_log10_a", "theta_beta"]].to_numpy(float)
        life = table["life"].to_numpy(float)
        if shuffle:
            order = np.random.default_rng(SEEDS["shuffle"]).permutation(len(theta))
            theta, life = theta[order], life[order]
        if gaussian:
            X = np.random.default_rng(SEEDS["gaussian"]).normal(size=X.shape)
        _, self.residual_cov, self.oof_rho = oof_by_batch(
            X, theta, life, table["batch"].tolist()
        )
        self.model = fit_mapping(X, theta, SEEDS["master"])
        self.population_mean = theta.mean(axis=0)
        self.population_cov = np.cov(theta.T) + 1e-8 * np.eye(2)
        if gaussian:
            self.residual_cov = 10 * self.population_cov

        self.support_scaler = StandardScaler().fit(table[RESPONSE_FEATURES])
        support = self.support_scaler.transform(table[RESPONSE_FEATURES])
        self.support_mean = support.mean(axis=0)
        self.support_inverse_cov = np.linalg.pinv(
            np.cov(support.T) + 1e-6 * np.eye(len(RESPONSE_FEATURES))
        )
        distances = np.asarray([self._distance(row) for row in support])
        self.support_threshold = float(np.quantile(distances, 0.90))

    def _distance(self, row):
        delta = row - self.support_mean
        return float(np.sqrt(delta @ self.support_inverse_cov @ delta))

    def prior(self, row: pd.Series, mapped=True):
        support = self.support_scaler.transform(
            row[RESPONSE_FEATURES].to_numpy(float).reshape(1, -1)
        )[0]
        abstain = self._distance(support) > self.support_threshold
        if not mapped:
            return self.population_mean, self.population_cov, abstain
        X = self.map_scaler.transform(
            row[MAPPING_FEATURES].to_numpy(float).reshape(1, -1)
        )
        return self.model.predict(X)[0], self.residual_cov, abstain


class LifeArm:
    """Direct mapping from early within-cell response to log10 life."""

    def __init__(self, table: pd.DataFrame, shuffle: bool = False):
        X = table[PRIMARY_FEATURES].to_numpy(float)
        y = np.log10(table["life"].to_numpy(float))
        if shuffle:
            y = y[np.random.default_rng(SEEDS["shuffle"]).permutation(len(y))]
        self.scaler = StandardScaler().fit(X)
        Xs = self.scaler.transform(X)
        self.model = RandomForestRegressor(
            n_estimators=800,
            min_samples_leaf=2,
            max_features=0.8,
            random_state=SEEDS["master"],
            n_jobs=-1,
        ).fit(Xs, y)
        self.mean_log_life = float(np.mean(y))

        blocks = table["batch"].astype(str).to_numpy()
        oof = np.full(len(y), np.nan)
        if len(np.unique(blocks)) >= 2:
            for block in sorted(np.unique(blocks)):
                test = blocks == block
                train = ~test
                if train.sum() < 10:
                    continue
                fold_scaler = StandardScaler().fit(X[train])
                fold_model = RandomForestRegressor(
                    n_estimators=800,
                    min_samples_leaf=2,
                    max_features=0.8,
                    random_state=SEEDS["master"],
                    n_jobs=-1,
                ).fit(fold_scaler.transform(X[train]), y[train])
                oof[test] = fold_model.predict(fold_scaler.transform(X[test]))
        valid = np.isfinite(oof)
        residual = y[valid] - oof[valid] if valid.any() else y - self.model.predict(Xs)
        self.residual_sd = float(max(np.std(residual, ddof=1), 1e-6))
        self.oof_spearman = (
            float(spearmanr(oof[valid], y[valid]).statistic)
            if valid.sum() >= 3
            else None
        )
        self.oof_r2 = (
            float(1 - np.sum((oof[valid] - y[valid]) ** 2)
                  / np.sum((y[valid] - y[valid].mean()) ** 2))
            if valid.sum() >= 3
            else None
        )

        self.support_mean = Xs.mean(axis=0)
        self.support_inverse_cov = np.linalg.pinv(
            np.cov(Xs.T) + 1e-6 * np.eye(len(PRIMARY_FEATURES))
        )
        distances = np.asarray([self._distance(row) for row in Xs])
        self.support_threshold = float(np.quantile(distances, 0.90))

    def _distance(self, row):
        delta = row - self.support_mean
        return float(np.sqrt(delta @ self.support_inverse_cov @ delta))

    def predict(self, row: pd.Series):
        X = self.scaler.transform(
            row[PRIMARY_FEATURES].to_numpy(float).reshape(1, -1)
        )[0]
        abstain = self._distance(X) > self.support_threshold
        prediction = float(self.model.predict(X.reshape(1, -1))[0])
        half_width = 1.6448536269514722 * self.residual_sd
        return prediction, prediction - half_width, prediction + half_width, abstain


def posterior(mu_prior, cov_prior, mu_own, cov_own):
    try:
        p1 = np.linalg.inv(cov_prior)
        p2 = np.linalg.inv(cov_own + 1e-10 * np.eye(2))
        cov = np.linalg.inv(p1 + p2)
        mean = cov @ (p1 @ mu_prior + p2 @ mu_own)
        return mean, cov
    except np.linalg.LinAlgError:
        return mu_prior, cov_prior


def interval(theta, covariance, rng):
    sample = rng.multivariate_normal(theta, covariance, N_INTERVAL)
    life = np.asarray([life_from_theta(item) for item in sample])
    return np.quantile(np.log10(life), [0.05, 0.95])


def holm_adjust(pvalues: list[float]) -> list[float]:
    order = np.argsort(pvalues)
    adjusted = np.zeros(len(pvalues))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted.tolist()


def stage_formal(raw_dir: Path, out: Path):
    audit = json.loads((out / "crosslab_fade_raw_preoutcome_audit.json").read_text())
    donor_check = json.loads((out / "crosslab_fade_raw_donor_selfcheck.json").read_text())
    if audit["status"] != "eligible-preoutcome":
        raise RuntimeError("Recipient audit did not pass; formal stage forbidden")
    if donor_check["status"] != "donor-selfcheck-passed":
        raise RuntimeError("Donor-only gate did not pass; formal stage forbidden")

    early = pd.read_csv(out / "crosslab_fade_raw_recipient_early_release.csv")
    donor = valid_donor(donor_table(raw_dir, out))
    wrong_path = out / "crosslab_fade_raw_wrong_chem_table.csv"
    if not wrong_path.exists():
        raise RuntimeError(
            "Wrong-chemistry table is absent; formal stage is forbidden until "
            "the frozen CALCE control is complete"
        )
    wrong = pd.read_csv(wrong_path)
    wrong_required = PRIMARY_FEATURES + ["life", "batch"]
    wrong = wrong.loc[wrong[wrong_required].notna().all(axis=1)].reset_index(drop=True)
    if len(wrong) < 8:
        raise RuntimeError("Fewer than eight usable CALCE wrong-chemistry cells")
    sealed = np.load(out / "crosslab_fade_raw_recipient_outcomes_SEALED.npz")
    outcomes = pd.DataFrame(
        {
            "cell_id": sealed["cell_id"].astype(str),
            "life": sealed["life"].astype(float),
            "censored": sealed["censored"].astype(bool),
        }
    )
    recipient = early.merge(outcomes, on="cell_id", validate="one_to_one")
    usable = recipient[MAPPING_FEATURES].notna().all(axis=1)
    usable &= recipient[
        ["own_theta_log10_a", "own_theta_beta", "own_cov_00", "own_cov_01", "own_cov_11"]
    ].notna().all(axis=1)
    usable &= ~recipient["censored"]
    recipient = recipient.loc[usable].reset_index(drop=True)
    if len(recipient) < 20:
        raise RuntimeError("Fewer than 20 uncensored recipient cells")

    primary_arm = LifeArm(donor)
    shuffled_arm = LifeArm(donor, shuffle=True)
    wrong_arm = LifeArm(wrong)
    coefficient_arm = DonorArm(donor, "coefficient")
    rng = np.random.default_rng(SEEDS["master"] + 1)
    prediction_rows = []
    for _, row in recipient.iterrows():
        own_theta = row[["own_theta_log10_a", "own_theta_beta"]].to_numpy(float)
        own_cov = np.asarray(
            [[row["own_cov_00"], row["own_cov_01"]], [row["own_cov_01"], row["own_cov_11"]]]
        )
        own_log_life = math.log10(life_from_theta(own_theta))
        own_interval = interval(own_theta, own_cov, rng)
        result = {
            "cell_id": row["cell_id"],
            "log10_life_true": math.log10(row["life"]),
            "recipient_only": own_log_life,
            "recipient_only_lo": own_interval[0],
            "recipient_only_hi": own_interval[1],
        }
        for name, arm in [
            ("donor_response_transfer", primary_arm),
            ("shuffled_donor", shuffled_arm),
            ("wrong_chemistry_donor", wrong_arm),
        ]:
            prediction, lo, hi, abstain = arm.predict(row)
            if abstain:
                result[name] = own_log_life
                result[f"{name}_lo"] = own_interval[0]
                result[f"{name}_hi"] = own_interval[1]
            else:
                result[name] = prediction
                result[f"{name}_lo"] = lo
                result[f"{name}_hi"] = hi
            result[f"{name}_abstain"] = bool(abstain)
        result["donor_mean"] = primary_arm.mean_log_life

        mu, covariance, abstain = coefficient_arm.prior(row, mapped=True)
        if abstain:
            result["coefficient_posterior"] = own_log_life
            result["coefficient_posterior_lo"] = own_interval[0]
            result["coefficient_posterior_hi"] = own_interval[1]
        else:
            mean, cov = posterior(mu, covariance, own_theta, own_cov)
            result["coefficient_posterior"] = math.log10(life_from_theta(mean))
            (result["coefficient_posterior_lo"],
             result["coefficient_posterior_hi"]) = interval(mean, cov, rng)
        result["coefficient_posterior_abstain"] = bool(abstain)
        prediction_rows.append(result)

    predictions = pd.DataFrame(prediction_rows)
    prediction_path = out / "crosslab_fade_raw_formal_predictions.csv"
    predictions.to_csv(prediction_path, index=False)
    y = predictions["log10_life_true"].to_numpy(float)
    methods = [
        "recipient_only",
        "donor_response_transfer",
        "shuffled_donor",
        "wrong_chemistry_donor",
        "donor_mean",
        "coefficient_posterior",
    ]

    def metrics(method):
        pred = predictions[method].to_numpy(float)
        error = pred - y
        result = {
            "rmse_log10_life": float(np.sqrt(np.mean(error**2))),
            "mape_life": float(np.mean(np.abs(10**pred - 10**y) / 10**y)),
            "spearman": float(spearmanr(pred, y).statistic),
            "r2_log10_life": float(1 - np.sum(error**2) / np.sum((y - y.mean()) ** 2)),
        }
        if f"{method}_lo" in predictions:
            result["coverage90"] = float(
                np.mean((predictions[f"{method}_lo"] <= y) & (y <= predictions[f"{method}_hi"]))
            )
        return result

    method_metrics = {method: metrics(method) for method in methods}
    boot_rng = np.random.default_rng(SEEDS["bootstrap"])
    real = predictions["donor_response_transfer"].to_numpy(float)
    real_se = (real - y) ** 2
    bases = [
        "recipient_only",
        "shuffled_donor",
        "wrong_chemistry_donor",
        "donor_mean",
        "coefficient_posterior",
    ]
    contrasts, pvalues = [], []
    for base in bases:
        base_pred = predictions[base].to_numpy(float)
        base_se = (base_pred - y) ** 2
        relative = 1 - np.sqrt(real_se.mean()) / np.sqrt(base_se.mean())
        indices = boot_rng.integers(0, len(y), size=(N_BOOT, len(y)))
        bootstrap = 1 - np.sqrt(real_se[indices].mean(axis=1)) / np.sqrt(
            base_se[indices].mean(axis=1)
        )
        paired = base_se - real_se
        flips = boot_rng.choice([-1, 1], size=(N_PERM, len(y)))
        null = (flips * paired).mean(axis=1)
        pvalue = float((1 + np.sum(null >= paired.mean())) / (N_PERM + 1))
        contrasts.append(
            {
                "contrast": f"donor_response_transfer_vs_{base}",
                "relative_rmse_reduction": float(relative),
                "ci95": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
                "fraction_cells_improved": float(np.mean(paired > 0)),
                "sign_flip_p_one_sided": pvalue,
            }
        )
        pvalues.append(pvalue)
    for contrast, adjusted in zip(contrasts, holm_adjust(pvalues)):
        contrast["holm_p"] = adjusted

    draw_rng = np.random.default_rng(SEEDS["draws"])
    budget_rows = []
    for budget in BUDGETS[1:]:
        for draw in range(N_DRAWS):
            labelled = draw_rng.choice(len(y), size=budget, replace=False)
            evaluate = np.setdiff1d(np.arange(len(y)), labelled)
            for method in methods:
                pred = predictions[method].to_numpy(float).copy()
                shift = np.mean(y[labelled] - pred[labelled]) * budget / (budget + TAU)
                rmse = np.sqrt(np.mean((pred[evaluate] + shift - y[evaluate]) ** 2))
                budget_rows.append(
                    {"budget": budget, "draw": draw, "method": method, "rmse_log10_life": rmse}
                )
    budget_path = out / "crosslab_fade_raw_formal_metrics.csv"
    pd.DataFrame(budget_rows).to_csv(budget_path, index=False)

    primary = contrasts[0]
    shuffled = contrasts[1]
    wrong_contrast = contrasts[2]
    coverage_real = method_metrics["donor_response_transfer"].get("coverage90", np.nan)
    coverage_own = method_metrics["recipient_only"].get("coverage90", np.nan)
    gate = {
        "relative_rmse_reduction_at_least_0_10": primary["relative_rmse_reduction"] >= 0.10,
        "ci95_lower_above_zero": primary["ci95"][0] > 0,
        "holm_p_below_0_05": primary["holm_p"] < 0.05,
        "margin_over_shuffled_at_least_0_05": shuffled["relative_rmse_reduction"] >= 0.05,
        "margin_over_wrong_chemistry_at_least_0_05":
            wrong_contrast["relative_rmse_reduction"] >= 0.05,
        "absolute_r2_above_zero":
            method_metrics["donor_response_transfer"]["r2_log10_life"] > 0,
        "coverage_not_degraded_more_than_5pp": coverage_real >= coverage_own - 0.05,
        "fraction_cells_improved_at_least_0_65": primary["fraction_cells_improved"] >= 0.65,
        "wrong_chemistry_control_complete": True,
    }
    summary = {
        "status": "formal-complete",
        "design_sha256": sha256(DESIGN),
        "raw_restoration_amendment_sha256": sha256(AMENDMENT),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "recipient_uncensored_evaluated": int(len(recipient)),
        "donor_valid_cells": int(len(donor)),
        "donor_oof_spearman": primary_arm.oof_spearman,
        "donor_oof_r2": primary_arm.oof_r2,
        "wrong_chemistry_cells": int(len(wrong)),
        "abstention_rate": float(
            predictions["donor_response_transfer_abstain"].mean()
        ),
        "method_metrics_budget0": method_metrics,
        "contrasts_budget0": contrasts,
        "success_gate": {
            "checks": gate,
            "pass": bool(all(gate.values())),
            "decision": (
                "positive-crosslab-response-edge"
                if all(gate.values())
                else "null-harmful-or-abstaining-edge"
            ),
        },
        "predictions_sha256": sha256(prediction_path),
        "metrics_sha256": sha256(budget_path),
        "claim_guard": (
            "The raw HUST recipient was preceded by an approximate mirror run. "
            "This is a pre-specified raw-source confirmation, not a never-seen "
            "recipient and not prospective laboratory discovery."
        ),
    }
    atomic_json(out / "crosslab_fade_raw_formal_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["boundary", "donor-check", "formal"], required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()
    if args.stage == "boundary":
        result = stage_boundary(args.raw_dir, args.out)
        return 0 if result["status"] == "eligible-preoutcome" else 2
    if args.stage == "donor-check":
        result = stage_donor_check(args.raw_dir, args.out)
        return 0 if result["status"] == "donor-selfcheck-passed" else 2
    stage_formal(args.raw_dir, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
