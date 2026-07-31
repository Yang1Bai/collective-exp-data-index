#!/bin/bash
#SBATCH --job-name=bandgap-pce
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

result_archive="analysis/results/bandgap_perovskite_pce_ood_balam_results.tar.gz"
checksum_file="analysis/results/bandgap_perovskite_pce_ood_checksums.sha256"

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 1 -type f \
      \( -name 'bandgap_*' -o -name 'bandgap-perovskite-*' \) \
      ! -name "$(basename "$result_archive")" \
      ! -name "$(basename "$checksum_file")" \
      | sort
  )
  input_files=(
    analysis/BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json
    analysis/bandgap_borrowing_common.py
    analysis/audit_bandgap_perovskite_pair.py
    analysis/run_bandgap_external_source_skill.py
    analysis/run_bandgap_perovskite_pce_ood.py
    analysis/verify_bandgap_perovskite_results.py
    analysis/balam/requirements.txt
    analysis/balam/run_bandgap_perovskite_pce_ood_balam.sh
    analysis/balam/prepare_and_submit_bandgap_perovskite_pce_ood.sh
    data/external/bandgap_borrowing/BandgapDatabase1_v2.zip
    data/external/bandgap_borrowing/hybrid_bandgap_210413.zip
    data/external/bandgap_borrowing/hybrid3_bandgap/hybrid3_bandgap_records.csv
    data/external/bandgap_borrowing/hybrid3_bandgap/hybrid3_bandgap_manifest.json
    data/external/bandgap_borrowing/nomad_perovskite_v4/perovskite_solar_cell_recipient.csv
    data/external/bandgap_borrowing/nomad_perovskite_v4/perovskite_solar_cell_recipient_manifest.json
  )
  sha256sum "${input_files[@]}" "${result_files[@]}" \
    > "$checksum_file"
  tar -czf "$result_archive" \
    analysis/BANDGAP_PEROVSKITE_PCE_OOD_DESIGN.json \
    analysis/bandgap_borrowing_common.py \
    analysis/audit_bandgap_perovskite_pair.py \
    analysis/run_bandgap_external_source_skill.py \
    analysis/run_bandgap_perovskite_pce_ood.py \
    analysis/verify_bandgap_perovskite_results.py \
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
export PYTHONHASHSEED=20260728
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/bandgap-pce-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

rm -f \
  analysis/results/bandgap_perovskite_pair_audit.json \
  analysis/results/bandgap_source_cards_strict.csv \
  analysis/results/bandgap_external_source_predictions.csv \
  analysis/results/bandgap_external_source_shuffled_controls.csv \
  analysis/results/bandgap_external_donor_features.csv \
  analysis/results/bandgap_external_source_skill_summary.json \
  analysis/results/bandgap_perovskite_pce_ood_split.json \
  analysis/results/bandgap_perovskite_pce_ood_metrics.csv \
  analysis/results/bandgap_perovskite_pce_ood_predictions.csv \
  analysis/results/bandgap_perovskite_pce_ood_bootstrap.csv \
  analysis/results/bandgap_perovskite_pce_ood_summary.json \
  analysis/results/bandgap_perovskite_pce_ood_environment.json

python - <<'PY' \
  > analysis/results/bandgap_perovskite_pce_ood_environment.json
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
    "recipient_model_workers": -1,
}, indent=2))
PY

python -u analysis/audit_bandgap_perovskite_pair.py
python -u analysis/run_bandgap_external_source_skill.py
python -u analysis/verify_bandgap_perovskite_results.py --source-only
python -u analysis/run_bandgap_perovskite_pce_ood.py
python -u analysis/verify_bandgap_perovskite_results.py

trap - EXIT
package_results
echo "Band-gap-to-perovskite PCE OOD benchmark complete: ${SLURM_JOB_ID}"
