"""Audit the frozen Caltech external ionic-conductor target without fitting policies."""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.common import composition_features, load_property  # noqa: E402
from scripts.localdb.build_localdb import canonical_formula  # noqa: E402

DESIGN_PATH = HERE / "caltech_ionic_external_policy_design.json"
AMENDMENT_PATH = HERE / "CALTECH_IONIC_SCHEMA_AMENDMENT.md"
TARGET_PATH = ROOT / "data" / "external" / "caltech_ionic" / "ionic_conductivity_database.csv"
OUTPUT_PATH = HERE / "results" / "caltech_ionic_external_audit.json"

COLUMNS = {
    "formula": "compound",
    "outcome": "conductivity_siemens_per_cm",
    "doi": "conductivity_doi",
    "icsd": "icsd_collectioncode",
    "temperature": "lowest_extrapolation_temperature_K",
}

SOURCE_SPECS = {
    "obelix_same_property": {
        "dataset": "obelix-solid-electrolytes",
        "property": "ionic_conductivity",
        "valid": lambda value: value > 0,
        "log10": True,
    },
    "estm_transport_neighbor": {
        "dataset": "estm-thermoelectric",
        "property": "ZT",
        "valid": lambda value: (value > 0) & (value <= 5),
        "log10": False,
    },
    "borg_mechanical_control": {
        "dataset": "mpea-dataset-borg",
        "property": "PROPERTY: YS (MPa)",
        "valid": lambda value: (value > 0) & (value <= 10000),
        "log10": True,
    },
    "ocx_catalysis_control": {
        "dataset": "ocx24-open-catalyst-experiments-2024",
        "property": "fe_h2",
        "valid": lambda value: (value >= 0) & (value <= 100),
        "log10": False,
    },
}

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;]+", re.IGNORECASE)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_dois(value: object) -> tuple[str, ...]:
    if pd.isna(value):
        return ()
    text = str(value).strip().lower()
    if not text or text in {"na", "nan", "none"}:
        return ()
    text = re.sub(r"https?://(?:dx\.)?doi\.org/", "", text)
    text = re.sub(r"^doi\s*:\s*", "", text)
    matches = DOI_RE.findall(text)
    if not matches and text.startswith("10."):
        matches = [text]
    return tuple(sorted({item.rstrip(".);]").lower() for item in matches}))


def normalize_icsd(value: object) -> tuple[str, ...]:
    if pd.isna(value):
        return ()
    text = str(value).strip().lower()
    if not text or text in {"na", "nan", "none"}:
        return ()
    tokens: list[str] = []
    for token in re.split(r"[,;|/]", text):
        token = token.strip()
        if re.fullmatch(r"\d+\.0", token):
            token = token[:-2]
        if token:
            tokens.append(token)
    return tuple(sorted(set(tokens)))


class DisjointSet:
    def __init__(self, size: int):
        self.parent = np.arange(size)

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[int(self.parent[index])]
            index = int(self.parent[index])
        return index

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def connected_groups(frame: pd.DataFrame) -> pd.Series:
    dsu = DisjointSet(len(frame))
    token_to_first: dict[str, int] = {}
    for position, row in enumerate(frame.itertuples(index=False)):
        tokens = [f"formula:{row.material_key}"]
        tokens.extend(f"doi:{item}" for item in row.normalized_dois)
        tokens.extend(f"icsd:{item}" for item in row.normalized_icsd)
        for token in tokens:
            if token in token_to_first:
                dsu.union(position, token_to_first[token])
            else:
                token_to_first[token] = position

    root_members: dict[int, list[int]] = defaultdict(list)
    for position in range(len(frame)):
        root_members[dsu.find(position)].append(position)
    labels: dict[int, str] = {}
    for root, positions in root_members.items():
        identity = "||".join(sorted(frame.iloc[positions]["material_key"].unique()))
        labels[root] = "component-" + hashlib.sha256(identity.encode()).hexdigest()[:16]
    return pd.Series([labels[dsu.find(i)] for i in range(len(frame))], index=frame.index)


