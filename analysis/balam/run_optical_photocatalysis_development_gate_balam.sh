#!/bin/bash
#SBATCH --job-name=optical-dev
#SBATCH --account=ac-sdl
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=32
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
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/optical-dev-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/optical_photocatalysis_development_balam_environment.json
import json
import os
import platform

import joblib
import numpy
import pandas
import rdkit
import scipy
import sklearn

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
    "allocated_cpus": os.environ.get("SLURM_CPUS_ON_NODE"),
}, indent=2))
PY

python -u analysis/verify_optical_photocatalysis_source_features.py
python -u analysis/run_optical_photocatalysis_development_gate.py --jobs 32
python -u analysis/verify_optical_photocatalysis_development_gate.py

sha256sum \
  analysis/optical_photocatalysis_borrowing_design.json \
  analysis/optical_photocatalysis_development_gate_config.json \
  analysis/OPTICAL_PHOTOCATALYSIS_SOURCE_VERIFIER_AMENDMENT.md \
  analysis/results/optical_photocatalysis_source_skill.json \
  analysis/results/optical_photocatalysis_donor_features.csv \
  analysis/results/optical_photocatalysis_development_draws.csv \
  analysis/results/optical_photocatalysis_development_draws_manifest.json \
  analysis/results/optical_photocatalysis_development_metrics.csv \
  analysis/results/optical_photocatalysis_development_gate.json \
  analysis/results/optical_photocatalysis_development_gate_VERIFIED.json \
  analysis/results/optical_photocatalysis_development_balam_environment.json \
  > analysis/results/optical_photocatalysis_development_checksums.sha256

tar -czf analysis/results/optical_photocatalysis_development_balam_results.tar.gz \
  analysis/optical_photocatalysis_borrowing_design.json \
  analysis/optical_photocatalysis_development_gate_config.json \
  analysis/OPTICAL_PHOTOCATALYSIS_SOURCE_VERIFIER_AMENDMENT.md \
  analysis/run_optical_photocatalysis_development_gate.py \
  analysis/verify_optical_photocatalysis_development_gate.py \
  analysis/results/optical_photocatalysis_source_skill.json \
  analysis/results/optical_photocatalysis_source_features_VERIFIED.json \
  analysis/results/optical_photocatalysis_donor_features.csv \
  analysis/results/optical_photocatalysis_development_draws.csv \
  analysis/results/optical_photocatalysis_development_draws_manifest.json \
  analysis/results/optical_photocatalysis_development_metrics.csv \
  analysis/results/optical_photocatalysis_development_gate.json \
  analysis/results/optical_photocatalysis_development_gate_VERIFIED.json \
  analysis/results/optical_photocatalysis_development_balam_environment.json \
  analysis/results/optical_photocatalysis_development_checksums.sha256

echo "Optical development gate complete: ${SLURM_JOB_ID}"
