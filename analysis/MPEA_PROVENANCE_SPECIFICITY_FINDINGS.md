# MPEA provenance and donor-specificity findings

## Verification

The Balam run completed successfully as job 71811 (`mpea-prov2`, exit code
0:0). The formal outputs contain 3,900 metric rows and 333,840 row-level
predictions. Remote and local semantic verification both passed against frozen
design SHA-256
`1116aa24ac1ffcda9eb17ce413818758d32102f223cd3a16ee144159e903863c`.

The independent inferential unit is the unordered elemental system. The 30
label draws and two tree learners are algorithmic repetitions, not independent
experimental samples. Q4 contains 14 elemental systems in every model draw.

## Main result: transfer attenuates along the provenance ladder

With elemental systems held out but publication DOI allowed to overlap,
ultimate-tensile-strength borrowing reduced Q4 RMSE by 6.04% (elemental-system
cluster 95% CI, 1.43% to 10.49%) and improved the augmented Q4 R2 to 0.231
(95% CI, 0.009 to 0.387). The gain over the architecture-matched shuffled
donor was 7.06 percentage points (95% CI, 2.32 to 11.79).

After excluding evaluation-publication DOIs from the donor, the Q4 gain fell to
4.15% (95% CI, -0.25% to 8.29%). After also removing evaluation-publication
DOIs from target development and from every donor cross-fit, the gain fell to
2.26% (95% CI, -1.96% to 6.49%). The strict augmented Q4 R2 remained negative
(-0.130; 95% CI, -0.478 to 0.118).

The 2.26% strict point estimate is the pooled-SSE estimate. Across the 60
algorithmic model-by-draw runs, the mean gain was -0.13%, only 33 of 60 runs
were positive, and the run-level standard deviation was 13.24%. It must
therefore not be described as a stable improvement.

Thus, approximately 62% of the original Q4 point gain was lost under full
publication separation. The original programme-level positive edge is real
under chemical-system separation but is partly provenance-supported and cannot
be described as publication-independent UTS transfer.

## Donor specificity under full DOI separation

All donors were restricted to 265 eligible source records.

- Ultimate tensile strength: Q4 RMSE gain 2.26% (95% CI, -1.96% to 6.49%).
- Vickers hardness: Q4 RMSE gain 2.24% (95% CI, 1.06% to 3.37%); gain over its
  shuffled donor 2.85 percentage points (95% CI, 1.67 to 4.10).
- Elongation at failure: Q4 RMSE gain -0.09% (95% CI, -1.64% to 1.36%).

No predeclared primary contrast survived four-comparison Holm correction.
Ultimate tensile strength did not outperform hardness (Holm-adjusted p =
0.488). The defensible interpretation is therefore class-selective rather than
UTS-specific: strength-related neighboring endpoints retain modest transferable
signal after publication separation, whereas the ductility endpoint does not.
The hardness result is a frozen secondary result, not an independent
prospective confirmation.

The hardness result was positive in 48 of 60 model-by-draw runs, but its
run-level gain had a standard deviation of 4.91% and a 2.5th-to-97.5th
percentile range of -6.92% to 12.66%. Its absolute log10-RMSE reduction was
0.0083 versus a run-level standard deviation of 0.0161. Without a declared
experimental noise floor or minimum practically important effect, this is
detectable secondary structure, not a convincing practical OOD improvement.

## Experimental-state mechanism

Under full DOI separation, the full planned-state contract gave a 2.26% Q4
point gain. Composition-only borrowing gave 0.29%, and removing test type and
test temperature gave 0.19%; neither supplied useful absolute OOD prediction.
Removing processing and phase reduced the point gain to 1.42%, whereas removing
density retained 1.93%.

The transferred feature is therefore not simply a composition proxy. Test
context is the most consequential state block in this ablation, with processing
and phase providing additional support. This result directly supports
state-matched borrowing and argues against indiscriminate donor-feature
injection.

## Target-label equivalence

At 60 target labels, the strict UTS-augmented Q4 RMSE was 0.3394. The frozen
target-only learning curve reached this error at an interpolated 76.3 labels.
The point estimate is therefore equivalent to approximately 16 additional
target labels, or 27% more target labeling. This is a practical effect-size
translation, not a confidence-bounded sample-efficiency claim.

## Claim decision

The result strengthens the boundary and gatekeeping parts of the paper:

1. chemical-system-disjoint transfer is reproducibly positive;
2. stronger publication separation attenuates the selected UTS edge;
3. a second strength-related donor shows a small, unstable secondary
   strict-provenance benefit;
4. a ductility donor and state-poor contracts are null;
5. the correct policy is therefore selective borrowing or abstention, not
   generic adjacency-based transfer.

The current experiment does not supply a headline-quality,
publication-independent positive transfer edge. The paper must not state that
publication-independent UTS transfer was statistically confirmed, that the
strict hardness effect is practically meaningful, that the strict model solved
OOD prediction, or that the effect establishes prospective discovery.
