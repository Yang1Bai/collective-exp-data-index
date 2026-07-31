import pandas as pd
import pytest

from analysis.verify_starrydata_reverse_transport_results import (
    FROZEN_RANK_COLUMNS,
    merge_frozen_exploration_ranks,
)


def _frames():
    evaluation = pd.DataFrame(
        {
            "entity_id": ["a", "b"],
            "component_id": ["c1", "c2"],
            "target_zt": [1.0, 2.0],
        }
    )
    frozen = pd.DataFrame(
        {
            "entity_id": ["a", "b"],
            "component_id": ["c1", "c2"],
            FROZEN_RANK_COLUMNS[0]: [0.1, 0.9],
            FROZEN_RANK_COLUMNS[1]: [0.2, 0.8],
            FROZEN_RANK_COLUMNS[2]: [0.3, 0.7],
        }
    )
    return evaluation, frozen


def test_rank_merge_preserves_unsuffixed_target_component_id():
    evaluation, frozen = _frames()
    merged = merge_frozen_exploration_ranks(evaluation, frozen)
    assert merged["component_id"].tolist() == ["c1", "c2"]
    assert "component_id_x" not in merged.columns
    assert "component_id_y" not in merged.columns
    assert all(column in merged.columns for column in FROZEN_RANK_COLUMNS)


def test_rank_merge_rejects_changed_component_assignment():
    evaluation, frozen = _frames()
    frozen.loc[frozen["entity_id"].eq("b"), "component_id"] = "changed"
    with pytest.raises(AssertionError, match="component assignments disagree"):
        merge_frozen_exploration_ranks(evaluation, frozen)
