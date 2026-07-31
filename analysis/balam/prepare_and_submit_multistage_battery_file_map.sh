#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p logs analysis/results
python analysis/verify_multistage_battery_cca_v2_preoutcome.py
JOB_ID="$(sbatch --parsable analysis/balam/run_multistage_battery_file_map_balam.sh)"
echo "BALAM_JOB_ID=${JOB_ID}"
squeue -j "$JOB_ID"
