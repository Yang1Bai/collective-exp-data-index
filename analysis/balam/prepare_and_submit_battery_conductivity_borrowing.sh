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

mkdir -p logs analysis/results
.venv-balam/bin/python -m py_compile \
  analysis/prepare_battery_conductivity_source_cards.py \
  analysis/verify_battery_conductivity_source_cards.py \
  analysis/run_battery_conductivity_borrowing.py \
  analysis/verify_battery_conductivity_borrowing.py
.venv-balam/bin/python analysis/verify_battery_conductivity_formal_release.py

job_id="$(
  sbatch --parsable \
    analysis/balam/run_battery_conductivity_borrowing_balam.sh
)"
echo "BALAM_JOB_ID=${job_id}"
squeue -j "$job_id"

