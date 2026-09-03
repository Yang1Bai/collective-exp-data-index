#!/bin/bash
#SBATCH --job-name=optical-borrow
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

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 2 -type f \
      \( -name 'optical_supervised_*' -o -name '*.pt' -o -name 'optical_photocatalysis_donor_features.csv' \) \
      ! -name 'optical_supervised_borrowing_balam_results.tar.gz' \
      ! -name 'optical_supervised_borrowing_checksums.sha256' \
      | sort
  )
  input_files=(
    analysis/optical_photocatalysis_borrowing_design.json
    analysis/optical_supervised_borrowing_config.json
    analysis/OPTICAL_FOCUSED_METHOD_DECISION.md
    analysis/OPTICAL_SUPERVISED_BORROWING_PROTOCOL.md
    analysis/OPTICAL_SUPERVISED_VERIFIER_AMENDMENT.md
    analysis/prepare_optical_supervised_borrowing_scopes.py
    analysis/pretrain_optical_source_chemprop.py
    analysis/verify_optical_supervised_source_encoder.py
    analysis/run_optical_supervised_borrowing_development.py
    analysis/verify_optical_supervised_borrowing_development.py
  )
  sha256sum "${input_files[@]}" "${result_files[@]}" \
    > analysis/results/optical_supervised_borrowing_checksums.sha256
  tar -czf analysis/results/optical_supervised_borrowing_balam_results.tar.gz \
    "${input_files[@]}" \
    "${result_files[@]}" \
    analysis/results/optical_supervised_borrowing_checksums.sha256
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
module load cuda/12.3.1
module load python/3.11.5
module load pytorch/2.1.2
source .venv-optical-supervised/bin/activate

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=20260726
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/optical-borrow-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

if [[ "${OPTICAL_RESUME_FROM_SOURCE:-0}" != "1" ]]; then
  rm -rf analysis/results/optical_supervised_source_checkpoints
  rm -f \
    analysis/results/optical_supervised_source_embeddings.npz \
    analysis/results/optical_supervised_source_oof.csv \
    analysis/results/optical_supervised_source_summary.json \
    analysis/results/optical_supervised_source_VERIFIED.json
fi
rm -f \
  analysis/results/optical_supervised_borrowing_metrics.csv \
  analysis/results/optical_supervised_borrowing_contrasts.csv \
  analysis/results/optical_supervised_borrowing_summary.json \
  analysis/results/optical_supervised_borrowing_release.json \
  analysis/results/optical_supervised_borrowing_VERIFIED.json

python - <<'PY' > analysis/results/optical_supervised_borrowing_balam_environment.json
import json
import os
import platform
import subprocess

import chemprop
import joblib
import lightning
import numpy
import pandas
import rdkit
import scipy
import sklearn
import torch

gpu = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
print(json.dumps({
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "node": os.environ.get("SLURMD_NODENAME"),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "chemprop": chemprop.__version__,
    "lightning": lightning.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_runtime": torch.version.cuda,
    "gpu": gpu,
    "numpy": numpy.__version__,
    "pandas": pandas.__version__,
    "rdkit": rdkit.__version__,
    "scipy": scipy.__version__,
    "scikit_learn": sklearn.__version__,
    "joblib": joblib.__version__,
    "allocated_cpus": os.environ.get("SLURM_CPUS_ON_NODE"),
}, indent=2))
if not torch.cuda.is_available():
    raise SystemExit("Balam GPU allocation is not visible to PyTorch")
PY

python -u analysis/prepare_optical_supervised_borrowing_scopes.py --jobs 24

if [[ "${OPTICAL_RESUME_FROM_SOURCE:-0}" == "1" ]]; then
  echo "Reusing hash-anchored source artifacts from the completed source-training stage."
  required_source_artifacts=(
    analysis/results/optical_supervised_source_embeddings.npz
    analysis/results/optical_supervised_source_oof.csv
    analysis/results/optical_supervised_source_summary.json
    analysis/results/optical_supervised_source_checkpoints
  )
  for artifact in "${required_source_artifacts[@]}"; do
    if [[ ! -e "$artifact" ]]; then
      echo "Missing source artifact required for resume: $artifact" >&2
      exit 1
    fi
  done
  source_status=0
else
  set +e
  python -u analysis/pretrain_optical_source_chemprop.py --device cuda
  source_status=$?
  set -e
fi

if [[ "$source_status" -eq 0 ]]; then
  python -u analysis/verify_optical_supervised_source_encoder.py
  python -u analysis/run_optical_supervised_borrowing_development.py --jobs 28
  python -u analysis/verify_optical_supervised_borrowing_development.py
fi

if [[ "$source_status" -ne 0 ]]; then
  echo "Source representation gate failed; diagnostics were packaged."
  exit "$source_status"
fi

trap - EXIT
package_results
echo "Focused optical borrowing complete: ${SLURM_JOB_ID}"
