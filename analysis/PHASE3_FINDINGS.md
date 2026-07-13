# Phase 3 findings: rigor upgrades, mechanism, and the transfer→search gap

Extends Phase 2. All scripts in analysis/; figures fig4/fig5/fig6.

## 1. Statistical power (bootstrap CIs, 15–20 reps)
Cross-domain transfer into data-poor OBELiX solid electrolytes:
- **thermoelectric (TE:ZT) source: significant** — ΔR² = +0.173 [+0.078,+0.302]
  at n=30, +0.106 [+0.003,+0.203] at n=120 (95% CI excludes 0).
- alloy-YS and catalysis-FE sources: **not significant** (CIs include 0).
→ Sharpens the "selective" claim: only the physically-closest neighbor
  (activated transport) gives a statistically significant boost.

## 2. Mechanism (feature attribution)
In the augmented OBELiX model, the injected thermoelectric-prediction feature
is the **single most important feature (importance 0.254, rank 1 of 54)** —
above every element. The OBELiX model keys on P, O, Li, La (garnet/LISICON
electrolyte chemistry); the TE source model keys on Te, Sb, Se, Ag, Bi
(chalcogenide thermoelectrics). Different elements → what transfers is the
learned *composition→activated-transport* functional form, not shared
chemistry. Consistent with the Phase-2b result (transfer survives removing
chalcogenides).

## 3. Organic-side null is physical, not a featurization artifact
Best-case aqueous molecular pair (aqsoldb logS ← FreeSolv ΔG_hydration),
tested under BOTH element-composition and Morgan fingerprints: ΔR² ≈ 0 in
both (CIs include 0). Structural features do not unlock organic cross-property
transfer here → the cold organic region of the knowledge-borrowing map (Fig 4)
reflects genuinely distinct underlying physics, not a poor representation.

## 4. Transfer → search-acceleration gap (honest null)
Attempted the applied payoff: RF-UCB active-learning campaign on OBELiX to
find top-5% ionic conductors, baseline vs cross-domain-prior feature (10 seeds).
**No significant speedup** (24 vs 21 experiments to top-5%; early campaign
baseline is if anything marginally ahead). Predictive transfer (rigorously
shown in §1–2) does NOT automatically translate into faster discovery when the
borrowed signal is injected naively as a BO feature.

## Overall conclusion
The unified data lake yields a **measurable, significant, mechanistically
interpretable, and physically-selective** map of which data-poor domains can
borrow from which neighbors — but converting that predictive advantage into
self-driving-lab search acceleration is a real, unsolved problem, not a
corollary. This is the paper's central honest contribution and its clearest
open question.
