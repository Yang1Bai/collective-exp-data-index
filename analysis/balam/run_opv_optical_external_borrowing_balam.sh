#!/bin/bash
#SBATCH --job-name=opv-optical
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

package_results() {
  set +e
  mapfile -t result_files < <(
    find analysis/results -maxdepth 2 -type f \
      \( -name 'opv_optical_*' \
         -o -path 'analysis/results/opv_optical_source_checkpoints/*' \) \
      ! -name 'opv_optical_external_balam_results.tar.gz' \
      ! -name 'opv_optical_external_checksums.sha256' \
      | sort
  )
  input_files=(
    analysis/opv_optical_external_borrowing_design.json
    analysis/opv_optical_implementation_freeze.json
    analysis/OPV_OPTICAL_EXTERNAL_BORROWING_PROTOCOL.md
    analysis/OPV_OPTICAL_PORTABLE_ZIP_AMENDMENT.md
    analysis/OPV_OPTICAL_PREOUTCOME_IMPLEMENTATION_ALIGNMENT_AMENDMENT.md
    analysis/audit_opv_optical_external_pair.py
    analysis/prepare_opv_optical_draws.py
    analysis/prepare_opv_optical_source_features.py
    analysis/preflight_opv_optical_external_borrowing.py
    analysis/prepare_optical_photocatalysis_donor_features.py
    analysis/pretrain_optical_source_chemprop.py
    analysis/optical_supervised_borrowing_config.json
    analysis/run_opv_optical_external_borrowing.py
    analysis/summarize_opv_optical_external_borrowing.py
    analysis/verify_opv_optical_external_borrowing.py
    analysis/balam/requirements.txt
    analysis/balam/requirements_opv_optical.txt
    analysis/balam/run_opv_optical_external_borrowing_balam.sh
    analysis/balam/prepare_and_submit_opv_optical_external_borrowing.sh
  )
  sha256sum "${input_files[@]}" "${result_files[@]}" \
    > analysis/results/opv_optical_external_checksums.sha256
  tar -czf analysis/results/opv_optical_external_balam_results.tar.gz \
    "${input_files[@]}" \
    "${result_files[@]}" \
    analysis/results/opv_optical_external_checksums.sha256
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
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/opv-optical-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

rm -rf \
  analysis/results/opv_optical_source_checkpoints \
  analysis/results/opv_optical_external_checkpoints_formal_*
rm -f \
  analysis/results/opv_optical_global_source_oof.csv \
  analysis/results/opv_optical_source_features.csv \
  analysis/results/opv_optical_source_summary.json \
  analysis/results/opv_optical_external_formal_metrics.csv \
  analysis/results/opv_optical_external_formal_primary_predictions.csv \
  analysis/results/opv_optical_external_formal_run.json \
  analysis/results/opv_optical_external_formal_summary.json \
  analysis/results/opv_optical_external_formal_VERIFIED.json

python - <<'PY' > analysis/results/opv_optical_external_balam_environment.json
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

python -u analysis/audit_opv_optical_external_pair.py
python -u analysis/prepare_opv_optical_draws.py
python -u analysis/preflight_opv_optical_external_borrowing.py \
  --stage audited
python -u analysis/prepare_opv_optical_source_features.py --device cuda
python -u analysis/preflight_opv_optical_external_borrowing.py \
  --stage source-ready
python -u analysis/run_opv_optical_external_borrowing.py \
  --formal --jobs 64
python -u analysis/summarize_opv_optical_external_borrowing.py \
  --mode formal
python -u analysis/verify_opv_optical_external_borrowing.py \
  --mode formal

trap - EXIT
package_results
echo "Formal optical-to-OPV borrowing benchmark complete: ${SLURM_JOB_ID}"
