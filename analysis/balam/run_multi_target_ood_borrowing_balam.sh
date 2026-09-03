#!/bin/bash
#SBATCH --job-name=multi-ood-map
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
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/multi-ood-map-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/multi_target_ood_balam_environment.txt
import json, os, platform
import joblib, numpy, pandas, rdkit, scipy, sklearn
print(json.dumps({
  "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
  "node": os.environ.get("SLURMD_NODENAME"),
  "python": platform.python_version(),
  "numpy": numpy.__version__,
  "pandas": pandas.__version__,
  "rdkit": rdkit.__version__,
  "scipy": scipy.__version__,
  "scikit_learn": sklearn.__version__,
  "joblib": joblib.__version__,
  "workers": 64,
}, indent=2))
PY

python -u analysis/run_multi_target_ood_borrowing.py --jobs 64
python -u analysis/verify_multi_target_ood_borrowing.py

sha256sum \
  analysis/multi_target_ood_borrowing_design.json \
  analysis/results/multi_target_ood_strata.csv \
  analysis/results/multi_target_ood_source_quality.csv \
  analysis/results/multi_target_ood_metrics.csv \
  analysis/results/multi_target_ood_contrasts.csv \
  analysis/results/multi_target_ood_group_errors.csv \
  analysis/results/multi_target_ood_edge_summary.csv \
  analysis/results/multi_target_ood_target_summary.csv \
  analysis/results/multi_target_ood_summary.json \
  analysis/results/multi_target_ood_COMPLETE.json \
  analysis/results/multi_target_ood_VERIFIED.json \
  > analysis/results/multi_target_ood_checksums.sha256

tar -czf analysis/results/multi_target_ood_balam_results.tar.gz \
  analysis/MULTI_TARGET_OOD_BORROWING_PROTOCOL.md \
  analysis/multi_target_ood_borrowing_design.json \
  analysis/run_multi_target_ood_borrowing.py \
  analysis/verify_multi_target_ood_borrowing.py \
  analysis/results/multi_target_ood_strata.csv \
  analysis/results/multi_target_ood_source_quality.csv \
  analysis/results/multi_target_ood_metrics.csv \
  analysis/results/multi_target_ood_contrasts.csv \
  analysis/results/multi_target_ood_group_errors.csv \
  analysis/results/multi_target_ood_edge_summary.csv \
  analysis/results/multi_target_ood_target_summary.csv \
  analysis/results/multi_target_ood_summary.json \
  analysis/results/multi_target_ood_COMPLETE.json \
  analysis/results/multi_target_ood_VERIFIED.json \
  analysis/results/multi_target_ood_balam_environment.txt \
  analysis/results/multi_target_ood_checksums.sha256

echo "Multi-target OOD borrowing benchmark complete: ${SLURM_JOB_ID}"
