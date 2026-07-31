# Balam run: frozen OBELiX OOD discovery campaign

This package runs the prespecified sequential discovery simulation in
`analysis/obelix_ood_discovery_design.json`.  It does not refit or redefine the
source priors, outcome, seeds, discovery threshold, controls, or claim gates.

The self-contained NPZ is checked against its SHA-256 manifest before any model
fit.  It contains 500 canonical OBELiX rows, 126 composition features, the
official 390/110 train/test split, the fixed 44-row hard-OOD subset, and three
frozen source-prior columns.  Exact source-target composition overlap is zero.

## Submit

From the repository root in a visible PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit.ps1
```

Enter the Balam password or keyboard-interactive response only in that terminal.
The script uploads one archive, creates an isolated pinned environment on the
login node, and submits the SLURM job under account `ac-sdl`.
Because upload and remote submission are separate SSH connections, Balam may
ask for the same interactive login twice.  Never paste the password into chat.

The job follows the previously proven Balam full-node Slurm pattern:
`compute_full_node`, four GPU allocation units, one task, and 64 CPU cores.
The code itself is CPU-only and leaves the GPUs unused.  The wall-time limit is
eight hours.  Seed batches are written atomically under a design/input-hashed
checkpoint directory, so resubmission can resume rather than repeat completed
batches.

## Monitor

```powershell
ssh yangbai@balam.scinet.utoronto.ca "squeue -u yangbai"
```

The remote log is under
`/scratch/yangbai/collective-exp-ood/logs/obelix-ood-<jobid>.out`.
If the job has left the queue, inspect its terminal state and exact-id logs in
Balam bash:

```bash
sacct -j JOBID --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,AllocTRES%80
tail -n 160 /scratch/yangbai/collective-exp-ood/logs/obelix-ood-JOBID.out
tail -n 200 /scratch/yangbai/collective-exp-ood/logs/obelix-ood-JOBID.err
ls -lh /scratch/yangbai/collective-exp-ood/analysis/results/*COMPLETE*
```

## Fetch

After the job leaves the queue:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_results.ps1
```

The archive includes all reach, trajectory, inference, bootstrap, summary,
environment, and checksum artifacts.  The manuscript claim remains bounded to
a retrospective sequential simulation on a genuinely held-out experimental
database pool; it is not a prospective laboratory campaign.

## Post-diagnostic neighborhood-policy benchmark

The completed frozen campaign should not be rerun or reinterpreted. A separate
exploratory job tests explicit source ranking, target/source rank fusion,
composition novelty, target mean, the failed UCB policy, random acquisition,
and wrong-source controls. Its design was frozen only after the signal-anatomy
diagnostic and therefore cannot change the published OBELiX null.

This benchmark uses one Balam full node and runs 64 independent seed workers,
one per physical CPU core. The scikit-learn workload is CPU-only and does not
use the four allocated GPUs; the full-node request is an operational latency
choice after the scheduler returned the same estimated start time for both a
single-GPU slice and a full node. Explicit CPU and MPI directives are omitted
so Slurm applies Balam's native mapping of 32 logical CPU threads per GPU
without the earlier partial-allocation warning. This changes only execution
parallelism, not the frozen design, seeds, models, or inference.

Submit from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit_neighbor_policy.ps1
```

After the job completes, fetch and verify:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_neighbor_policy_results.ps1
```

The expected job name is `neighbor-policy`; logs are
`/scratch/yangbai/collective-exp-ood/logs/neighbor-policy-<jobid>.out` and
`.err`. The job records full 40-step trajectories so that one early lucky hit
cannot conceal poor cumulative recall or regret.

The retained run completed as job `70666` on `balam002` with exit code `0:0`.
The local verifier matches every remote checksum and independently recomputes
first-hit reach, cumulative-hit utility, pool regret, policy summaries, and all
20 paired contrast effects from the 80,000 trajectory rows. The author-side
attribution audit is recorded in
`../NEIGHBOR_TRANSFER_POLICY_VALIDATION.md`; it leaves the frozen UCB null
unchanged.

## Independent Caltech ionic-conductor policy benchmark

This is the first outcome-frozen external target for the safer policy family.
It uses a DOI/ICSD/composition-disjoint 339/144 development-candidate split,
an additional 58-entity hard-OOD scope, 100 paired campaigns, 40 acquisitions,
five-fold source admission gates, wrong-source controls, and an exploratory
novelty-band policy. The packaged database is about 20.8 MB compressed; the
raw external CSV hash and the 97 MB local SQLite snapshot are verified before
the result is accepted.

Submit from a visible PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit_caltech_ionic_policy.ps1
```

The expected job name is `caltech-borrow`. It requests the same full-node,
four-allocation-unit, 64-worker configuration as the completed policy job and
uses hash-keyed seed-batch checkpoints. Monitor with:

```powershell
ssh yangbai@balam.scinet.utoronto.ca "squeue -u yangbai"
```

After completion, fetch and independently recompute the trajectory utilities,
eight Holm-corrected contrasts, and gate summaries:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_caltech_ionic_policy_results.ps1
```

The result can validate at most one retrospective source-to-policy edge. It
cannot establish prospective laboratory acceleration or new science.

## Combined outcome-unseen core-story programme

The combined job executes the complete frozen Starrydata reverse-transport and
clean four-plate TRI OER programmes on one full Balam node. It includes all
prediction baselines, two representations, three learners, matched specificity
controls, fixed CCA policies, six prewritten hypothesis cards, independent
verifiers, and the two-target random-effects synthesis. Smoke files are never
packaged as claim-bearing results.

Submit from a visible PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit_core_story_outcome_unseen.ps1
```

The expected job name is `core-borrow`. Monitor with:

```powershell
ssh yangbai@balam.scinet.utoronto.ca "squeue -u yangbai"
```

After completion, fetch and independently verify both targets and their
cross-target synthesis:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_core_story_outcome_unseen_results.ps1
```

The job is retrospective and outcome-unseen at the method-selection boundary;
it is not a prospective laboratory campaign. Null targets and abstentions stay
in the knowledge-borrowing map.

The retained formal run completed as Job `70888` with exit code `0:0`. The
downloaded archive passed portable Starrydata, TRI, and multi-target verification.
Starrydata is directionally positive but fails its complete gate; TRI is null;
the two-target mean is null and heterogeneous. Earlier failed jobs and verifier-
only amendments remain in the audit trail and did not change scientific choices.

## Multi-stage battery metadata-only archive map

This job downloads the 279 battery ZIP archives (about 10.3 GB total) but opens
only archive member names and `*_meta.txt`. It never opens a numeric CSV member.
The resulting table resolves each Figshare file ID to Stage 1 or Stage 2 using
the composite `(archive serial, archive-internal serial)` key. This map is a
mandatory data-integrity gate before the frozen CCA-v2 outcome analysis.

Submit from the repository root in a visible PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit_multistage_battery_file_map.ps1
```

The expected job name is `battery-map`. Balam requires every job to reserve a
GPU, so this metadata-only task requests the minimum allowed allocation: one
GPU and its associated 32 CPU cores on the regular `compute` partition. The GPU
is not used by the mapper. After completion, fetch and independently verify the
279-row map:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_multistage_battery_file_map_results.ps1
```

The mapping job does not fit a model and does not reveal a scientific result.
If any archive lacks an unambiguous composite key, the later target analysis
must exclude it and enforce the frozen coverage gate rather than guess or
replace the target.

If Balam compute nodes cannot reach Figshare, cancel the remote job and run the
checkpointed mapper locally:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_run_multistage_battery_file_map.ps1
```

The local runner defaults to eight concurrent downloads, deletes each ZIP after
metadata extraction, and resumes from
`analysis/results/multistage_battery_file_map/archive_map_checkpoint.json`.

## Multi-target OOD knowledge-borrowing benchmark

This full-node job runs the frozen 100-repeat benchmark across eight recipient
tasks, 40 inherited real donor edges, eight shuffled controls and three fixed
recipient learners. It then independently verifies OOD/ID strata, identity
exclusion, metric reconstruction, OOD-minus-ID contrasts, multiplicity and
edge/cohort gates.

Submit from the repository root in a visible PowerShell terminal:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_upload_and_submit_multi_target_ood_borrowing.ps1
```

The expected job name is `multi-ood-map`. It requests a full Balam node and
uses 64 workers. Monitor with:

```powershell
ssh yangbai@balam.scinet.utoronto.ca "squeue -u yangbai"
```

After completion, download and independently verify the formal package:

```powershell
powershell -ExecutionPolicy Bypass -File analysis\balam\local_fetch_multi_target_ood_borrowing_results.ps1
```

The smoke package is only a workflow check. The formal result remains
post-outcome method development and cannot replace a new outcome-unseen
external programme.
