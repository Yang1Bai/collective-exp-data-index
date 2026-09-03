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
python -m pip install -r analysis/balam/requirements_optical_supervised.txt
python - <<'PY'
import chemprop
import joblib
import lightning
import numpy
import pandas
import rdkit
import scipy
import sklearn
import torch

print("Focused optical environment ready")
print("torch", torch.__version__, "module_import_ok")
print("chemprop", chemprop.__version__)
print("lightning", lightning.__version__)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scikit-learn", sklearn.__version__)
print("rdkit", rdkit.__version__)
print("joblib", joblib.__version__)
PY

mkdir -p logs analysis/results
if [[ "${OPTICAL_RESUME_FROM_SOURCE:-0}" == "1" ]]; then
  job_id="$(
    sbatch --parsable \
      --export=ALL,OPTICAL_RESUME_FROM_SOURCE=1 \
      analysis/balam/run_optical_supervised_borrowing_balam.sh
  )"
else
  job_id="$(
    sbatch --parsable analysis/balam/run_optical_supervised_borrowing_balam.sh
  )"
fi
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"
