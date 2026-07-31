# Discovery candidate quarantine

Automated searches, including text-and-data-mining records, enter this queue and
do **not** count toward the validated manuscript catalog.  A candidate can move
to `catalog/catalog.json` only after a curator verifies that it is a genuine
experimental database or dataset, resolves version and concept DOIs, records a
direct evidence URL, checks access and licence statements, and passes the base
catalog validator.

An `accepted` queue entry must name the resulting `canonical_record_id`.  The
candidate validator rejects an accepted record that is absent from the main
catalog.  The paper's 118-record snapshot therefore remains reproducible while
new discovery can continue without silently changing the denominator.
