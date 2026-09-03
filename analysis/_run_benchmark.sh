#!/bin/bash
# Run full benchmark in background, save output to log file.
cd /Users/sissifeng/collective-exp-data-index
python analysis/run_full_benchmark.py > /tmp/benchmark_output.log 2>&1
echo "DONE: $?" >> /tmp/benchmark_output.log
