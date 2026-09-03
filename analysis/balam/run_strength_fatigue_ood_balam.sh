#!/bin/bash
#SBATCH --job-name=str-fatigue
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

result_archive="analysis/results/strength_fatigue_ood_balam_results.tar.gz"
checksum_file="analysis/results/strength_fatigue_ood_checksums.sha256"

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 1 -type f \
      -name 'strength_fatigue_*' \
      ! -name "$(basename "$result_archive")" \
      ! -name "$(basename "$checksum_file")" \
      | sort
  )
  input_files=(
    analysis/strength_to_fatigue_ood_design.json
    analysis/strength_fatigue_implementation.json
    analysis/run_strength_to_fatigue_ood.py
    analysis/verify_strength_to_fatigue_results.py
    analysis/common.py
    analysis/balam/run_strength_fatigue_ood_balam.sh
    analysis/balam/prepare_and_submit_strength_fatigue_ood.sh
  )
  sha256sum "${input_files[@]}" "${result_files[@]}" > "$checksum_file"
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
export PYTHONHASHSEED=20260729
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/str-fatigue-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

rm -f \
  analysis/results/strength_fatigue_source_cards.csv \
  analysis/results/strength_fatigue_shuffled_source_cards.csv \
  analysis/results/strength_fatigue_source_summary.json \
  analysis/results/strength_fatigue_split_audit.csv \
  analysis/results/strength_fatigue_metrics.csv \
  analysis/results/strength_fatigue_predictions.csv \
  analysis/results/strength_fatigue_bootstrap.csv \
  analysis/results/strength_fatigue_summary.json \
  analysis/results/strength_fatigue_environment.json \
  analysis/results/strength_fatigue_VERIFIED.json

python -u analysis/run_strength_to_fatigue_ood.py --jobs 96
python -u analysis/verify_strength_to_fatigue_results.py

trap - EXIT
package_results
echo "Strength-to-fatigue OOD benchmark complete: ${SLURM_JOB_ID}"
