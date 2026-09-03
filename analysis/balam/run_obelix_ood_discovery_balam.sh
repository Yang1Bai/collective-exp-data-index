#!/bin/bash
#SBATCH --job-name=obelix-ood
#SBATCH --account=ac-sdl
#SBATCH --partition=compute_full_node
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
mkdir -p logs analysis/results
rm -f analysis/results/obelix_ood_discovery_balam_checksums.sha256

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

# Balam's proven full-node pattern couples four GPU allocation units to all 64
# CPU cores.  This simulation is CPU-only; the GPUs remain unused.
export OOD_WORKERS=64
export OOD_BATCH_SIZE=64
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/obelix-joblib-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/obelix_ood_discovery_balam_environment.txt
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

python -u analysis/run_obelix_ood_discovery.py --validate-only
python -u analysis/run_obelix_ood_discovery.py
python -u analysis/verify_obelix_ood_discovery_results.py

test -s analysis/results/obelix_ood_discovery_summary.json
sha256sum \
  analysis/obelix_ood_discovery_design.json \
  analysis/results/obelix_ood_discovery_input.npz \
  analysis/results/obelix_ood_discovery_input_meta.json \
  analysis/results/obelix_ood_discovery_reach.csv \
  analysis/results/obelix_ood_discovery_trajectories.csv \
  analysis/results/obelix_ood_discovery_edges.csv \
  analysis/results/obelix_ood_discovery_bootstrap.csv \
  analysis/results/obelix_ood_discovery_summary.json \
  > analysis/results/obelix_ood_discovery_balam_checksums.sha256
python -u analysis/verify_obelix_ood_discovery_results.py

SUMMARY_SHA256="$(sha256sum analysis/results/obelix_ood_discovery_summary.json | cut -d' ' -f1)"
cat > analysis/results/obelix_ood_discovery_COMPLETE.json <<EOF
{
  "status": "COMPLETE",
  "slurm_job_id": "${SLURM_JOB_ID}",
  "summary_sha256": "${SUMMARY_SHA256}"
}
EOF

tar -czf analysis/results/obelix_ood_discovery_balam_results.tar.gz \
  analysis/obelix_ood_discovery_design.json \
  analysis/results/obelix_ood_discovery_input_meta.json \
  analysis/results/obelix_ood_discovery_reach.csv \
  analysis/results/obelix_ood_discovery_trajectories.csv \
  analysis/results/obelix_ood_discovery_edges.csv \
  analysis/results/obelix_ood_discovery_bootstrap.csv \
  analysis/results/obelix_ood_discovery_summary.json \
  analysis/results/obelix_ood_discovery_balam_environment.txt \
  analysis/results/obelix_ood_discovery_balam_checksums.sha256 \
  analysis/results/obelix_ood_discovery_COMPLETE.json

echo "OBELiX OOD discovery campaign complete: ${SLURM_JOB_ID}"
