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
  analysis/run_strength_to_fatigue_ood.py \
  analysis/verify_strength_to_fatigue_results.py \
  analysis/common.py

.venv-balam/bin/python analysis/run_strength_to_fatigue_ood.py --validate-only

job_id=$(
  sbatch --parsable analysis/balam/run_strength_fatigue_ood_balam.sh
)
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"
