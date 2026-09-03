# State-matched MPEA figure contract

**Core conclusion:** Restoring the planned experimental state and generating
UTS donor features under the same held-system contract as deployment produces a
source-specific reduction in chemically OOD YS error, while measured UTS
reveals substantial remaining headroom.

**Figure archetype:** schematic-led asymmetric composite.

**Target/output:** *Digital Discovery*, double-column, 183 × 108 mm; editable
SVG and PDF, 600-dpi TIFF, 300-dpi PNG preview.

**Backend:** Python/matplotlib exclusively.

**Panel map (Figure 3e–h)**

- **e — information contract:** planned-state fields, intact elemental-system
  splitting, source exclusions, cross-fitted UTS feature, and YS recipient.
- **f — primary falsifier:** real UTS, architecture-matched shuffled UTS, and
  their paired Q4 contrast with two-way cluster-bootstrap intervals.
- **g — OOD scope:** Q1, Q4, and Q4-minus-Q1 effects, explicitly showing that
  the benefit persists in Q4 but is not statistically Q4-exclusive.
- **h — information ladder:** composition-to-state improvement,
  predicted-UTS incremental gain, and measured-UTS auxiliary ceiling.

**Evidence hierarchy**

- Hero: positive Q4 interval and real-minus-shuffled interval.
- Validation: 55/60 positive runs, pooled Q4 R²=0.103, 59 systems.
- Boundary: Q4-minus-Q1 interval crosses zero; measured UTS is a separate
  auxiliary-measurement contract.

**Statistics**

- Primary intervals: 100,000-replicate two-way cluster bootstrap over elemental
  systems and model-by-draw runs.
- State and measured-ceiling intervals: descriptive t intervals across the 60
  frozen model-by-draw runs.
- Split: intact elemental systems; 639 development and 428 evaluation rows,
  59 held evaluation systems.

**Reviewer risks**

- Do not call the result independent or prospective.
- Do not present measured UTS as model transfer.
- Do not claim statistically preferential Q4 benefit.
- V2 architecture-matched shuffled control supersedes the V1 residual-anchor
  shuffled contrast.
