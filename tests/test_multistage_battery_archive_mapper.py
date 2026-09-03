from analysis.map_multistage_battery_archives import (
    normalize_testpoint_token,
    parse_metadata_text,
    resolve_complementary_stages,
    resolve_with_validated_date_envelopes,
)


def test_archive_metadata_parser_extracts_stage_join_key() -> None:
    parsed = parse_metadata_text(
        "Laboratory identifier: SIE\n"
        "Internal cell serial: S001\n"
        "Testpoint: k01\n"
        "run_time: Time since start of measurement\n"
    )
    assert parsed == {
        "internal_serial": "S001",
        "laboratory": "SIE",
        "testpoint": "k01",
    }


def test_archive_metadata_parser_preserves_numeric_stage2_serial() -> None:
    parsed = parse_metadata_text(
        "Laboratory identifier: SIE\r\n"
        "Internal cell serial: 057\r\n"
        "Testpoint: k01\r\n"
    )
    assert parsed["internal_serial"] == "057"


def test_testpoint_token_normalizes_mkii_but_preserves_identity() -> None:
    assert normalize_testpoint_token("TP_k04_06_MKII") == "k04"
    assert normalize_testpoint_token("k02noCU") == "k02"


def test_complementary_stage_requires_an_exactly_mapped_twin() -> None:
    candidates = {
        "TP_k04_06": [
            {"serial_internal": "INT012", "serial": "TP_k04_06", "stage": "1", "lab": "INT", "type": "k", "tp": "4", "cell": "6", "sampling": "FF"},
            {"serial_internal": "INT190", "serial": "TP_k04_06", "stage": "2", "lab": "INT", "type": "k", "tp": "4", "cell": "6", "sampling": "pi"},
        ]
    }
    exact = {"status": "mapped-metadata-only", "archive_name": "TP_k04_06.zip", "stage": "2"}
    conflict = {
        "status": "unresolved-metadata-conflict",
        "archive_name": "TP_k04_06.zip",
        "archive_internal_serial": "INT048",
        "metadata_conflict_flags": "archive_internal_serial_conflicts_with_experiments_meta",
    }
    resolved = resolve_complementary_stages([exact, conflict], candidates)
    assert resolved[1]["status"] == "mapped-metadata-only"
    assert resolved[1]["stage"] == "1"
    assert resolved[1]["serial_internal"] == "INT012"
    assert resolved[1]["mapping_method"].startswith("archive-serial-plus-complement")


def test_complementary_stage_does_not_guess_when_both_twins_are_unresolved() -> None:
    candidates = {
        "TP_k04_06": [
            {"serial_internal": "INT012", "serial": "TP_k04_06", "stage": "1", "lab": "INT", "type": "k", "tp": "4", "cell": "6", "sampling": "FF"},
            {"serial_internal": "INT190", "serial": "TP_k04_06", "stage": "2", "lab": "INT", "type": "k", "tp": "4", "cell": "6", "sampling": "pi"},
        ]
    }
    rows = [
        {"status": "unresolved-metadata-conflict", "archive_name": "TP_k04_06.zip"},
        {"status": "unresolved-metadata-conflict", "archive_name": "TP_k04_06.zip"},
    ]
    resolved = resolve_complementary_stages(rows, candidates)
    assert all(row["status"] == "unresolved-metadata-conflict" for row in resolved)


def test_date_envelope_requires_nonoverlap_and_minimum_calibration() -> None:
    candidates = {
        "TP_z04_03": [
            {"serial_internal": "INT021", "serial": "TP_z04_03", "stage": "1", "lab": "INT", "type": "z", "tp": "4", "cell": "3", "sampling": "cLH"},
            {"serial_internal": "INT061", "serial": "TP_z04_03", "stage": "2", "lab": "INT", "type": "z", "tp": "4", "cell": "3", "sampling": "cLH"},
        ]
    }
    calibration = []
    for stage, date in [("1", "05.10.2021"), ("2", "19.01.2023")]:
        for index in range(20):
            calibration.append({
                "status": "mapped-metadata-only",
                "mapping_method": "exact-archive-serial-plus-internal-serial",
                "lab": "INT",
                "stage": stage,
                "measurement_start_date": date,
                "archive_name": f"calibration-{stage}-{index}.zip",
            })
    unresolved = {
        "status": "unresolved-metadata-conflict",
        "archive_name": "TP_z04_03.zip",
        "archive_lab_raw": "INT",
        "measurement_start_date": "05.10.2021",
        "metadata_conflict_flags": "archive_internal_serial_conflicts_with_experiments_meta",
    }
    resolved, audit = resolve_with_validated_date_envelopes(
        calibration + [unresolved], candidates
    )
    assert audit["INT"]["1"]["n"] == 20
    assert resolved[-1]["stage"] == "1"
    assert resolved[-1]["mapping_method"].endswith("validated-lab-date-envelope")
