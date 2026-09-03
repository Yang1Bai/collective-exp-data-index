#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${SCRATCH:-/scratch/yangbai}/collective-exp-ood"
cd "$PROJECT_ROOT"
module --force purge
module load BalamEnv
module load python/3.11.5

if [[ ! -x .venv-balam/bin/python ]]; then
  python -m venv .venv-balam
fi
.venv-balam/bin/python -m pip install --upgrade pip
.venv-balam/bin/python -m pip install -r analysis/balam/requirements.txt
.venv-balam/bin/python - <<'PY'
import joblib
import numpy
import pandas
import sklearn

print("Balam environment ready")
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scikit-learn", sklearn.__version__)
print("joblib", joblib.__version__)
PY

mkdir -p logs analysis/results
job_id="$(sbatch --parsable analysis/balam/run_obelix_ood_discovery_balam.sh)"
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"
