import io

import pytest

from analysis.extract_multistage_battery_capacity import (
    CapacityExtractionError,
    extract_rpt_capacity,
    parse_elapsed_seconds,
)


HEADER = "run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type\n"


def test_elapsed_time_allows_hours_above_23() -> None:
    assert parse_elapsed_seconds("27:01:02.500") == 97262.5


def test_capacity_is_mean_of_signed_charge_and_discharge_integrals() -> None:
    rows = (
        "00:00:00.000,3.0,2.0,23,23,21\n"
        "01:00:00.000,4.2,2.0,23,23,21\n"
        "01:00:01.000,4.2,0.0,23,23,0\n"
        "02:00:00.000,4.2,-1.0,23,23,22\n"
        "04:00:00.000,2.5,-1.0,23,23,22\n"
    )
    result = extract_rpt_capacity(io.StringIO(HEADER + rows))
    assert result["charge_capacity_Ah"] == pytest.approx(2.0)
    assert result["discharge_capacity_Ah"] == pytest.approx(2.0)
    assert result["rpt_capacity_Ah"] == pytest.approx(2.0)


def test_capacity_extractor_rejects_multiple_selected_blocks() -> None:
    rows = (
        "00:00:00.000,3.0,1.0,23,23,21\n"
        "00:10:00.000,3.5,1.0,23,23,21\n"
        "00:10:01.000,3.5,0.0,23,23,0\n"
        "00:20:00.000,3.6,1.0,23,23,21\n"
        "00:30:00.000,4.2,1.0,23,23,21\n"
        "00:40:00.000,4.2,-1.0,23,23,22\n"
        "00:50:00.000,2.5,-1.0,23,23,22\n"
    )
    with pytest.raises(CapacityExtractionError, match="2 contiguous blocks"):
        extract_rpt_capacity(io.StringIO(HEADER + rows))
