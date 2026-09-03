# Caltech ionic-conductor same-environment verification amendment

Frozen after the complete job `70740` result bundle was recovered locally and
before any scientific policy contrast was interpreted.

The corrected verifier refit source ExtraTrees models on Windows. ESTM and OCx
reproduced exactly, while OBELiX and Borg source OOF R2 differed from Balam by
approximately 0.002. Those small cross-platform tree-split differences changed
static ranks and therefore prevent exact Windows replay of Linux trajectories.
This is expected for randomized tree implementations with many tied feature
values; it is not evidence that the stored Balam trajectories are internally
inconsistent.

Exact model and static-policy replay must therefore run in the pinned Balam
environment that generated the trajectories. The remote verifier refits all
four sources and reproduces every static and shuffled-static acquisition for
both scopes and all 100 seeds. It also checks checksums, row coverage,
utilities, bootstrap intervals, sign-flip tests, Holm corrections and gate
summaries. Only after that passes is a `VERIFIED` sentinel and final archive
created.

Portable verification after download checks the remote verifier hash, verifier
amendment hashes, formal checksum manifest and summary hash, then independently
recomputes every platform-independent trajectory utility, contrast and gate
summary. It deliberately does not demand bitwise cross-platform ExtraTrees
reproduction. No model, trajectory, endpoint, comparison, threshold or claim
gate changes.
