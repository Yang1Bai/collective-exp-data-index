from analysis.check_core_story_experiments import validate_registry


def test_core_story_registry_is_structurally_valid() -> None:
    result = validate_registry(require_complete=False)
    assert result["status"] == "valid", result["errors"]
    assert result["experiments"] == 15


def test_core_story_registry_has_no_open_submission_blockers() -> None:
    result = validate_registry(require_complete=False)
    blocker_ids = {item["id"] for item in result["submission_blockers"]}
    assert blocker_ids == set()


def test_completed_boundary_program_is_retained() -> None:
    result = validate_registry(require_complete=True)
    assert result["status"] == "valid", result["errors"]
