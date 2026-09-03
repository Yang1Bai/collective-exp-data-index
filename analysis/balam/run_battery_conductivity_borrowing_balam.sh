#!/bin/bash
#SBATCH --job-name=battery-borrow
#SBATCH --account=ac-sdl
#SBATCH --partition=compute_full_node
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=128
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
mkdir -p logs analysis/results

result_archive="analysis/results/battery_conductivity_balam_results.tar.gz"
checksum_file="analysis/results/battery_conductivity_checksums.sha256"

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 1 -type f \
      -name 'battery_conductivity_*' \
      ! -name "$(basename "$result_archive")" \
      ! -name "$(basename "$checksum_file")" \
      | sort
  )
  input_files=(
    analysis/BATTERY_CONDUCTIVITY_BORROWING_PROTOCOL.md
    analysis/BATTERY_CONDUCTIVITY_SCHEMA_AMENDMENT.md
    analysis/BATTERY_CONDUCTIVITY_VALUE_SEMANTICS_AMENDMENT.md
    analysis/BATTERY_CONDUCTIVITY_SOURCE_AGGREGATION_AMENDMENT.md
    analysis/battery_conductivity_borrowing_design.json
    analysis/battery_conductivity_implementation.json
    analysis/battery_conductivity_release_freeze.json
    analysis/battery_conductivity_source_freeze.json
    analysis/battery_conductivity_benchmark_freeze.json
    analysis/prepare_battery_conductivity_source_cards.py
    analysis/verify_battery_conductivity_source_cards.py
    analysis/run_battery_conductivity_borrowing.py
    analysis/verify_battery_conductivity_borrowing.py
    analysis/balam/requirements.txt
    analysis/balam/run_battery_conductivity_borrowing_balam.sh
    analysis/balam/prepare_and_submit_battery_conductivity_borrowing.sh
  )
  sha256sum "${input_files[@]}" "${result_files[@]}" \
    > "$checksum_file"
  tar -czf "$result_archive" \
    "${input_files[@]}" \
    "${result_files[@]}" \
    "$checksum_file"
  set -e
}

on_exit() {
  status=$?
  trap - EXIT
  package_results
  exit "$status"
}
trap on_exit EXIT

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=20260727
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/battery-borrow-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

rm -f \
  analysis/results/battery_conductivity_source_cards.csv \
  analysis/results/battery_conductivity_source_summary.json \
  analysis/results/battery_conductivity_metrics.csv \
  analysis/results/battery_conductivity_primary_predictions.csv.gz \
  analysis/results/battery_conductivity_contrasts.csv \
  analysis/results/battery_conductivity_formal_summary.json \
  analysis/results/battery_conductivity_complete.json

python - <<'PY' > analysis/results/battery_conductivity_balam_environment.json
import json
import os
import platform

import joblib
import numpy
import pandas
import scipy
import sklearn

print(json.dumps({
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "node": os.environ.get("SLURMD_NODENAME"),
    "python": platform.python_version(),
    "numpy": numpy.__version__,
    "pandas": pandas.__version__,
    "scipy": scipy.__version__,
    "scikit_learn": sklearn.__version__,
    "joblib": joblib.__version__,
    "allocated_cpus": os.environ.get("SLURM_CPUS_ON_NODE"),
    "source_workers": 32,
    "recipient_workers": 64,
}, indent=2))
PY

python -u analysis/verify_battery_conductivity_formal_release.py
python -u analysis/prepare_battery_conductivity_source_cards.py \
  --workers 32
python -u analysis/verify_battery_conductivity_source_cards.py
python -u analysis/run_battery_conductivity_borrowing.py \
  --workers 64
python -u analysis/verify_battery_conductivity_borrowing.py

trap - EXIT
package_results
echo "Battery conductivity borrowing benchmark complete: ${SLURM_JOB_ID}"

