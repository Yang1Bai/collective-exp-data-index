from __future__ import annotations

from copy import deepcopy

from scripts.validate_candidates import validate_payload
from scripts.validate_catalog import lite_check


def valid_catalog_entry() -> dict:
    return {
        "id": "example-dataset",
        "name": "Example dataset",
        "description": "A sufficiently detailed experimental dataset description.",
        "domain": "materials",
        "subdomain": "batteries",
        "data_type": "experimental",
        "access": "open",
        "homepage_url": "https://example.org/data",
        "source": "curated-seed",
        "doi": "10.1234/example",
    }


def test_lite_catalog_gate_rejects_untracked_source_class() -> None:
    entry = valid_catalog_entry()
    entry["source"] = "api-discovery-tdm"
    errors = lite_check([entry])
    assert any("source='api-discovery-tdm'" in error for error in errors)


def test_lite_catalog_gate_rejects_duplicate_doi() -> None:
    first = valid_catalog_entry()
    second = deepcopy(first)
    second["id"] = "second-dataset"
    errors = lite_check([first, second])
    assert any("duplicate DOI" in error for error in errors)


def test_candidate_acceptance_requires_main_catalog_record() -> None:
    candidate = {
        "candidate_id": "candidate-one",
        "name": "Candidate one",
        "homepage_url": "https://example.org/candidate",
        "doi": "10.1234/not-ingested",
        "concept_doi": None,
        "discovery_source": "api-discovery-tdm",
        "candidate_status": "accepted",
        "record_kind": "dataset",
        "outcome_access_status": "metadata-only",
        "canonical_record_id": "missing-record",
        "review_flags": [],
        "review_notes": None,
        "discovered_at": "2026-07-20T16:49:52Z",
    }
    payload = {
        "schema_version": 1,
        "snapshot_utc": "2026-07-20T16:49:52Z",
        "entries": [candidate],
    }
    errors = validate_payload(payload, [valid_catalog_entry()])
    assert any("valid canonical_record_id" in error for error in errors)
    assert any("DOI is absent" in error for error in errors)