def aggregate_target(frame: pd.DataFrame) -> pd.DataFrame:
    component_check = frame.groupby("material_key")["group"].nunique()
    if (component_check != 1).any():
        raise AssertionError("A canonical composition maps to multiple connected components")
    return (
        frame.groupby("material_key", as_index=False)
        .agg(
            value=("value", "median"),
            group=("group", "first"),
            n_raw=("value", "size"),
            material_raw=("compound", "first"),
        )
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def outcome_blind_split(entities: pd.DataFrame, seed: int) -> pd.DataFrame:
    group_sizes = entities.groupby("group").size().to_dict()
    ordered = sorted(
        group_sizes,
        key=lambda group: hashlib.sha256(f"{seed}|{group}".encode()).hexdigest(),
    )
    cumulative = np.cumsum([group_sizes[group] for group in ordered])
    target = 0.70 * len(entities)
    cut = int(np.argmin(np.abs(cumulative[:-1] - target))) + 1
    development = set(ordered[:cut])
    output = entities.copy()
    output["split"] = np.where(output["group"].isin(development), "development", "candidate")
    return output


def source_audit(target_keys: set[str], target_dois: set[str]) -> dict[str, object]:
    results: dict[str, object] = {}
    for source_id, spec in SOURCE_SPECS.items():
        frame = load_property(
            spec["dataset"],
            spec["property"],
            valid=spec["valid"],
            log10=bool(spec["log10"]),
        )
        frame["normalized_dois"] = frame["source_reference"].map(normalize_dois)
        formula_overlap = frame["material_key"].isin(target_keys)
        doi_overlap = frame["normalized_dois"].map(lambda values: bool(set(values) & target_dois))
        keep = ~(formula_overlap | doi_overlap)
        retained = frame[keep].copy()
        results[source_id] = {
            "raw_valid_rows": int(len(frame)),
            "raw_valid_entities": int(frame["material_key"].nunique()),
            "formula_overlap_rows": int(formula_overlap.sum()),
            "formula_overlap_entities": int(frame.loc[formula_overlap, "material_key"].nunique()),
            "doi_overlap_rows": int(doi_overlap.sum()),
            "doi_overlap_entities": int(frame.loc[doi_overlap, "material_key"].nunique()),
            "union_overlap_rows": int((formula_overlap | doi_overlap).sum()),
            "remaining_rows": int(len(retained)),
            "remaining_entities": int(retained["material_key"].nunique()),
            "remaining_unique_dois": int(
                len(set().union(*retained["normalized_dois"].tolist())) if len(retained) else 0
            ),
            "minimum_entity_gate": bool(retained["material_key"].nunique() >= 100),
        }
    return results


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    expected_columns = set(COLUMNS.values())
    header = set(pd.read_csv(TARGET_PATH, nrows=0).columns)
    if not expected_columns.issubset(header):
        missing = sorted(expected_columns - header)
        raise RuntimeError(f"Frozen schema amendment does not resolve columns: {missing}")
    target_md5 = file_hash(TARGET_PATH, "md5")
    if target_md5 != design["target"]["required_md5"]:
        raise RuntimeError(f"Target MD5 mismatch: {target_md5}")

    raw = pd.read_csv(TARGET_PATH)
    parsed_formula = raw[COLUMNS["formula"]].map(canonical_formula)
    raw["material_key"] = parsed_formula.map(lambda item: item[0])
    raw["formula_flag"] = parsed_formula.map(lambda item: item[1])
    raw["value_raw"] = pd.to_numeric(raw[COLUMNS["outcome"]], errors="coerce")
    raw["valid_outcome"] = np.isfinite(raw["value_raw"]) & (raw["value_raw"] > 0)
    raw["normalized_dois"] = raw[COLUMNS["doi"]].map(normalize_dois)
    raw["normalized_icsd"] = raw[COLUMNS["icsd"]].map(normalize_icsd)
    raw["temperature_K"] = pd.to_numeric(raw[COLUMNS["temperature"]], errors="coerce")

    formula_invalid = raw["material_key"].isna()
    outcome_invalid = ~raw["valid_outcome"]
    eligible = raw[~formula_invalid & ~outcome_invalid].copy()
    eligible["value"] = np.log10(eligible["value_raw"].astype(float))
    eligible["group"] = connected_groups(eligible)
    entities = aggregate_target(eligible)
    entities = outcome_blind_split(entities, int(design["target_split"]["seed"]))

    development = entities[entities["split"] == "development"].copy()
    candidate = entities[entities["split"] == "candidate"].copy()
    scaler = StandardScaler().fit(composition_features(development["material_key"].tolist()))
    development_x = scaler.transform(composition_features(development["material_key"].tolist()))
    candidate_x = scaler.transform(composition_features(candidate["material_key"].tolist()))
    _, distances = pairwise_distances_argmin_min(candidate_x, development_x)
    hard_n = max(1, int(math.ceil(0.40 * len(candidate))))
    hard_indices = np.argsort(distances)[-hard_n:]

    target_dois = set().union(*eligible["normalized_dois"].tolist())
    quality = design["target_quality_gates"]
    metrics = {
        "raw_rows": int(len(raw)),
        "invalid_formula_rows": int(formula_invalid.sum()),
        "invalid_formula_fraction": float(formula_invalid.mean()),
        "invalid_outcome_rows": int(outcome_invalid.sum()),
        "invalid_outcome_fraction": float(outcome_invalid.mean()),
        "nonempty_doi_rows": int(raw["normalized_dois"].map(bool).sum()),
        "nonempty_doi_fraction": float(raw["normalized_dois"].map(bool).mean()),
        "nonempty_icsd_rows": int(raw["normalized_icsd"].map(bool).sum()),
        "eligible_rows": int(len(eligible)),
        "unique_canonical_compositions": int(len(entities)),
        "connected_components": int(entities["group"].nunique()),
        "largest_component_entities": int(entities.groupby("group").size().max()),
        "temperature_numeric_rows": int(np.isfinite(raw["temperature_K"]).sum()),
        "near_room_temperature_eligible_rows": int(
            ((eligible["temperature_K"].notna()) & (eligible["temperature_K"] <= 350)).sum()
        ),
        "development_entities": int(len(development)),
        "candidate_entities": int(len(candidate)),
        "hard_ood_entities": int(len(hard_indices)),
    }
    gates = {
        "minimum_eligible_rows": metrics["eligible_rows"] >= int(quality["minimum_eligible_rows"]),
        "minimum_unique_canonical_compositions": metrics["unique_canonical_compositions"]
        >= int(quality["minimum_unique_canonical_compositions"]),
        "maximum_invalid_formula_fraction": metrics["invalid_formula_fraction"]
        <= float(quality["maximum_invalid_or_unparseable_formula_fraction"]),
        "maximum_invalid_outcome_fraction": metrics["invalid_outcome_fraction"]
        <= float(quality["maximum_nonpositive_or_nonnumeric_outcome_fraction"]),
        "minimum_nonempty_doi_fraction": metrics["nonempty_doi_fraction"]
        >= float(quality["minimum_nonempty_doi_fraction"]),
        "minimum_development_entities": metrics["development_entities"]
        >= int(design["target_split"]["minimum_development_entities"]),
        "minimum_candidate_entities": metrics["candidate_entities"]
        >= int(design["target_split"]["minimum_candidate_entities"]),
    }
    sources = source_audit(set(eligible["material_key"]), target_dois)
    all_sources_pass = all(item["minimum_entity_gate"] for item in sources.values())
    report = {
        "status": "pass" if all(gates.values()) and all_sources_pass else "fail",
        "design_sha256": file_hash(DESIGN_PATH, "sha256"),
        "schema_amendment_sha256": file_hash(AMENDMENT_PATH, "sha256"),
        "target_md5": target_md5,
        "resolved_columns": COLUMNS,
        "target_metrics": metrics,
        "target_gates": gates,
        "source_leakage_audit": sources,
        "all_target_gates_pass": bool(all(gates.values())),
        "all_source_minimums_pass": bool(all_sources_pass),
        "protocol_deviation": "Header inspection accidentally displayed two target data rows; no analysis rule changed.",
    }
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(report, indent=2))
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
