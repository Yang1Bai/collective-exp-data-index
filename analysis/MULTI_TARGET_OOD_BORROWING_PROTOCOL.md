# Frozen multi-target OOD knowledge-borrowing benchmark

## Scientific question

Can a donor model trained on a declared neighboring experimental task repair a
recipient model specifically where the recipient is farthest from its observed
training support, rather than merely improving average interpolation?

This is the systematic test suggested by the central paper thesis. For each
eligible recipient, the existing development observations are the only
recipient labels available for training. The already separated evaluation
groups are ranked by distance from that development support. We then compare
the same recipient learner, fitted to the same recipient observations, with and
without one leakage-excluded donor prediction feature. The required estimand is
therefore not only OOD gain but the difference in gains:

\[
G_\mathrm{specific}=G_\mathrm{OOD,Q4}-G_\mathrm{ID,Q1},
\qquad
G_s=\frac{\mathrm{RMSE}_{\mathrm{target-only},s}
-\mathrm{RMSE}_{\mathrm{borrowed},s}}
{\mathrm{RMSE}_{\mathrm{target-only},s}}.
\]

A positive \(G_\mathrm{specific}\) says that borrowing helps more in the
knowledge-poor region than in the ID-like region. It does not by itself prove
that the source is scientifically meaningful; the wrong-source and shuffled
controls are therefore part of the same gate.

## Frozen portfolio

The benchmark reuses the target tasks, five donor candidates per target,
representations, group definitions, target-development partitions, and
leakage-exclusion rule in `knowledge_map_design.json`. No donor is added,
removed, or replaced after inspecting this benchmark.

Eight recipients meet the predeclared minimum of 12 intact evaluation groups:

| Recipient | Programme | Designated neighbor | Fixed wrong-source control | Edge class |
|---|---|---|---|---|
| Thermoelectric ZT | ESTM | Seebeck coefficient | alloy yield strength | within database |
| Alloy yield strength | Borg MPEA | ultimate tensile strength | thermoelectric thermal conductivity | within database |
| CO2R H2 selectivity | OCx24 | cell voltage | alloy yield strength | within database |
| Solid-electrolyte ionic conductivity | OBELiX | thermoelectric electrical conductivity | alloy yield strength | cross database |
| Aqueous solubility | AqSolDB | hydration free energy | photoswitch absorption | cross database |
| Hydration free energy | FreeSolv | aqueous solubility | photoswitch absorption | cross database |
| Polymer tensile strength | OpenPoly | Young's modulus | photoswitch absorption | within database |
| Polymer melting temperature | OpenPoly | crystallization temperature | photoswitch absorption | within database |

The photoswitch Z-state task is excluded because its combined evaluation set
contains only five intact scaffold groups, below the frozen minimum. This is an
eligibility exclusion, not an outcome-dependent exclusion.

The analysis evaluates all 40 inherited real directed edges (eight recipients
times five sources), not only the eight designated primary edges. It also
evaluates one independently shuffled version of the designated donor signal per
recipient. Every null and negative-transfer result is retained.

## Fixed OOD definition

OOD membership is defined without recipient outcomes.

- Formula tasks use Euclidean distance in the shared element-composition
  representation after scaling each feature with the complete recipient
  development matrix only.
- Molecular tasks use exact Tanimoto distance between Morgan radius-2,
  1024-bit fingerprints.
- Each evaluation entity is compared with every complete development entity.
  The median entity distance is assigned to its intact element-set or
  Bemis–Murcko-scaffold group.
- Evaluation groups are deterministically ranked and divided into four
  approximately group-balanced quartiles. Q1 is the ID-like scope and Q4 the
  OOD scope. A group can never cross scopes.

The complete development set is used only as a feature-space reference for
distance. Each model fit still receives only the frozen low-label budget
sampled as intact development groups. No evaluation outcome is used in
distance calculation, donor choice, feature construction, or fitting.

## Models and controls

The primary recipient learner is ridge regression with \(\alpha=10\), matching
the knowledge-map design. Random forest and extremely randomized trees are
fixed sensitivity learners. Each comparison holds the sampled target labels,
evaluation entities, representation, learner family, and random seed constant;
the only difference is the appended donor prediction feature.

Donor models exclude every recipient evaluation material identity before
fitting. Each designated edge must have zero remaining identity overlap.

Two specificity controls are compulsory:

1. a fixed scientifically distant donor already present in the inherited
   five-source set; and
2. a shuffled designated-donor signal that preserves the marginal
   distribution but destroys entity alignment.

## Replication and inference

The formal benchmark uses 100 independent grouped target-training draws. The
primary uncertainty interval resamples both training draws and intact
evaluation groups. The Q1 and Q4 gains use the same resampled training-draw
weights, so their difference preserves the paired design. Wrong-source and
shuffled-source contrasts use paired repeat bootstraps. The one-sided
repeat-level sign-flip tests are Holm-adjusted across the eight designated
primary edges.

The inferential unit for an edge is the intact evaluation group, with
target-training repetition treated as a second sampling dimension. Programme
claims are aggregated over seven programme clusters; the two OpenPoly
recipients are not treated as independent programmes.

## Frozen full edge gate

A designated edge is classified as `ood-repair-gate-passed` only if all of the
following hold:

1. mean Q4 relative-RMSE gain is at least 5%;
2. its hierarchical 95% interval is above zero;
3. mean borrowed-model Q4 \(R^2\) is positive;
4. Q4 gain is positive in at least 80% of target-training draws;
5. the hierarchical interval for \(G_\mathrm{OOD}-G_\mathrm{ID}\) is above
   zero;
6. it beats both the fixed wrong source and shuffled control with paired 95%
   intervals above zero;
7. at least two of the three fixed learner families have positive mean Q4
   gain;
8. the Holm-adjusted one-sided sign-flip \(P\) value is below 0.05; and
9. post-exclusion donor–evaluation identity overlap is zero.

Failure of one component is not silently converted into success. The declared
secondary classifications distinguish positive but non-OOD-specific,
directional, harmful, and unresolved effects.

## Cohort claims

The selective OOD-repair cohort gate requires at least two independent
programme clusters with a fully passing designated edge and a programme-level
bootstrap interval for mean designated-edge Q4 gain above zero.

The stronger cross-database statement additionally requires at least two of the
three designated cross-database edges to pass the complete edge gate. A
within-database paired-property success is still valuable evidence that
neighboring experimental conditions can be borrowed, but it does not establish
cross-database transfer.

## Analysis status and claim boundary

This protocol was frozen on 23 July 2026 before running this unified benchmark,
but after earlier analyses of several component datasets were already known.
It is therefore a systematic post-outcome method-development benchmark, not a
prospective preregistration. It can demonstrate that a fixed procedure repairs
held-out OOD regions across a declared portfolio and map where that procedure
abstains or fails. Independent confirmation still requires a new
outcome-unseen experimental programme; retrospective success cannot establish
prospective laboratory discovery acceleration.
