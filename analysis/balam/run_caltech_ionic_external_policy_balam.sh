#!/bin/bash
#SBATCH --job-name=caltech-borrow
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
  analysis/results/caltech_ionic_external_policy_balam_checksums.sha256 \
  analysis/results/caltech_ionic_external_policy_COMPLETE.json

module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

export CALTECH_WORKERS=64
export CALTECH_BATCH_SIZE=64
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/caltech-borrow-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/caltech_ionic_external_policy_balam_environment.txt
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
    "caltech_workers": os.environ.get("CALTECH_WORKERS"),
}, indent=2))
PY

python -u analysis/audit_caltech_ionic_external_target.py
python -u analysis/run_caltech_ionic_external_policy.py --validate-only
python -u analysis/run_caltech_ionic_external_policy.py

sha256sum \
  analysis/caltech_ionic_external_policy_design.json \
  analysis/caltech_ionic_external_policy_implementation.json \
  analysis/CALTECH_IONIC_SCHEMA_AMENDMENT.md \
  analysis/CALTECH_IONIC_INFERENCE_AMENDMENT.md \
  analysis/CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md \
  analysis/CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md \
  analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md \
  analysis/results/caltech_ionic_external_audit.json \
  data/external/caltech_ionic/ionic_conductivity_database.csv \
  data/collective.sqlite \
  analysis/results/caltech_ionic_external_policy_trajectories.csv \
  analysis/results/caltech_ionic_external_policy_gates.csv \
  analysis/results/caltech_ionic_external_policy_utility.csv \
  analysis/results/caltech_ionic_external_policy_gate_summary.csv \
  analysis/results/caltech_ionic_external_policy_source_quality.csv \
  analysis/results/caltech_ionic_external_policy_contrasts.csv \
  analysis/results/caltech_ionic_external_policy_summary.json \
  > analysis/results/caltech_ionic_external_policy_balam_checksums.sha256

SUMMARY_SHA256="$(sha256sum analysis/results/caltech_ionic_external_policy_summary.json | cut -d' ' -f1)"
cat > analysis/results/caltech_ionic_external_policy_COMPLETE.json <<EOF
{
  "status": "COMPLETE",
  "slurm_job_id": "${SLURM_JOB_ID}",
  "summary_sha256": "${SUMMARY_SHA256}"
}
EOF

python -u analysis/verify_caltech_ionic_external_policy_results.py

tar -czf analysis/results/caltech_ionic_external_policy_balam_results.tar.gz \
  analysis/caltech_ionic_external_policy_design.json \
  analysis/caltech_ionic_external_policy_implementation.json \
  analysis/CALTECH_IONIC_SCHEMA_AMENDMENT.md \
  analysis/CALTECH_IONIC_INFERENCE_AMENDMENT.md \
  analysis/CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md \
  analysis/CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md \
  analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md \
  analysis/results/caltech_ionic_external_audit.json \
  analysis/results/caltech_ionic_external_policy_trajectories.csv \
  analysis/results/caltech_ionic_external_policy_gates.csv \
  analysis/results/caltech_ionic_external_policy_utility.csv \
  analysis/results/caltech_ionic_external_policy_gate_summary.csv \
  analysis/results/caltech_ionic_external_policy_source_quality.csv \
  analysis/results/caltech_ionic_external_policy_contrasts.csv \
  analysis/results/caltech_ionic_external_policy_summary.json \
  analysis/results/caltech_ionic_external_policy_balam_environment.txt \
  analysis/results/caltech_ionic_external_policy_balam_checksums.sha256 \
  analysis/results/caltech_ionic_external_policy_COMPLETE.json

echo "Caltech external borrowing benchmark complete: ${SLURM_JOB_ID}"
