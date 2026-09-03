#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${SCRATCH:-/scratch/yangbai}/collective-exp-ood"
cd "$PROJECT_ROOT"
module --force purge
module load BalamEnv
module load cuda/12.3.1
module load python/3.11.5
module load pytorch/2.1.2

if [[ ! -x .venv-optical-supervised/bin/python ]]; then
  python -m venv --system-site-packages .venv-optical-supervised
fi
source .venv-optical-supervised/bin/activate
python -m pip install -r analysis/balam/requirements_opv_optical.txt
python - <<'PY'
import chemprop
import hashlib
import joblib
import json
import lightning
import numpy
import pandas
from pathlib import Path
import rdkit
import scipy
import sklearn
import torch
import zipfile

print("OPV optical-borrowing environment ready")
print("torch", torch.__version__, "module_import_ok")
print("chemprop", chemprop.__version__)
print("lightning", lightning.__version__)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scikit-learn", sklearn.__version__)
print("rdkit", rdkit.__version__)
print("joblib", joblib.__version__)

root = Path.cwd()
target = root / "data/external/opv_borrowing/opvdb.zip"
design = json.loads(
    (root / "analysis/opv_optical_external_borrowing_design.json").read_text()
)
target_hash = hashlib.sha256(target.read_bytes()).hexdigest()
if target_hash != design["target"]["required_archive_sha256"]:
    raise SystemExit("Packaged OPV archive hash does not match the freeze")
expected = design["target"]["member"].replace("\\", "/")
with zipfile.ZipFile(target) as archive:
    normalized = {
        name.replace("\\", "/"): name for name in archive.namelist()
    }
if expected not in normalized:
    raise SystemExit(
        f"Packaged OPV archive lacks the normalized member {expected!r}"
    )
print("OPV archive preflight", target_hash, normalized[expected])
PY

python -u analysis/preflight_opv_optical_external_borrowing.py \
  --stage package \
  --archive opv_optical_external_balam_package.tar.gz

mkdir -p logs analysis/results
job_id="$(
  sbatch --parsable \
    analysis/balam/run_opv_optical_external_borrowing_balam.sh
)"
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"
