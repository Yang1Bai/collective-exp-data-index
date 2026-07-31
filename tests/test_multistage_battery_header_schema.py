import zipfile

from analysis.inspect_multistage_battery_headers import EXPECTED_HEADER, read_one_header
from analysis.verify_multistage_battery_header_schema import verify


def test_header_reader_returns_only_first_physical_line(tmp_path) -> None:
    archive_path = tmp_path / "sentinel.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("cell_ET_T23.csv", EXPECTED_HEADER + "\nDO_NOT_READ_THIS_NUMERIC_ROW\n")
    with zipfile.ZipFile(archive_path) as archive:
        observed = read_one_header(archive, "cell_ET_T23.csv")
    assert observed == EXPECTED_HEADER
    assert "DO_NOT_READ" not in observed


def test_frozen_header_and_endpoint_schema_are_valid() -> None:
    result = verify()
    assert result["status"] == "verified-header-and-endpoint-schema", result["errors"]
    assert result["numeric_csv_data_rows_opened"] is False
    assert "Q_RPT_AT_T23" in result["primary_endpoint"]
