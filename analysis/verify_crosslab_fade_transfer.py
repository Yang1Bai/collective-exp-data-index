#!/usr/bin/env python3
"""Independent recomputation of the crosslab fade formal summary."""
import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path('/home/claude/results')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


summary = json.loads((OUT / 'crosslab_fade_formal_summary.json').read_text())
pred_path = OUT / 'crosslab_fade_formal_predictions.csv'
met_path = OUT / 'crosslab_fade_formal_metrics.csv'
assert sha256(pred_path) == summary['predictions_sha256'], 'pred hash mismatch'
assert sha256(met_path) == summary['metrics_sha256'], 'metrics hash mismatch'

p = pd.read_csv(pred_path)
y = p['log10_life_true'].to_numpy()
checks = {}
for m, rec in summary['method_metrics_budget0'].items():
    if m == 'oracle_all_recipient':
        continue
    pr = p[m].to_numpy()
    rmse = float(np.sqrt(np.mean((pr - y) ** 2)))
    r2 = float(1 - np.sum((pr - y) ** 2) / np.sum((y - y.mean()) ** 2))
    checks[f'rmse_{m}'] = abs(rmse - rec['rmse_log10_life']) < 1e-9
    checks[f'r2_{m}'] = abs(r2 - rec['r2_log10_life']) < 1e-9

t = p['donor_prior_transfer'].to_numpy()
for c in summary['contrasts_budget0']:
    base = c['contrast'].replace('donor_prior_transfer_vs_', '')
    b = p[base].to_numpy()
    rel = 1 - (np.sqrt(np.mean((t - y) ** 2))
               / np.sqrt(np.mean((b - y) ** 2)))
    checks[f'rel_{base}'] = abs(rel - c['relative_rmse_reduction']) < 1e-9
    frac = float((((b - y) ** 2) > ((t - y) ** 2)).mean())
    checks[f'frac_{base}'] = abs(frac - c['fraction_cells_improved']) < 1e-9

checks['abstention_rate'] = abs(
    p['donor_prior_transfer_abstain'].mean()
    - summary['abstention_rate_transfer']) < 1e-12
checks['n_cells'] = len(p) == summary['recipient_uncensored_evaluated']
gate = summary['success_gate']
checks['gate_pass_consistent'] = gate['pass'] == all(gate['checks'].values())

verified = {
    'status': ('verified-complete'
               if all(checks.values()) else 'verification-failed'),
    'checks': {k: bool(v) for k, v in checks.items()},
    'summary_sha256': sha256(OUT / 'crosslab_fade_formal_summary.json'),
    'predictions_sha256': summary['predictions_sha256'],
    'metrics_sha256': summary['metrics_sha256'],
    'audit_sha256': sha256(OUT / 'crosslab_fade_preoutcome_audit.json'),
    'donor_selfcheck_sha256':
        sha256(OUT / 'crosslab_fade_donor_selfcheck.json'),
    'decision': summary['success_gate']['decision'],
    'abstention_rate_transfer': summary['abstention_rate_transfer'],
    'claim_guard': summary['claim_guard'],
}
(OUT / 'crosslab_fade_VERIFIED.json').write_text(
    json.dumps(verified, indent=2))
print(json.dumps(verified, indent=2))
