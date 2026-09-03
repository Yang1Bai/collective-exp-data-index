# Decision: replace the broad optical-transfer sweep

## Decision

The broad post-gate screen in `OPTICAL_TRANSFER_METHOD_DISCOVERY_PROTOCOL.md`
will not be submitted. It mixes many feature blocks, property subsets and
fusion rules, creating unnecessary researcher degrees of freedom while still
reusing deterministic scalar functions of the same molecular fingerprint.

The replacement is one mechanism-led strategy:

1. learn a molecular-graph representation from experimental optical outcomes
   with a fixed Chemprop directed message-passing encoder;
2. keep aqueous/alcohol and molecular-solid measurements as separate source
   experts;
3. use the source representation only to correct out-of-fold residuals from a
   target-only hurdle model;
4. scale the correction by outcome-free source chemical support;
5. allow the correction weight to be exactly zero;
6. compare with a state-blind source encoder, a shuffled-source-label encoder
   and the original scalar optical predictions.

The strategy is evaluated on the already frozen 300 scaffold-separated draws
at target-label budgets 30, 60 and 120. Development selection is made on the
40% of evaluation molecules farthest from the labeled target set. The 96
published blind outcomes remain unopened.

## Why this is the preferred test

The recipient outcome is strongly zero-inflated: 340 of 572 development
measurements are zero. A target-only hurdle model therefore separates activity
occurrence from positive activity magnitude before any donor information is
introduced. This avoids attributing a better target likelihood to transfer.

The original scalar-injection gate failed. Each scalar prediction was also a
deterministic function of the same Morgan fingerprint used by the recipient
model. Supervised source-task pretraining is a stricter test of knowledge
borrowing because the representation is shaped by external experimental
optical labels. Shuffling those labels preserves architecture and molecular
inputs while destroying the claimed knowledge.

## Evidential boundary

This is post-gate method development. A successful development result can
release exactly one frozen method to the still-unopened blind set. It cannot
rewrite the failed scalar-injection result. If the focused method does not pass
all frozen gates, the optical-to-photocatalysis edge remains null and no blind
outcomes are opened.
