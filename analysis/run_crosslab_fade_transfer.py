#!/usr/bin/env python3
"""Cross-laboratory degradation-parameter transfer (H1 flagship).

Frozen design: analysis/crosslab_fade_transfer_design.json (+ infrastructure
amendment 1). Stages: audit -> donor-check -> formal. The audit stage reads
recipient files with a hard nrows=101 cap so recipient outcomes are physically
unread before the formal stage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import medfilt
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
DATA = Path("/home/claude/PINN4SOH/data")
BML = Path("/home/claude/BatteryML/batteryml/preprocess/preprocess_HUST.py")
OUT = Path("/home/claude/results")
OUT.mkdir(exist_ok=True)

SEEDS = {"master": 20260729, "shuffle": 2026072901, "draws": 2026072902,
         "bootstrap": 2026072903, "gaussian": 2026072904}
EARLY = 100          # candidate-time window (cycles)
SOH_EOL = 0.89  # amendment 2: rule-derived milestone
LIFE_CLIP = (100.0, 100000.0)
TAU = 5.0            # recalibration shrinkage
BUDGETS = [0, 5, 10]
N_DRAWS = 200
N_BOOT = 10000
N_PERM = 100000
MC_INT = 1000        # MC samples for predictive intervals

CHARGE_COLS = ['voltage mean', 'voltage std', 'voltage kurtosis',
               'voltage skewness', 'CC Q', 'CC charge time', 'voltage slope',
               'voltage entropy', 'current mean', 'current std',
               'current kurtosis', 'current skewness', 'CV Q',
               'CV charge time', 'current slope', 'current entropy']


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def hust_rate_families() -> dict:
    """Parse DISCHARGE_RATES from the pinned BatteryML clone."""
    text = BML.read_text()
    block = text[text.index('DISCHARGE_RATES'):]
    pairs = re.findall(r"'(\d+-\d+)':\s*\[(\d+),\s*(\d+),\s*(\d+)\]", block)
    return {k: (int(a), int(b), int(c)) for k, a, b, c in pairs}


# ----------------------------------------------------------------- degradation
def smooth(cap: np.ndarray) -> np.ndarray:
    if len(cap) < 5:
        return cap.astype(float)
    return medfilt(cap.astype(float), 5)


def q_ref(cap_s: np.ndarray) -> float:
    return float(np.nanmax(cap_s[:50])) if len(cap_s) else np.nan


def life_label(cap_s: np.ndarray, qref: float):
    soh = cap_s / qref
    idx = np.where(soh <= SOH_EOL)[0]
    if len(idx) == 0:
        return None  # right-censored
    return int(idx[0] + 1)  # 1-based cycle


def wls_powerlaw(cycles: np.ndarray, qloss: np.ndarray):
    """WLS fit of log10 qloss vs log10 n. Returns theta=(log10a, beta), cov."""
    m = cycles >= 10
    n, q = cycles[m].astype(float), qloss[m]
    if len(n) < 5:
        return None, None
    y = np.log10(np.maximum(q, 1e-5))
    x = np.log10(n)
    w = np.where(q > 1e-4, 1.0, 0.1)
    X = np.column_stack([np.ones_like(x), x])
    W = np.diag(w)
    XtWX = X.T @ W @ X
    try:
        XtWX_inv = np.linalg.inv(XtWX + 1e-10 * np.eye(2))
    except np.linalg.LinAlgError:
        return None, None
    theta = XtWX_inv @ X.T @ W @ y
    resid = y - X @ theta
    dof = max(len(n) - 2, 1)
    sigma2 = float((w * resid ** 2).sum() / max(w.sum() * dof / len(n), 1e-9))
    cov = sigma2 * XtWX_inv
    return theta, cov  # theta[0]=log10 a, theta[1]=beta


def life_from_theta(theta: np.ndarray) -> float:
    log10a, beta = float(theta[0]), float(theta[1])
    if beta <= 0.01:
        return LIFE_CLIP[1]
    n = 10 ** ((np.log10(1 - SOH_EOL) - log10a) / beta)
    return float(np.clip(n, *LIFE_CLIP))


# ------------------------------------------------------------------- features
def early_features(df: pd.DataFrame) -> np.ndarray | None:
    """51 symmetric features from cycles <=100. df rows are cycles 1..N."""
    if len(df) < 101:
        return None
    d = df.iloc[:EARLY]
    feats = []
    cyc = np.arange(1, EARLY + 1, dtype=float)
    for c in CHARGE_COLS:
        v = d[c].to_numpy(float)
        lev = np.nanmedian(v[9:30])
        sl = np.polyfit(cyc[9:], np.nan_to_num(v[9:], nan=np.nanmedian(v)),
                        1)[0]
        delta = np.nanmedian(v[90:100]) - np.nanmedian(v[4:14])
        feats += [lev, sl, delta]
    cap = d['capacity'].to_numpy(float)
    cap_s = smooth(cap)
    qr = q_ref(cap_s)
    feats.append(cap_s[EARLY - 1] / qr)
    coef = np.polyfit(cyc[1:], cap[1:], 1)
    feats.append(coef[0])
    resid = cap[9:] - np.polyval(np.polyfit(cyc[9:], cap[9:], 1), cyc[9:])
    feats.append(np.log10(np.var(resid) + 1e-12))
    return np.asarray(feats, float)


def load_cells(folder: Path, nrows: int | None = None) -> dict:
    cells = {}
    for f in sorted(folder.glob('*.csv')):
        try:
            df = pd.read_csv(f, nrows=nrows)
        except Exception:
            continue
        cells[f.stem] = df
    return cells


def donor_cell_table(folder: Path, qref_bounds=(0.99, 1.32)):
    """Full-trajectory fits for a donor population."""
    rows = []
    for f in sorted(folder.glob('**/*.csv')):
        df = pd.read_csv(f)
        if 'capacity' not in df.columns or len(df) < 101:
            continue
        x = early_features(df)
        cap_s = smooth(df['capacity'].to_numpy(float))
        qr = q_ref(cap_s)
        life = life_label(cap_s, qr)
        valid = (life is not None and x is not None
                 and np.all(np.isfinite(x)))
        if qref_bounds is not None:
            valid = valid and (qref_bounds[0] <= qr <= qref_bounds[1])
        theta = cov = None
        if valid:
            cyc = np.arange(1, life + 1, dtype=float)
            qloss = np.maximum(1 - cap_s[:life] / qr, 1e-5)
            theta, cov = wls_powerlaw(cyc, qloss)
            valid = theta is not None and theta[1] > 0
        rows.append({"cell": f.stem, "batch": f.parent.name, "valid": valid,
                     "qref": qr, "life": life, "features": x,
                     "theta": theta})
    return rows


# ------------------------------------------------------------------ mechanics
def fit_mapping(X, TH, seed):
    rf = RandomForestRegressor(n_estimators=500, min_samples_leaf=2,
                               random_state=seed, n_jobs=-1)
    rf.fit(X, TH)
    return rf


def oof_by_block(X, TH, lives, blocks, seed):
    """Block-out OOF predictions; returns preds, residual cov, life Spearman."""
    preds = np.zeros_like(TH)
    for b in sorted(set(blocks)):
        m = np.asarray([bb == b for bb in blocks])
        if m.all() or (~m).sum() < 10:
            continue
        rf = fit_mapping(X[~m], TH[~m], seed)
        preds[m] = rf.predict(X[m])
    resid = TH - preds
    cov = np.cov(resid.T) + 1e-8 * np.eye(2)
    oof_life = np.array([life_from_theta(t) for t in preds])
    rho = spearmanr(np.log10(oof_life), np.log10(lives)).statistic
    return preds, cov, float(rho)


def posterior(theta_prior, cov_prior, theta_own, cov_own):
    if theta_own is None or cov_own is None:
        return theta_prior, cov_prior
    try:
        P1 = np.linalg.inv(cov_prior)
        P2 = np.linalg.inv(cov_own + 1e-10 * np.eye(2))
        C = np.linalg.inv(P1 + P2)
        m = C @ (P1 @ theta_prior + P2 @ theta_own)
        return m, C
    except np.linalg.LinAlgError:
        return theta_prior, cov_prior


def interval(theta, cov, rng):
    s = rng.multivariate_normal(theta, cov, MC_INT)
    lives = np.array([life_from_theta(t) for t in s])
    return np.quantile(np.log10(lives), [0.05, 0.95])


class DonorArm:
    """A prior + mapping arm (real / shuffled / wrong-chem / gaussian)."""

    def __init__(self, name, donor_rows, seed, shuffle_seed=None,
                 gaussian_seed=None):
        self.name = name
        valid = [r for r in donor_rows if r['valid']]
        X = np.stack([r['features'] for r in valid])
        TH = np.stack([r['theta'] for r in valid])
        lives = np.array([r['life'] for r in valid], float)
        blocks = [r['batch'] for r in valid]
        if shuffle_seed is not None:
            rng = np.random.default_rng(shuffle_seed)
            perm = rng.permutation(len(TH))
            TH, lives = TH[perm], lives[perm]
        if gaussian_seed is not None:
            rng = np.random.default_rng(gaussian_seed)
            X = rng.normal(size=X.shape)
        self.scaler = StandardScaler().fit(X)
        Xs = self.scaler.transform(X)
        self.pop_mean = TH.mean(axis=0)
        self.pop_cov = np.cov(TH.T) + 1e-8 * np.eye(2)
        _, self.res_cov, self.oof_rho = oof_by_block(
            Xs, TH, lives, blocks, seed)
        if gaussian_seed is not None:
            self.res_cov = 10.0 * self.pop_cov
        self.model = fit_mapping(Xs, TH, seed)
        self.mu = Xs.mean(axis=0)
        self.cov_feat = np.cov(Xs.T) + 1e-6 * np.eye(Xs.shape[1])
        self.cov_feat_inv = np.linalg.pinv(self.cov_feat)
        d = [self._mah(x) for x in Xs]
        self.mah_thresh = float(np.quantile(d, 0.90))
        self.n_valid = len(valid)

    def _mah(self, xs):
        v = xs - self.mu
        return float(np.sqrt(v @ self.cov_feat_inv @ v))

    def prior_for(self, x, use_mapping=True):
        xs = self.scaler.transform(x.reshape(1, -1))[0]
        abstain = self._mah(xs) > self.mah_thresh
        if use_mapping:
            mu = self.model.predict(xs.reshape(1, -1))[0]
            return mu, self.res_cov, abstain
        return self.pop_mean, self.pop_cov, abstain


# ---------------------------------------------------------------------- audit
def stage_audit():
    rates = hust_rate_families()
    rec_dir = DATA / 'HUST data'
    meta, usable = [], 0
    feat_ok = 0
    for f in sorted(rec_dir.glob('*.csv')):
        df = pd.read_csv(f, nrows=101)          # hard candidate-time cap
        has101 = len(df) >= 101 and df['capacity'].iloc[:101].notna().sum() >= 95
        x = early_features(df) if has101 else None
        ok = x is not None and np.all(np.isfinite(x))
        usable += has101
        feat_ok += ok
        fam = rates.get(f.stem, (None,))[0]
        meta.append({"cell_id": f.stem, "has_101_cycles": bool(has101),
                     "features_computable": bool(ok),
                     "rate_family_stage1": fam})
    meta_df = pd.DataFrame(meta)
    meta_path = OUT / 'crosslab_fade_recipient_metadata_no_outcomes.csv'
    meta_df.to_csv(meta_path, index=False)

    donor_files = sorted((DATA / 'MIT data').glob('**/*.csv'))
    xjtu_files = sorted((DATA / 'XJTU data').glob('*.csv'))
    n_cells = len(meta)
    audit = {
        "status": None,
        "design": "analysis/crosslab_fade_transfer_design.json",
        "amendment": "analysis/CROSSLAB_FADE_INFRASTRUCTURE_AMENDMENT.md",
        "mirror_commit": "bf7a93148de6a7e249c1b053bd60fe3c9a3dc1f0",
        "recipient_read_cap_rows": 101,
        "recipient_outcomes_read": False,
        "recipient_cells": n_cells,
        "recipient_cells_with_101_cycles": int(usable),
        "recipient_feature_computable": int(feat_ok),
        "recipient_rate_families_known": int(meta_df['rate_family_stage1']
                                             .notna().sum()),
        "donor_files": len(donor_files),
        "wrong_chem_files": len(xjtu_files),
        "gate_checks": {
            "recipient_cells_at_least_20": bool(n_cells >= 20),
            "early_cycle_fraction_at_least_0_9":
                bool(usable / max(n_cells, 1) >= 0.9),
            "feature_intersection_available":
                bool(feat_ok / max(n_cells, 1) >= 0.9),
            "donor_files_at_least_100": bool(len(donor_files) >= 100),
        },
        "metadata_csv_sha256": sha256(meta_path),
    }
    audit["status"] = ("eligible-preoutcome"
                       if all(audit["gate_checks"].values())
                       else "audit-gate-failed-abstain")
    path = OUT / 'crosslab_fade_preoutcome_audit.json'
    path.write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))
    return audit


# ----------------------------------------------------------------- donor check
def stage_donor_check():
    donor_rows = donor_cell_table(DATA / 'MIT data')
    valid = [r for r in donor_rows if r['valid']]
    X = np.stack([r['features'] for r in valid])
    TH = np.stack([r['theta'] for r in valid])
    lives = np.array([r['life'] for r in valid], float)
    blocks = [r['batch'] for r in valid]
    scaler = StandardScaler().fit(X)
    _, res_cov, rho = oof_by_block(scaler.transform(X), TH, lives, blocks,
                                   SEEDS['master'])
    per_batch = pd.Series(blocks).value_counts().to_dict()
    # milestone-consistency diagnostic (amendment 2)
    l89, l85 = [], []
    for r in valid:
        f = None
        for sub in (DATA / 'MIT data').glob('**/*.csv'):
            if sub.stem == r['cell']:
                f = sub; break
        df = pd.read_csv(f)
        cap_s = smooth(df['capacity'].to_numpy(float))
        qr = q_ref(cap_s)
        soh = cap_s / qr
        i89 = np.where(soh <= 0.89)[0]
        i85 = np.where(soh <= 0.85)[0]
        if len(i89) and len(i85):
            l89.append(i89[0] + 1); l85.append(i85[0] + 1)
    mil_rho = (float(spearmanr(l89, l85).statistic)
               if len(l89) >= 10 else None)
    out = {
        "donor_cells_total": len(donor_rows),
        "donor_cells_valid": len(valid),
        "donor_cells_censored_or_qref_excluded":
            len(donor_rows) - len(valid),
        "per_batch_valid": per_batch,
        "oof_residual_cov": res_cov.tolist(),
        "batch_out_oof_life_spearman": rho,
        "life_range": [float(lives.min()), float(lives.max())],
        "milestone_consistency_spearman_89_vs_85": mil_rho,
        "milestone_consistency_n": len(l89),
        "gate_checks": {
            "donor_valid_at_least_100": len(valid) >= 100,
            "oof_spearman_at_least_0_5": bool(rho >= 0.5),
        },
    }
    out["status"] = ("donor-selfcheck-passed"
                     if all(out["gate_checks"].values())
                     else "donor-selfcheck-failed-abstain")
    (OUT / 'crosslab_fade_donor_selfcheck.json').write_text(
        json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return out


# --------------------------------------------------------------------- formal
def recipient_table():
    rows = []
    for f in sorted((DATA / 'HUST data').glob('*.csv')):
        df = pd.read_csv(f)                     # outcome access (post-freeze)
        x = early_features(df)
        cap_s = smooth(df['capacity'].to_numpy(float))
        qr = q_ref(cap_s)
        life = life_label(cap_s, qr)
        cyc = np.arange(1, EARLY + 1, dtype=float)
        qloss = np.maximum(1 - cap_s[:EARLY] / qr, 1e-5)
        th_own, cov_own = wls_powerlaw(cyc, qloss)
        rows.append({"cell": f.stem, "features": x, "qref": qr,
                     "life": life, "theta_own": th_own, "cov_own": cov_own,
                     "censored": life is None})
    return rows


def stage_formal():
    rng = np.random.default_rng(SEEDS['master'])
    donor_rows = donor_cell_table(DATA / 'MIT data')
    arms = {
        "donor_prior_transfer": DonorArm(
            "real", donor_rows, SEEDS['master']),
        "shuffled_donor": DonorArm(
            "shuffled", donor_rows, SEEDS['master'],
            shuffle_seed=SEEDS['shuffle']),
        "gaussian_prior": DonorArm(
            "gaussian", donor_rows, SEEDS['master'],
            gaussian_seed=SEEDS['gaussian']),
    }
    xjtu_rows = donor_cell_table(DATA / 'XJTU data', qref_bounds=None)
    arms["wrong_chemistry_prior"] = DonorArm(
        "xjtu", xjtu_rows, SEEDS['master'])

    rec = recipient_table()
    unc = [r for r in rec if not r['censored'] and r['features'] is not None
           and np.all(np.isfinite(r['features']))]
    print(f"recipient cells: {len(rec)}, uncensored+featured: {len(unc)}")
    if len(unc) < 20:
        abort = {"status": "insufficient-uncensored-recipient-abstain",
                 "recipient_cells": len(rec),
                 "recipient_uncensored": len(unc)}
        (OUT / 'crosslab_fade_formal_summary.json').write_text(
            json.dumps(abort, indent=2))
        print(json.dumps(abort, indent=2))
        return abort

    preds = {}
    int_rng = np.random.default_rng(SEEDS['master'] + 1)
    rows_out = []
    for r in unc:
        row = {"cell": r['cell'], "log10_life_true": np.log10(r['life'])}
        own_life = (life_from_theta(r['theta_own'])
                    if r['theta_own'] is not None else LIFE_CLIP[1])
        row['recipient_only'] = np.log10(own_life)
        lo, hi = (interval(r['theta_own'], r['cov_own'], int_rng)
                  if r['theta_own'] is not None else (np.nan, np.nan))
        row['recipient_only_lo'], row['recipient_only_hi'] = lo, hi
        for name, arm in arms.items():
            use_map = True
            mu, cov, abstain = arm.prior_for(r['features'], use_map)
            if abstain:
                row[name] = row['recipient_only']
                row[f'{name}_lo'] = row['recipient_only_lo']
                row[f'{name}_hi'] = row['recipient_only_hi']
                row[f'{name}_abstain'] = True
            else:
                m, C = posterior(mu, cov, r['theta_own'], r['cov_own'])
                row[name] = np.log10(life_from_theta(m))
                row[f'{name}_lo'], row[f'{name}_hi'] = interval(m, C, int_rng)
                row[f'{name}_abstain'] = False
        # prior_only from the real arm without mapping
        arm = arms['donor_prior_transfer']
        mu, cov, abstain = arm.prior_for(r['features'], use_mapping=False)
        m, C = posterior(mu, cov, r['theta_own'], r['cov_own'])
        row['prior_only'] = np.log10(life_from_theta(m))
        row['prior_only_lo'], row['prior_only_hi'] = interval(m, C, int_rng)
        rows_out.append(row)

    # oracle: LOO mapping fitted on other recipient cells
    Xr = np.stack([r['features'] for r in unc])
    THr, ok_idx = [], []
    for i, r in enumerate(unc):
        if r['theta_own'] is None:
            continue
        cyc = np.arange(1, r['life'] + 1, dtype=float)
        # oracle uses full recipient trajectories (upper bound only)
    # full-trajectory oracle coefficients
    oracle_th = []
    for r in unc:
        f = DATA / 'HUST data' / f"{r['cell']}.csv"
        df = pd.read_csv(f)
        cap_s = smooth(df['capacity'].to_numpy(float))
        qr = q_ref(cap_s)
        cyc = np.arange(1, r['life'] + 1, dtype=float)
        qloss = np.maximum(1 - cap_s[:r['life']] / qr, 1e-5)
        th, _ = wls_powerlaw(cyc, qloss)
        oracle_th.append(th)
    scaler_r = StandardScaler().fit(Xr)
    Xrs = scaler_r.transform(Xr)
    THo = np.stack([t if t is not None else np.array([np.nan, np.nan])
                    for t in oracle_th])
    good = np.all(np.isfinite(THo), axis=1)
    for i, row in enumerate(rows_out):
        m = good.copy()
        m[i] = False
        if m.sum() < 10 or not good[i]:
            row['oracle_all_recipient'] = np.nan
            continue
        rf = fit_mapping(Xrs[m], THo[m], SEEDS['master'])
        th = rf.predict(Xrs[i].reshape(1, -1))[0]
        row['oracle_all_recipient'] = np.log10(life_from_theta(th))

    pred_df = pd.DataFrame(rows_out)
    pred_path = OUT / 'crosslab_fade_formal_predictions.csv'
    pred_df.to_csv(pred_path, index=False)

    methods = ['recipient_only', 'donor_prior_transfer', 'shuffled_donor',
               'wrong_chemistry_prior', 'prior_only', 'gaussian_prior']

    def rmse(col, mask=None):
        d = pred_df if mask is None else pred_df[mask]
        return float(np.sqrt(np.mean((d[col] - d['log10_life_true']) ** 2)))

    y = pred_df['log10_life_true'].to_numpy()

    def metrics_for(col):
        p = pred_df[col].to_numpy()
        r = {
            "rmse_log10_life": float(np.sqrt(np.mean((p - y) ** 2))),
            "mape_life": float(np.mean(np.abs(10 ** p - 10 ** y) / 10 ** y)),
            "spearman": float(spearmanr(p, y).statistic),
            "r2_log10_life": float(1 - np.sum((p - y) ** 2)
                                   / np.sum((y - y.mean()) ** 2)),
        }
        lo = pred_df.get(f'{col}_lo')
        if lo is not None and pred_df.get(f'{col}_hi') is not None:
            cov = np.mean((pred_df[f'{col}_lo'] <= y)
                          & (y <= pred_df[f'{col}_hi']))
            r["coverage90"] = float(cov)
        return r

    metrics = {m: metrics_for(m) for m in methods}
    om = pred_df['oracle_all_recipient'].notna()
    if om.any():
        po = pred_df.loc[om, 'oracle_all_recipient'].to_numpy()
        yo = pred_df.loc[om, 'log10_life_true'].to_numpy()
        metrics['oracle_all_recipient'] = {
            "rmse_log10_life": float(np.sqrt(np.mean((po - yo) ** 2))),
            "n": int(om.sum())}

    # --- contrasts at primary budget k=0
    boot_rng = np.random.default_rng(SEEDS['bootstrap'])
    n = len(pred_df)
    t = pred_df['donor_prior_transfer'].to_numpy()
    se_t = (t - y) ** 2
    contrasts, pvals = [], []
    for base in ['recipient_only', 'shuffled_donor', 'wrong_chemistry_prior',
                 'prior_only', 'gaussian_prior']:
        b = pred_df[base].to_numpy()
        se_b = (b - y) ** 2
        rel = 1 - np.sqrt(se_t.mean()) / np.sqrt(se_b.mean())
        idx = boot_rng.integers(0, n, size=(N_BOOT, n))
        rel_bs = 1 - (np.sqrt(se_t[idx].mean(axis=1))
                      / np.sqrt(se_b[idx].mean(axis=1)))
        d = se_b - se_t
        flips = boot_rng.choice([-1, 1], size=(N_PERM, n))
        null = (flips * d).mean(axis=1)
        p = float((1 + (null >= d.mean()).sum()) / (1 + N_PERM))
        contrasts.append({
            "contrast": f"donor_prior_transfer_vs_{base}",
            "relative_rmse_reduction": float(rel),
            "ci95": [float(np.quantile(rel_bs, .025)),
                     float(np.quantile(rel_bs, .975))],
            "fraction_cells_improved": float((d > 0).mean()),
            "sign_flip_p_one_sided": p,
        })
        pvals.append(p)
    order = np.argsort(pvals)
    holm = {}
    k = len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (k - rank) * pvals[i])
        running = max(running, adj)
        holm[contrasts[i]['contrast']] = running
    for c in contrasts:
        c['holm_p'] = holm[c['contrast']]

    # --- budgets k>0: intercept recalibration, paired draws
    draw_rng = np.random.default_rng(SEEDS['draws'])
    budget_rows = []
    for k_b in [b for b in BUDGETS if b > 0]:
        for d_i in range(N_DRAWS):
            lab = draw_rng.choice(n, size=k_b, replace=False)
            ev = np.setdiff1d(np.arange(n), lab)
            for m in methods:
                p = pred_df[m].to_numpy().copy()
                delta = (y[lab] - p[lab]).mean() * k_b / (k_b + TAU)
                pr = p[ev] + delta
                budget_rows.append({
                    "budget": k_b, "draw": d_i, "method": m,
                    "rmse_log10_life":
                        float(np.sqrt(np.mean((pr - y[ev]) ** 2)))})
    bud_df = pd.DataFrame(budget_rows)
    bud_path = OUT / 'crosslab_fade_formal_metrics.csv'
    bud_df.to_csv(bud_path, index=False)
    bud_sum = (bud_df.groupby(['budget', 'method'])['rmse_log10_life']
               .mean().unstack().to_dict())

    # --- success gate (primary budget k=0)
    c0 = contrasts[0]
    c_sh = next(c for c in contrasts
                if c['contrast'].endswith('shuffled_donor'))
    c_wc = next(c for c in contrasts
                if c['contrast'].endswith('wrong_chemistry_prior'))
    cov_t = metrics['donor_prior_transfer'].get('coverage90', np.nan)
    cov_b = metrics['recipient_only'].get('coverage90', np.nan)
    gate = {
        "relative_rmse_reduction_at_least_0_10":
            c0['relative_rmse_reduction'] >= 0.10,
        "ci95_lower_above_zero": c0['ci95'][0] > 0,
        "holm_p_below_0_05": c0['holm_p'] < 0.05,
        "margin_over_shuffled_at_least_0_05":
            (metrics['shuffled_donor']['rmse_log10_life']
             - metrics['donor_prior_transfer']['rmse_log10_life'])
            / metrics['shuffled_donor']['rmse_log10_life'] >= 0.05,
        "margin_over_wrong_chem_at_least_0_05":
            (metrics['wrong_chemistry_prior']['rmse_log10_life']
             - metrics['donor_prior_transfer']['rmse_log10_life'])
            / metrics['wrong_chemistry_prior']['rmse_log10_life'] >= 0.05,
        "absolute_r2_above_zero":
            metrics['donor_prior_transfer']['r2_log10_life'] > 0,
        "coverage_not_degraded_more_than_5pp":
            (not np.isfinite(cov_t) or not np.isfinite(cov_b)
             or cov_t >= cov_b - 0.05),
        "fraction_cells_improved_at_least_0_65":
            c0['fraction_cells_improved'] >= 0.65,
    }
    abst = float(pred_df['donor_prior_transfer_abstain'].mean())
    summary = {
        "status": "formal-complete",
        "design": "analysis/crosslab_fade_transfer_design.json",
        "amendment": "analysis/CROSSLAB_FADE_INFRASTRUCTURE_AMENDMENT.md",
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__,
        },
        "donor_valid_cells": arms['donor_prior_transfer'].n_valid,
        "wrong_chem_valid_cells": arms['wrong_chemistry_prior'].n_valid,
        "donor_oof_life_spearman": arms['donor_prior_transfer'].oof_rho,
        "recipient_cells": len(rec),
        "recipient_uncensored_evaluated": n,
        "abstention_rate_transfer": abst,
        "method_metrics_budget0": metrics,
        "contrasts_budget0": contrasts,
        "budget_mean_rmse": {str(kk): {m: float(v[kk]) for m, v in
                                       bud_sum.items()}
                             for kk in [b for b in BUDGETS if b > 0]},
        "success_gate": {"checks": gate, "pass": all(gate.values()),
                         "decision": ("positive-crosslab-parameter-edge"
                                      if all(gate.values())
                                      else "null-harmful-or-incomplete-edge")},
        "predictions_sha256": sha256(pred_path),
        "metrics_sha256": sha256(bud_path),
        "claim_guard": ("A passing result establishes one outcome-blind, "
                        "cross-laboratory, parameter-level borrowing edge for "
                        "LFP capacity fade (same nominal cell model, different "
                        "laboratory). It does not establish universal battery "
                        "transfer, cross-chemistry transfer, or prospective "
                        "cell design."),
    }
    (OUT / 'crosslab_fade_formal_summary.json').write_text(
        json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ('method_metrics_budget0',
                                   'contrasts_budget0',
                                   'budget_mean_rmse')}, indent=2))
    print(json.dumps(summary['contrasts_budget0'], indent=2))
    print(json.dumps(summary['method_metrics_budget0'], indent=2))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True,
                    choices=['audit', 'donor-check', 'formal'])
    a = ap.parse_args()
    if a.stage == 'audit':
        r = stage_audit()
        sys.exit(0 if r['status'] == 'eligible-preoutcome' else 2)
    elif a.stage == 'donor-check':
        r = stage_donor_check()
        sys.exit(0 if r['status'] == 'donor-selfcheck-passed' else 2)
    else:
        stage_formal()
