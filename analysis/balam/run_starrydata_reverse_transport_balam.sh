#!/bin/bash
#SBATCH --job-name=starry-reverse
#SBATCH --account=ac-sdl
#SBATCH --partition=compute_full_node
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
mkdir -p logs analysis/results
rm -f \
  analysis/results/starrydata_reverse_metrics.csv \
  analysis/results/starrydata_reverse_group_errors.csv \
  analysis/results/starrydata_reverse_exploration.csv \
  analysis/results/starrydata_reverse_hypothesis_tests.csv \
  analysis/results/starrydata_reverse_summary.json \
  analysis/results/starrydata_reverse_COMPLETE.json \
  analysis/results/starrydata_reverse_matched_specificity_metrics.csv \
  analysis/results/starrydata_reverse_matched_specificity_summary.json \
  analysis/results/starrydata_reverse_matched_specificity_COMPLETE.json \
  analysis/results/starrydata_reverse_VALIDATED.json \
  analysis/results/starrydata_reverse_balam_checksums.sha256

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/starry-reverse-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/starrydata_reverse_balam_environment.txt
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
    "slurm_job_node": os.environ.get("SLURMD_NODENAME"),
    "python": platform.python_version(),
    "numpy": numpy.__version__,
    "pandas": pandas.__version__,
    "scipy": scipy.__version__,
    "scikit_learn": sklearn.__version__,
    "joblib": joblib.__version__,
    "workers": 64,
}, indent=2))
PY

python -u analysis/verify_starrydata_reverse_preoutcome.py
python -u analysis/prepare_starrydata_matched_source_controls.py
python -u analysis/run_starrydata_reverse_transport.py --jobs 64
python -u analysis/run_starrydata_matched_specificity.py --jobs 64
python -u analysis/verify_starrydata_reverse_transport_results.py

sha256sum \
  analysis/starrydata_reverse_transport_design.json \
  analysis/starrydata_reverse_transport_implementation.json \
  analysis/STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md \
  analysis/STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md \
  analysis/results/starrydata_reverse_PREOUTCOME.json \
  analysis/results/starrydata_reverse_matched_source_controls.json \
  analysis/results/starrydata_reverse_metrics.csv \
  analysis/results/starrydata_reverse_group_errors.csv \
  analysis/results/starrydata_reverse_exploration.csv \
  analysis/results/starrydata_reverse_hypothesis_tests.csv \
  analysis/results/starrydata_reverse_summary.json \
  analysis/results/starrydata_reverse_COMPLETE.json \
  analysis/results/starrydata_reverse_matched_specificity_metrics.csv \
  analysis/results/starrydata_reverse_matched_specificity_summary.json \
  analysis/results/starrydata_reverse_matched_specificity_COMPLETE.json \
  analysis/results/starrydata_reverse_VALIDATED.json \
  > analysis/results/starrydata_reverse_balam_checksums.sha256

tar -czf analysis/results/starrydata_reverse_balam_results.tar.gz \
  analysis/starrydata_reverse_transport_design.json \
  analysis/starrydata_reverse_transport_implementation.json \
  analysis/STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md \
  analysis/STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md \
  analysis/results/starrydata_reverse_matched_source_controls.csv \
  analysis/results/starrydata_reverse_matched_source_controls.json \
  analysis/results/starrydata_reverse_metrics.csv \
  analysis/results/starrydata_reverse_group_errors.csv \
  analysis/results/starrydata_reverse_exploration.csv \
  analysis/results/starrydata_reverse_hypothesis_tests.csv \
  analysis/results/starrydata_reverse_summary.json \
  analysis/results/starrydata_reverse_COMPLETE.json \
  analysis/results/starrydata_reverse_matched_specificity_metrics.csv \
  analysis/results/starrydata_reverse_matched_specificity_summary.json \
  analysis/results/starrydata_reverse_matched_specificity_COMPLETE.json \
  analysis/results/starrydata_reverse_VALIDATED.json \
  analysis/results/starrydata_reverse_balam_environment.txt \
  analysis/results/starrydata_reverse_balam_checksums.sha256

echo "Starrydata reverse-transport formal benchmark complete: ${SLURM_JOB_ID}"

