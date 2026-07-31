#!/usr/bin/env python3
"""Prepare the frozen CALCE LCO wrong-chemistry control table."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import medfilt

from run_crosslab_fade_raw_transfer import (
    EARLY,
    frame_cycle_metrics,
    life_label,
    make_features,
)


KEEP = ["date", "Cycle_Index", "Test_Time(s)", "Current(A)", "Voltage(V)"]


def date_from_name(name: str) -> str:
    upper = name.upper()
    matches = re.findall(r"C[XS]2?_\d+_(\d+)_(\d+)B?_(\d+)", upper)
    if not matches:
        matches = re.findall(r"(\d+)_(\d+)_(\d+)_CX2_32", upper)
    if not matches:
        raise ValueError(f"Cannot parse date from {name}")
    month, day, year = map(int, matches[0])
    return f"{year:04d}-{month:02d}-{day:02d}"


def load_txt(path: Path):
    source = pd.read_csv(path, sep="\t")
    return pd.DataFrame(
        {
            "date": date_from_name(path.stem),
            "Cycle_Index": source["Charge count"] // 2 + 1,
            "Test_Time(s)": source["Time"],
            "Current(A)": source["mA"] / 1000.0,
            "Voltage(V)": source["mV"] / 1000.0,
        }
    )


def load_excel(path: Path):
    with pd.ExcelFile(path) as workbook:
        frames = []
        for sheet in workbook.sheet_names:
            if sheet.startswith("Channel"):
                frames.append(workbook.parse(sheet))
        if not frames:
            frames = [workbook.parse(sheet) for sheet in workbook.sheet_names]
    frame = pd.concat(frames, ignore_index=True)
    frame["date"] = date_from_name(path.stem)
    return frame[KEEP]


def monotone_cycle_index(values):
    values = np.asarray(values).copy()
    current, previous = values[0], values[0]
    for index in range(1, len(values)):
        if values[index] != previous:
            current += 1
            previous = values[index]
        values[index] = current
    return values


def cell_table(zip_path: Path, work: Path):
    cell = zip_path.stem
    cell_dir = work / cell
    if cell_dir.exists():
        shutil.rmtree(cell_dir)
    cell_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(cell_dir)
    files = [
        path
        for suffix in ("*.txt", "*.xlsx", "*.xls")
        for path in cell_dir.rglob(suffix)
        if "_cache" not in path.stem
    ]
    frames = []
    errors = []
    for path in files:
        try:
            frames.append(load_txt(path) if path.suffix.lower() == ".txt" else load_excel(path))
        except Exception as error:
            errors.append(f"{path.name}: {error}")
    if not frames:
        shutil.rmtree(cell_dir)
        return None, errors
    data = pd.concat(frames, ignore_index=True).sort_values(["date", "Test_Time(s)"])
    data["Cycle_Index"] = monotone_cycle_index(data["Cycle_Index"].to_numpy())

    cycles = []
    for _, frame in data.groupby(["date", "Cycle_Index"], sort=True):
        current = frame["Current(A)"].to_numpy(float)
        converted = pd.DataFrame(
            {
                "Current (mA)": current * 1000.0,
                "Time (s)": frame["Test_Time(s)"].to_numpy(float),
                "Voltage (V)": frame["Voltage(V)"].to_numpy(float),
            }
        )
        cycles.append(frame_cycle_metrics(converted))
    qd_raw = np.asarray([item[0] for item in cycles])
    median = medfilt(qd_raw, 21) if len(qd_raw) >= 21 else medfilt(qd_raw, 5)
    threshold = np.median(np.abs(qd_raw - median))
    keep = (np.abs(qd_raw - median) < 3 * max(threshold, 1e-8)) & (qd_raw > 0.1)
    clean = [item for item, accepted in zip(cycles, keep) if accepted]
    if cell.upper() == "CX2_16" and clean:
        clean = clean[1:]
    shutil.rmtree(cell_dir)
    if len(clean) < EARLY:
        return None, errors + [f"only {len(clean)} clean cycles"]

    qd = np.asarray([item[0] for item in clean])
    qc = np.asarray([item[1] for item in clean])
    features = make_features(qd, qc, clean[9][2], clean[99][2], np.nan, np.nan)
    life, censored = life_label(qd)
    row = {
        "cell_id": cell,
        "batch": "CALCE_LCO",
        "life": life,
        "censored": censored,
        "cycles_at_least_100": True,
    }
    row.update(features)
    return row, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    work = args.raw_dir / "_extract_work"
    work.mkdir(exist_ok=True)
    rows, errors = [], {}
    for archive in sorted(args.raw_dir.glob("C*.zip")):
        row, cell_errors = cell_table(archive, work)
        if row is not None:
            rows.append(row)
        if cell_errors:
            errors[archive.stem] = cell_errors
        print(
            f"{archive.stem}: "
            f"{'usable' if row is not None else 'unusable'} "
            f"errors={len(cell_errors)}",
            flush=True,
        )
    table = pd.DataFrame(rows)
    table.to_csv(args.out, index=False)
    audit = {
        "status": (
            "wrong-chemistry-control-eligible"
            if len(table.loc[~table["censored"].astype(bool)]) >= 8
            else "wrong-chemistry-control-unavailable"
        ),
        "source": "CALCE graphite/LCO prismatic cells",
        "archives": len(list(args.raw_dir.glob("C*.zip"))),
        "cells_with_early_features": int(len(table)),
        "uncensored_cells": int((~table["censored"].astype(bool)).sum()) if len(table) else 0,
        "errors": errors,
        "recipient_outcomes_opened": False,
    }
    audit_path = args.out.with_name("crosslab_fade_raw_wrong_chem_audit.json")
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(audit)


if __name__ == "__main__":
    main()
