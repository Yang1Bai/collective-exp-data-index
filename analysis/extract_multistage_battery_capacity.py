"""Frozen RPT capacity extractor for the multi-stage battery experiment."""

from __future__ import annotations

import csv
import io
import math
import re
import zipfile
from pathlib import Path


EXPECTED_COLUMNS = ["run_time", "c_vol", "c_cur", "c_surf_temp", "amb_temp", "step_type"]
ACCEPTED_COLUMNS = [EXPECTED_COLUMNS, [*EXPECTED_COLUMNS, "time_to_sec"]]
TIME_RE = re.compile(r"^(\d+):(\d{2}):(\d{2}(?:\.\d+)?)$")


class CapacityExtractionError(ValueError):
    """Raised when a frozen endpoint validity rule fails."""


def parse_elapsed_seconds(value: str) -> float:
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        raise CapacityExtractionError(f"invalid run_time: {value!r}")
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    if not (0 <= minutes < 60 and 0 <= seconds < 60):
        raise CapacityExtractionError(f"run_time component out of range: {value!r}")
    result = 3600.0 * hours + 60.0 * minutes + seconds
    if not math.isfinite(result):
        raise CapacityExtractionError(f"nonfinite run_time: {value!r}")
    return result


def parse_step_type(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        number = float(stripped)
    except ValueError as exc:
        raise CapacityExtractionError(f"invalid step_type: {value!r}") from exc
    if not math.isfinite(number) or not number.is_integer():
        raise CapacityExtractionError(f"nonintegral step_type: {value!r}")
    return int(number)


def _integrate_block(points: list[tuple[float, float]], step_type: int) -> float:
    if len(points) < 2 or len({time for time, _ in points}) < 2:
        raise CapacityExtractionError(f"step_type {step_type} has fewer than two distinct timestamps")
    total_as = 0.0
    for (time_a, current_a), (time_b, current_b) in zip(points, points[1:]):
        delta = time_b - time_a
        if delta < 0:
            raise CapacityExtractionError(f"time decreases within step_type {step_type}")
        total_as += 0.5 * (current_a + current_b) * delta
    return total_as / 3600.0


def extract_rpt_capacity(handle: io.TextIOBase) -> dict[str, float | int]:
    reader = csv.DictReader(handle)
    if reader.fieldnames not in ACCEPTED_COLUMNS:
        raise CapacityExtractionError(f"unexpected CSV header: {reader.fieldnames!r}")

    blocks: dict[int, list[list[tuple[float, float]]]] = {21: [], 22: []}
    active_step: int | None = None
    last_time: float | None = None
    row_count = 0
    for row in reader:
        row_count += 1
        time = parse_elapsed_seconds(row["run_time"])
        if last_time is not None and time < last_time:
            raise CapacityExtractionError("run_time decreases within the RPT file")
        last_time = time
        step = parse_step_type(row["step_type"])
        if step not in {21, 22}:
            active_step = None
            continue
        try:
            current = float(row["c_cur"])
        except (TypeError, ValueError) as exc:
            raise CapacityExtractionError(f"invalid c_cur in step_type {step}: {row['c_cur']!r}") from exc
        if not math.isfinite(current):
            raise CapacityExtractionError(f"nonfinite c_cur in step_type {step}")
        if active_step != step:
            blocks[step].append([])
            active_step = step
        blocks[step][-1].append((time, current))

    if row_count == 0:
        raise CapacityExtractionError("RPT CSV has no data rows")
    for step in (21, 22):
        if len(blocks[step]) != 1:
            raise CapacityExtractionError(f"step_type {step} has {len(blocks[step])} contiguous blocks; expected one")

    charge = _integrate_block(blocks[21][0], 21)
    discharge = -_integrate_block(blocks[22][0], 22)
    if not (math.isfinite(charge) and charge > 0):
        raise CapacityExtractionError(f"nonpositive charge capacity: {charge}")
    if not (math.isfinite(discharge) and discharge > 0):
        raise CapacityExtractionError(f"nonpositive discharge capacity: {discharge}")
    return {
        "charge_capacity_Ah": charge,
        "discharge_capacity_Ah": discharge,
        "rpt_capacity_Ah": 0.5 * (charge + discharge),
        "csv_data_rows": row_count,
        "charge_rows": len(blocks[21][0]),
        "discharge_rows": len(blocks[22][0]),
    }


def _unique_member(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.lower().endswith(suffix.lower())]
    if len(matches) != 1:
        raise CapacityExtractionError(f"expected exactly one *{suffix}; found {len(matches)}")
    return matches[0]


def _validate_23c_meta(archive: zipfile.ZipFile, csv_member: str) -> str:
    names = archive.namelist()
    meta_member = re.sub(r"\.csv$", "_meta.txt", csv_member, flags=re.IGNORECASE)
    if meta_member not in names:
        raise CapacityExtractionError(f"missing metadata companion for {csv_member}")
    with archive.open(meta_member) as raw:
        text = raw.read().decode("utf-8-sig", errors="strict")
    match = re.search(r"^Climate chamber temperature setpoint:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    token = match.group(1).replace(" ", "") if match else ""
    if token not in {"23", "23°C", "23Â°C"}:
        raise CapacityExtractionError(f"metadata setpoint is not 23°C for {csv_member}")
    return meta_member


def extract_cell_endpoint(archive_path: Path) -> dict[str, float | int | str]:
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        et_member = _unique_member(names, "_ET_T23.csv")
        at_member = _unique_member(names, "_AT_T23.csv")
        et_meta = _validate_23c_meta(archive, et_member)
        at_meta = _validate_23c_meta(archive, at_member)
        with archive.open(et_member) as raw:
            et = extract_rpt_capacity(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        with archive.open(at_member) as raw:
            at = extract_rpt_capacity(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))

    q_et = float(et["rpt_capacity_Ah"])
    q_at = float(at["rpt_capacity_Ah"])
    if q_et <= 0:
        raise CapacityExtractionError("initial RPT capacity is nonpositive")
    return {
        "et_csv_member": et_member,
        "at_csv_member": at_member,
        "et_meta_member": et_meta,
        "at_meta_member": at_meta,
        "q_charge_et_Ah": et["charge_capacity_Ah"],
        "q_discharge_et_Ah": et["discharge_capacity_Ah"],
        "q_rpt_et_Ah": q_et,
        "q_charge_at_Ah": at["charge_capacity_Ah"],
        "q_discharge_at_Ah": at["discharge_capacity_Ah"],
        "q_rpt_at_Ah": q_at,
        "q_rel_end_percent": 100.0 * q_at / q_et,
        "q_rel_charge_percent": 100.0 * float(at["charge_capacity_Ah"]) / float(et["charge_capacity_Ah"]),
        "q_rel_discharge_percent": 100.0 * float(at["discharge_capacity_Ah"]) / float(et["discharge_capacity_Ah"]),
        "charge_discharge_disagreement_et_percent": 100.0 * abs(float(et["charge_capacity_Ah"]) - float(et["discharge_capacity_Ah"])) / q_et,
        "charge_discharge_disagreement_at_percent": 100.0 * abs(float(at["charge_capacity_Ah"]) - float(at["discharge_capacity_Ah"])) / q_at,
        "et_csv_data_rows": et["csv_data_rows"],
        "at_csv_data_rows": at["csv_data_rows"],
    }
