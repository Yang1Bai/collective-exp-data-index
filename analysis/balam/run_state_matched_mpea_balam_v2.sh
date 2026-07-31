#!/bin/bash
#SBATCH --job-name=state-mpea-v2
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
export JOBLIB_TEMP_FOLDER="${SLURM_TMPDIR:-/tmp}/state-mpea-v2-${SLURM_JOB_ID}"
mkdir -p "$JOBLIB_TEMP_FOLDER"

python - <<'PY' > analysis/results/state_matched_mpea_balam_v2_environment.txt
import json, os, platform
import joblib, numpy, pandas, scipy, sklearn
print(json.dumps({
  "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
  "node": os.environ.get("SLURMD_NODENAME"),
  "python": platform.python_version(),
  "numpy": numpy.__version__,
  "pandas": pandas.__version__,
  "scipy": scipy.__version__,
  "scikit_learn": sklearn.__version__,
  "joblib": joblib.__version__,
  "cpus": int(os.environ.get("SLURM_CPUS_PER_TASK", "1")),
}, indent=2))
PY

python -u analysis/run_state_matched_mpea_borrowing_screen.py \
  --design-path analysis/state_matched_mpea_balam_design_v2.json \
  --output-prefix state_matched_mpea_balam_v2 \
  --overwrite
python -u analysis/analyze_state_matched_mpea_balam_bootstrap.py \
  --design-path analysis/state_matched_mpea_balam_design_v2.json \
  --input-prefix state_matched_mpea_balam_v2 \
  --output-prefix state_matched_mpea_balam_v2
python -u analysis/verify_state_matched_mpea_balam.py \
  --design-path analysis/state_matched_mpea_balam_design_v2.json \
  --input-prefix state_matched_mpea_balam_v2 \
  --output-prefix state_matched_mpea_balam_v2

sha256sum \
  analysis/state_matched_mpea_balam_design_v2.json \
  analysis/results/state_matched_mpea_balam_v2_screen.csv \
  analysis/results/state_matched_mpea_balam_v2_predictions.csv \
  analysis/results/state_matched_mpea_balam_v2_summary.json \
  analysis/results/state_matched_mpea_balam_v2_bootstrap.csv.gz \
  analysis/results/state_matched_mpea_balam_v2_bootstrap_summary.json \
  analysis/results/state_matched_mpea_balam_v2_VERIFIED.json \
  > analysis/results/state_matched_mpea_balam_v2_checksums.sha256

tar -czf analysis/results/state_matched_mpea_balam_v2_results.tar.gz \
  analysis/STATE_MATCHED_MPEA_BORROWING_PROTOCOL.md \
  analysis/STATE_MATCHED_MPEA_CONTROL_AMENDMENT_V2.md \
  analysis/state_matched_mpea_balam_design_v2.json \
  analysis/run_state_matched_mpea_borrowing_screen.py \
  analysis/analyze_state_matched_mpea_balam_bootstrap.py \
  analysis/verify_state_matched_mpea_balam.py \
  analysis/results/state_matched_mpea_balam_v2_screen.csv \
  analysis/results/state_matched_mpea_balam_v2_predictions.csv \
  analysis/results/state_matched_mpea_balam_v2_summary.json \
  analysis/results/state_matched_mpea_balam_v2_bootstrap.csv.gz \
  analysis/results/state_matched_mpea_balam_v2_bootstrap_summary.json \
  analysis/results/state_matched_mpea_balam_v2_VERIFIED.json \
  analysis/results/state_matched_mpea_balam_v2_environment.txt \
  analysis/results/state_matched_mpea_balam_v2_checksums.sha256

echo "State-matched MPEA V2 control-correction run complete: ${SLURM_JOB_ID}"
