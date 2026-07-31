# Outcome-blind external ionic-conductor policy test

This specification was frozen before downloading or reading any row from the
Caltech experimental Li-ion conductivity CSV. The only prior information used
was the repository metadata: file identity and checksum, CC0 license, 571
Li-containing compounds, room-temperature conductivity, DOI, ICSD identifier,
and lowest measurement temperature.

## Why this target

The target is independent of the current local data lake and supplies the
article identifiers needed to remove cross-database reuse. It permits a
physically ordered test with four source roles:

1. OBELiX Li-ion conductivity as a same-property cross-database anchor;
2. ESTM thermoelectric ZT as a transport-adjacent source;
3. Borg yield strength as an unrelated mechanical control;
4. OCx hydrogen Faradaic efficiency as an unrelated catalysis control.

All exact target compositions and target DOIs are removed from every source
training set. Thus success cannot be obtained by retrieving the same material
or article from another database.

## Why the acquisition endpoint changes

The OBELiX diagnostic showed that a first hit can be one lucky candidate. The
primary endpoint here is therefore cumulative top-5% hit AUC through 20
acquisitions. First-hit speed is retained as a non-inferiority guardrail, and
recall at 20 must exceed 0.50. This tests whether borrowing helps explore a
high-value region rather than merely placing one known record near the top.

## Safer borrowing strategy

The strategy starts from composition novelty. Target mean and each source are
added only when group-aware cross-validation on the currently labelled target
set shows positive error reduction. Source influence is the rank correction
between an augmented and a composition-only target model; its weight is
shrunk toward zero and at most two sources can enter. If no source passes, the
policy falls back exactly to target-only novelty.

This architecture makes negative transfer observable and reversible. Wrong or
shuffled sources must be admitted in fewer than 20% of steps and carry mean
weight below 0.10. A source-aware policy must then beat the matching safe
target-only backbone, not a target policy that already loses to random.

## Claim boundary

The file and design can support an external retrospective policy test because
the row-level target outcomes were unseen at freeze time. They cannot support a
prospective discovery or new-science claim. That requires a source-derived
hypothesis and matched control written before revealing candidate outcomes.
