#!/bin/bash
#SBATCH --job-name=core-borrow
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

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/core-borrow-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/core_story_balam_environment.txt
import json, os, platform
import joblib, numpy, pandas, scipy, sklearn
print(json.dumps({
  "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
  "node": os.environ.get("SLURMD_NODENAME"),
  "python": platform.python_version(),
  "numpy": numpy.__version__, "pandas": pandas.__version__,
  "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
  "joblib": joblib.__version__, "workers": 64,
}, indent=2))
PY

python -u analysis/verify_starrydata_reverse_preoutcome.py
python -u analysis/prepare_starrydata_matched_source_controls.py
if [[ -f analysis/results/starrydata_reverse_COMPLETE.json \
   && -f analysis/results/starrydata_reverse_matched_specificity_COMPLETE.json ]]; then
  echo "Reusing complete formal Starrydata artifacts from the interrupted combined programme."
else
  python -u analysis/run_starrydata_reverse_transport.py --jobs 64
  python -u analysis/run_starrydata_matched_specificity.py --jobs 64
fi
python -u analysis/verify_starrydata_reverse_transport_results.py

python -u analysis/verify_tri_oer_preoutcome.py
if [[ -f analysis/results/tri_oer_COMPLETE.json ]]; then
  echo "Reusing complete formal TRI OER artifacts from Job 70861."
else
  python -u analysis/run_tri_oer_neighbor.py --jobs 64
fi
python -u analysis/verify_tri_oer_neighbor_results_amended.py
python -u analysis/synthesize_outcome_unseen_validation.py

sha256sum \
  analysis/results/starrydata_reverse_PREOUTCOME.json \
  analysis/results/starrydata_reverse_summary.json \
  analysis/results/starrydata_reverse_VALIDATED.json \
  analysis/results/tri_oer_PREOUTCOME.json \
  analysis/results/tri_oer_summary.json \
  analysis/results/tri_oer_VALIDATED.json \
  analysis/results/outcome_unseen_multi_target_summary.json \
  > analysis/results/core_story_outcome_unseen_checksums.sha256

tar -czf analysis/results/core_story_outcome_unseen_balam_results.tar.gz \
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
  analysis/results/tri_oer_metrics.csv \
  analysis/results/tri_oer_group_errors.csv \
  analysis/results/tri_oer_matched_specificity.csv \
  analysis/results/tri_oer_exploration.csv \
  analysis/results/tri_oer_hypothesis_tests.csv \
  analysis/results/tri_oer_summary.json \
  analysis/results/tri_oer_COMPLETE.json \
  analysis/results/tri_oer_VALIDATED.json \
  analysis/TRI_OER_VERIFIER_AMENDMENT.md \
  analysis/verify_tri_oer_neighbor_results_amended.py \
  analysis/results/outcome_unseen_multi_target_summary.json \
  analysis/results/core_story_balam_environment.txt \
  analysis/results/core_story_outcome_unseen_checksums.sha256

echo "Core-story outcome-unseen programme complete: ${SLURM_JOB_ID}"
