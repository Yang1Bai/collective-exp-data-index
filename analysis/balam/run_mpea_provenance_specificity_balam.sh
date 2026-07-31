#!/bin/bash
#SBATCH --job-name=mpea-prov2
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

result_archive="analysis/results/mpea_provenance_specificity_balam_results.tar.gz"
checksum_file="analysis/results/mpea_provenance_specificity_checksums.sha256"

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 1 -type f \
      \( -name 'mpea_provenance_specificity_*' \
         -o -name 'caltech_static_ranking_empirical_null*' \) \
      ! -name "$(basename "$result_archive")" \
      ! -name "$(basename "$checksum_file")" \
      | sort
  )
  input_files=(
    analysis/MPEA_PROVENANCE_SPECIFICITY_PROTOCOL.md
    analysis/mpea_provenance_specificity_design.json
    analysis/mpea_provenance_specificity_implementation.sha256
    analysis/run_mpea_provenance_specificity.py
    analysis/analyze_mpea_provenance_specificity.py
    analysis/verify_mpea_provenance_specificity.py
    analysis/recompute_caltech_static_ranking_inference.py
    analysis/verify_caltech_static_ranking_inference.py
    analysis/balam/run_mpea_provenance_specificity_balam.sh
    analysis/balam/prepare_and_submit_mpea_provenance_specificity.sh
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
export PYTHONHASHSEED=20260727
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/mpea-prov-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

sha256sum -c analysis/mpea_provenance_specificity_implementation.sha256

rm -f \
  analysis/results/mpea_provenance_specificity_metrics.csv \
  analysis/results/mpea_provenance_specificity_predictions.csv.gz \
  analysis/results/mpea_provenance_specificity_audit.json \
  analysis/results/mpea_provenance_specificity_complete.json \
  analysis/results/mpea_provenance_specificity_inference_summary.json \
  analysis/results/mpea_provenance_specificity_VERIFIED.json \
  analysis/results/mpea_provenance_specificity_balam_environment.json \
  analysis/results/caltech_static_ranking_empirical_null.csv \
  analysis/results/caltech_static_ranking_empirical_null_summary.json \
  analysis/results/caltech_static_ranking_empirical_null_VERIFIED.json

python - <<'PY' > analysis/results/mpea_provenance_specificity_balam_environment.json
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
    "tree_estimators": 320,
    "target_repeats": 30,
}, indent=2))
PY

# Reproduce the zero-compute corrective analysis in the remote environment.
python -u analysis/recompute_caltech_static_ranking_inference.py
python -u analysis/verify_caltech_static_ranking_inference.py \
  > analysis/results/caltech_static_ranking_empirical_null_VERIFIED.json
cat analysis/results/caltech_static_ranking_empirical_null_VERIFIED.json

# Frozen MPEA strengthening experiment.
python -u analysis/run_mpea_provenance_specificity.py \
  --design-path analysis/mpea_provenance_specificity_design.json \
  --output-prefix mpea_provenance_specificity \
  --overwrite
python -u analysis/analyze_mpea_provenance_specificity.py \
  --design-path analysis/mpea_provenance_specificity_design.json \
  --output-prefix mpea_provenance_specificity \
  --overwrite
python -u analysis/verify_mpea_provenance_specificity.py \
  --design-path analysis/mpea_provenance_specificity_design.json \
  --output-prefix mpea_provenance_specificity \
  --require-inference \
  > analysis/results/mpea_provenance_specificity_VERIFIED.json
cat analysis/results/mpea_provenance_specificity_VERIFIED.json

trap - EXIT
package_results
echo "MPEA provenance-specificity benchmark complete: ${SLURM_JOB_ID}"
