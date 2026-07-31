#!/bin/bash
#SBATCH --job-name=battery-map
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

OUTPUT="analysis/results/multistage_battery_file_map"
python -u analysis/map_multistage_battery_archives.py \
  --output-dir "$OUTPUT" \
  --workers 8
python -u analysis/verify_multistage_battery_file_map.py "$OUTPUT" \
  > "$OUTPUT/INDEPENDENT_VERIFICATION.json"

sha256sum \
  "$OUTPUT/archive_file_stage_map.csv" \
  "$OUTPUT/COMPLETE.json" \
  "$OUTPUT/INDEPENDENT_VERIFICATION.json" \
  > "$OUTPUT/checksums.sha256"

tar -czf analysis/results/multistage_battery_file_map_results.tar.gz \
  "$OUTPUT/archive_file_stage_map.csv" \
  "$OUTPUT/archive_map_checkpoint.json" \
  "$OUTPUT/figshare_article_api.json" \
  "$OUTPUT/experiments_meta.csv" \
  "$OUTPUT/COMPLETE.json" \
  "$OUTPUT/INDEPENDENT_VERIFICATION.json" \
  "$OUTPUT/checksums.sha256"

echo "Metadata-only battery archive map complete: ${SLURM_JOB_ID}"
