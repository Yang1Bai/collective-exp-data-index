#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../.."
mkdir -p logs analysis/results

module --force purge
module load BalamEnv
module load python/3.11.5

if [[ ! -x .venv-balam/bin/python ]]; then
  python -m venv .venv-balam
fi
.venv-balam/bin/python -m pip install --upgrade pip
.venv-balam/bin/python -m pip install -r analysis/balam/requirements.txt

.venv-balam/bin/python -m py_compile \
  analysis/bandgap_borrowing_common.py \
  analysis/audit_bandgap_perovskite_pair.py \
  analysis/run_bandgap_external_source_skill.py \
  analysis/run_bandgap_perovskite_pce_ood.py \
  analysis/verify_bandgap_perovskite_results.py

.venv-balam/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path

design = Path("analysis/BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json")
expected = "8d370d238e5eb2072d0625b12ca2b06d7e1d18d2c63e234f87f698d3867294e0"
actual = hashlib.sha256(design.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit(f"Frozen PCE design hash changed: {actual}")

manifest_path = Path(
    "data/external/bandgap_borrowing/nomad_perovskite_v4/"
    "perovskite_solar_cell_recipient_manifest.json"
)
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("status") != "complete" or manifest.get("rows") != 43108:
    raise SystemExit("Recipient snapshot is incomplete")
csv_path = Path(
    "data/external/bandgap_borrowing/nomad_perovskite_v4/"
    "perovskite_solar_cell_recipient.csv"
)
csv_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
if csv_hash != manifest.get("csv_sha256"):
    raise SystemExit("Recipient CSV hash does not match manifest")
print(json.dumps({
    "status": "preflight-passed",
    "design_sha256": actual,
    "recipient_rows": manifest["rows"],
    "recipient_csv_sha256": csv_hash,
}, indent=2))
PY

job_id=$(
  sbatch --parsable \
    analysis/balam/run_bandgap_perovskite_pce_ood_balam.sh
)
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"
