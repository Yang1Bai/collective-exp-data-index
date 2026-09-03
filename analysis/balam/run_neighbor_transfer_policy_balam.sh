#!/bin/bash
#SBATCH --job-name=neighbor-policy
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
rm -f analysis/results/neighbor_transfer_policy_balam_checksums.sha256

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

# Balam attaches 32 logical CPU threads to each GPU.  A four-GPU full node
# therefore exposes 64 physical cores; use one process per physical core.
# CPU and MPI directives are intentionally omitted so Slurm can apply the
# cluster's per-GPU CPU mapping without the partial-allocation warning.
export OOD_WORKERS=64
export OOD_BATCH_SIZE=64
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/neighbor-policy-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/neighbor_transfer_policy_balam_environment.txt
import json
import os
import platform

import joblib
import numpy
import pandas
import sklearn

print(json.dumps({
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "slurm_job_node": os.environ.get("SLURMD_NODENAME"),
    "python": platform.python_version(),
    "numpy": numpy.__version__,
    "pandas": pandas.__version__,
    "scikit_learn": sklearn.__version__,
    "joblib": joblib.__version__,
    "ood_workers": os.environ.get("OOD_WORKERS"),
}, indent=2))
PY

python -u analysis/run_neighbor_transfer_policy_benchmark.py --validate-only
python -u analysis/run_neighbor_transfer_policy_benchmark.py
python -u analysis/verify_neighbor_transfer_policy_results.py

sha256sum \
  analysis/neighbor_transfer_policy_design.json \
  analysis/results/obelix_ood_discovery_input.npz \
  analysis/results/obelix_ood_discovery_input_meta.json \
  analysis/results/neighbor_transfer_policy_reach.csv \
  analysis/results/neighbor_transfer_policy_trajectories.csv \
  analysis/results/neighbor_transfer_policy_contrasts.csv \
  analysis/results/neighbor_transfer_policy_bootstrap.csv \
  analysis/results/neighbor_transfer_policy_secondary_utility.csv \
  analysis/results/neighbor_transfer_policy_summary.json \
  > analysis/results/neighbor_transfer_policy_balam_checksums.sha256

SUMMARY_SHA256="$(sha256sum analysis/results/neighbor_transfer_policy_summary.json | cut -d' ' -f1)"
cat > analysis/results/neighbor_transfer_policy_COMPLETE.json <<EOF
{
  "status": "COMPLETE",
  "slurm_job_id": "${SLURM_JOB_ID}",
  "summary_sha256": "${SUMMARY_SHA256}"
}
EOF
python -u analysis/verify_neighbor_transfer_policy_results.py

tar -czf analysis/results/neighbor_transfer_policy_balam_results.tar.gz \
  analysis/neighbor_transfer_policy_design.json \
  analysis/results/obelix_ood_discovery_input_meta.json \
  analysis/results/neighbor_transfer_policy_reach.csv \
  analysis/results/neighbor_transfer_policy_trajectories.csv \
  analysis/results/neighbor_transfer_policy_contrasts.csv \
  analysis/results/neighbor_transfer_policy_bootstrap.csv \
  analysis/results/neighbor_transfer_policy_secondary_utility.csv \
  analysis/results/neighbor_transfer_policy_summary.json \
  analysis/results/neighbor_transfer_policy_balam_environment.txt \
  analysis/results/neighbor_transfer_policy_balam_checksums.sha256 \
  analysis/results/neighbor_transfer_policy_COMPLETE.json

echo "Neighborhood-transfer policy benchmark complete: ${SLURM_JOB_ID}"
