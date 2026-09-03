#!/bin/bash
#SBATCH --job-name=caltech-verify
#SBATCH --account=ac-sdl
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"
module --force purge
module load BalamEnv
module load python/3.11.5
source .venv-balam/bin/activate

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

python -u analysis/verify_caltech_ionic_external_policy_results.py

VERIFIER_SHA256="$(sha256sum analysis/verify_caltech_ionic_external_policy_results.py | cut -d' ' -f1)"
VERIFIER_AMENDMENT_SHA256="$(sha256sum analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md | cut -d' ' -f1)"
REMOTE_AMENDMENT_SHA256="$(sha256sum analysis/CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md | cut -d' ' -f1)"
CHECKSUMS_SHA256="$(sha256sum analysis/results/caltech_ionic_external_policy_balam_checksums.sha256 | cut -d' ' -f1)"
SUMMARY_SHA256="$(sha256sum analysis/results/caltech_ionic_external_policy_summary.json | cut -d' ' -f1)"
cat > analysis/results/caltech_ionic_external_policy_VERIFIED.json <<EOF
{
  "status": "VERIFIED",
  "formal_job_id": "70740",
  "verification_job_id": "${SLURM_JOB_ID}",
  "verifier_sha256": "${VERIFIER_SHA256}",
  "verifier_amendment_sha256": "${VERIFIER_AMENDMENT_SHA256}",
  "remote_amendment_sha256": "${REMOTE_AMENDMENT_SHA256}",
  "checksums_sha256": "${CHECKSUMS_SHA256}",
  "summary_sha256": "${SUMMARY_SHA256}"
}
EOF

tar -czf analysis/results/caltech_ionic_external_policy_balam_results.tar.gz \
  analysis/CALTECH_IONIC_VERIFIER_AMENDMENT_4.md \
  analysis/CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md \
  analysis/verify_caltech_ionic_external_policy_results.py \
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
  analysis/results/caltech_ionic_external_policy_COMPLETE.json \
  analysis/results/caltech_ionic_external_policy_VERIFIED.json

echo "Same-environment verification complete: ${SLURM_JOB_ID}"
