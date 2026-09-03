"""Freeze outcome-free Starrydata target state before reading target ZT values.

This program deliberately never requests the ``y`` column from the Starrydata
curve file.  It writes the target metadata, provenance/component split, source
predictions and ranks, fixed policy orders, matched hypothesis cards, and a
hash sentinel.  The formal outcome runner must verify that sentinel before it
is allowed to parse target outcomes.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import MiniBatchKMeans
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.audit_caltech_ionic_external_target import (  # noqa: E402
    COLUMNS as CALTECH_COLUMNS,
    TARGET_PATH as CALTECH_PATH,
    connected_groups as caltech_connected_groups,
    normalize_dois,
)
from analysis.common import composition_features  # noqa: E402
from analysis.run_caltech_ionic_external_policy import source_entities  # noqa: E402
from scripts.localdb.build_localdb import canonical_formula  # noqa: E402

DESIGN_PATH = HERE / "starrydata_reverse_transport_design.json"
SCHEMA_PATH = HERE / "STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md"
IMPLEMENTATION_PATH = HERE / "starrydata_reverse_transport_implementation.json"
INPUT_DIR = ROOT / "data" / "external" / "starrydata_2026-07-17"
CURVES_PATH = INPUT_DIR / "ThermoelectricMaterials_curves.csv.gz"
SAMPLES_PATH = INPUT_DIR / "ThermoelectricMaterials_samples.csv.gz"
PAPERS_PATH = INPUT_DIR / "ThermoelectricMaterials_papers.csv.gz"
RESULTS = HERE / "results"

METADATA_PATH = RESULTS / "starrydata_reverse_target_metadata.csv"
SOURCE_PREDICTIONS_PATH = RESULTS / "starrydata_reverse_source_predictions.csv"
SOURCE_QUALITY_PATH = RESULTS / "starrydata_reverse_source_quality.csv"
POLICY_PATH = RESULTS / "starrydata_reverse_policy_orders.csv"
CARDS_PATH = RESULTS / "starrydata_reverse_hypothesis_cards.csv"
FREEZE_PATH = RESULTS / "starrydata_reverse_PREOUTCOME.json"

SALT = "starrydata-reverse-transport-v1"
TARGET_TEMPERATURE = 800.0
TEMPERATURE_TOLERANCE = 25.0
SEED = 20260718
SOURCE_IDS = [
    "estm_same_domain",
    "obelix_adjacent_ionic",
    "caltech_adjacent_ionic",
    "borg_wrong_mechanical",
    "ocx_wrong_catalysis",
]
SQLITE_SOURCE_MAP = {
    "estm_same_domain": "estm_transport_neighbor",
    "obelix_adjacent_ionic": "obelix_same_property",
    "borg_wrong_mechanical": "borg_mechanical_control",
    "ocx_wrong_catalysis": "ocx_catalysis_control",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_unit(label: str) -> float:
    value = int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], "big")
    return value / float(2**64 - 1)


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "little")


def parse_numeric_list(value: object) -> list[float]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, (list, tuple, np.ndarray)):
        return []
    output: list[float] = []
    for item in parsed:
        try:
            output.append(float(item))
        except (TypeError, ValueError):
            output.append(float("nan"))
    return output


class DisjointSet:
    def __init__(self, size: int):
        self.parent = np.arange(size)

    def find(self, index: int) -> int:
        while self.parent[index] != index:
            self.parent[index] = self.parent[int(self.parent[index])]
            index = int(self.parent[index])
        return index

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def first_nonempty(values: Iterable[object]) -> str:
    for value in values:
        if pd.notna(value) and str(value).strip() and str(value).lower() != "nan":
            return str(value).strip()
    return ""


def doi_token(value: object) -> str:
    values = normalize_dois(value)
    return values[0] if values else ""


def verify_inputs(design: dict) -> None:
    expected = design["source_snapshot"]["files"]
    paths = {"curves": CURVES_PATH, "samples": SAMPLES_PATH, "papers": PAPERS_PATH}
    for role, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        observed = sha256(path)
        if observed != expected[role]["sha256"]:
            raise AssertionError(f"{role} hash mismatch: {observed}")


def build_curve_metadata() -> tuple[pd.DataFrame, dict[str, int]]:
    # The target outcome column ``y`` is intentionally absent from usecols.
    columns = [
        "SID", "DOI", "composition", "sample_id", "figure_id", "figure_name",
        "prop_x", "prop_y", "unit_x", "unit_y", "x", "created_at", "updated_at",
    ]
    curves = pd.read_csv(CURVES_PATH, usecols=columns, low_memory=False)
    descriptor = (
        curves["prop_y"].eq("ZT")
        & curves["unit_y"].eq("-")
        & curves["prop_x"].isin(["Temperature", "T"])
        & curves["unit_x"].eq("K")
    )
    curves = curves.loc[descriptor].copy()
    curves["curve_row"] = curves.index.astype(int)
    selected_position: list[int | None] = []
    selected_temperature: list[float] = []
    for value in curves["x"]:
        temperatures = parse_numeric_list(value)
        eligible = [
            (abs(temp - TARGET_TEMPERATURE), temp, position)
            for position, temp in enumerate(temperatures)
            if math.isfinite(temp) and abs(temp - TARGET_TEMPERATURE) <= TEMPERATURE_TOLERANCE
        ]
        if not eligible:
            selected_position.append(None)
            selected_temperature.append(float("nan"))
        else:
            _, temperature, position = min(eligible)
            selected_position.append(position)
            selected_temperature.append(temperature)
    curves["selected_position"] = pd.array(selected_position, dtype="Int64")
    curves["selected_temperature_K"] = selected_temperature
    curves = curves[curves["selected_position"].notna()].copy()

    sample_columns = [
        "SID", "DOI", "sample_id", "sample_name", "composition",
        "composition_details", "sample_info", "created_at", "updated_at",
    ]
    samples = pd.read_csv(SAMPLES_PATH, usecols=sample_columns, low_memory=False)
    samples = samples.sort_values(["SID", "sample_id", "updated_at"]).drop_duplicates(
        ["SID", "sample_id"], keep="last"
    )
    samples = samples.rename(
        columns={
            "DOI": "sample_DOI",
            "composition": "sample_composition",
            "created_at": "sample_created_at",
            "updated_at": "sample_updated_at",
        }
    )
    paper_columns = ["SID", "DOI", "URL", "issued", "title", "created_at"]
    papers = pd.read_csv(PAPERS_PATH, usecols=paper_columns, low_memory=False)
    papers = papers.sort_values(["SID", "created_at"]).drop_duplicates("SID", keep="last")
    papers = papers.rename(
        columns={
            "DOI": "paper_DOI",
            "created_at": "paper_created_at",
        }
    )

    merged = curves.merge(samples, on=["SID", "sample_id"], how="left", validate="many_to_one")
    merged = merged.merge(papers, on="SID", how="left", validate="many_to_one")
    merged["formula_raw"] = [
        first_nonempty([curve_formula, sample_formula])
        for curve_formula, sample_formula in zip(merged["composition"], merged["sample_composition"])
    ]
    parsed = merged["formula_raw"].map(canonical_formula)
    merged["material_key"] = parsed.map(lambda item: item[0])
    merged["formula_issue"] = parsed.map(lambda item: item[1] or "")
    for column in ["DOI", "sample_DOI", "paper_DOI"]:
        merged[f"normalized_{column}"] = merged[column].map(doi_token)
    doi_sets = merged[["normalized_DOI", "normalized_sample_DOI", "normalized_paper_DOI"]].apply(
        lambda row: {value for value in row if value}, axis=1
    )
    merged["doi_disagreement"] = doi_sets.map(lambda values: len(values) > 1)
    merged["normalized_doi"] = merged[
        ["normalized_DOI", "normalized_sample_DOI", "normalized_paper_DOI"]
    ].apply(lambda row: first_nonempty(row), axis=1)
    counts = {
        "descriptor_rows": int(descriptor.sum()),
        "temperature_window_rows": int(len(curves)),
        "unparsed_formula_rows": int(merged["material_key"].isna().sum()),
        "doi_disagreement_rows": int(merged["doi_disagreement"].sum()),
    }
    eligible = merged[merged["material_key"].notna() & ~merged["doi_disagreement"]].copy()
    if eligible.empty:
        raise RuntimeError("No eligible outcome-free target metadata")
    return eligible, counts


def connected_target_components(entities: pd.DataFrame) -> pd.Series:
    dsu = DisjointSet(len(entities))
    first: dict[str, int] = {}
    for position, row in enumerate(entities.itertuples(index=False)):
        tokens = [f"formula:{row.material_key}", f"sample:{row.SID}|{row.sample_id}"]
        tokens.append(f"provenance:{row.provenance_group}")
        for token in tokens:
            if token in first:
                dsu.union(position, first[token])
            else:
                first[token] = position
    roots = [dsu.find(position) for position in range(len(entities))]
    labels: dict[int, str] = {}
    for root in sorted(set(roots)):
        members = [index for index, value in enumerate(roots) if value == root]
        identity = "||".join(sorted(entities.iloc[members]["entity_id"].astype(str)))
        labels[root] = "component-" + hashlib.sha256(identity.encode()).hexdigest()[:16]
    return pd.Series([labels[root] for root in roots], index=entities.index)


def assign_split(entities: pd.DataFrame) -> pd.Series:
    sizes = entities.groupby("component_id").size().to_dict()
    ordered = sorted(sizes, key=lambda group: hashlib.sha256(f"{SALT}|{group}".encode()).hexdigest())
    split_by_group: dict[str, str] = {}
    cumulative = 0
    total = len(entities)
    for group in ordered:
        midpoint = (cumulative + 0.5 * sizes[group]) / total
        split = "development" if midpoint < 0.60 else "validation" if midpoint < 0.80 else "evaluation"
        split_by_group[group] = split
        cumulative += sizes[group]
    return entities["component_id"].map(split_by_group)


def aggregate_metadata(curves: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["SID", "sample_id", "material_key"]
    rows: list[dict] = []
    for keys, local in curves.groupby(group_columns, sort=True, dropna=False):
        sid, sample_id, material_key = keys
        normalized_doi = first_nonempty(local["normalized_doi"])
        provenance_group = normalized_doi or f"sid:{sid}"
        identity = f"{sid}|{sample_id}|{material_key}"
        rows.append(
            {
                "entity_id": "starry-" + hashlib.sha256(identity.encode()).hexdigest()[:20],
                "SID": sid,
                "sample_id": sample_id,
                "material_key": material_key,
                "formula_raw": first_nonempty(local["formula_raw"]),
                "normalized_doi": normalized_doi,
                "provenance_group": provenance_group,
                "sample_name": first_nonempty(local["sample_name"]),
                "sample_info": first_nonempty(local["sample_info"]),
                "composition_details": first_nonempty(local["composition_details"]),
                "curve_rows": ";".join(str(int(value)) for value in sorted(local["curve_row"])),
                "selected_positions": ";".join(str(int(value)) for value in local["selected_position"]),
                "selected_temperatures_K": ";".join(f"{float(value):.8g}" for value in local["selected_temperature_K"]),
                "replicate_curves": int(len(local)),
            }
        )
    entities = pd.DataFrame(rows).sort_values("entity_id").reset_index(drop=True)
    entities["component_id"] = connected_target_components(entities)
    entities["split"] = assign_split(entities)
    x = composition_features(entities["material_key"].tolist()).astype(np.float32)
    development = entities["split"].eq("development").to_numpy()
    scaler = StandardScaler().fit(x[development])
    x_scaled = scaler.transform(x)
    clusters = min(max(40, len(entities) // 25), 160, len(entities))
    model = MiniBatchKMeans(n_clusters=clusters, random_state=SEED, batch_size=1024, n_init=10)
    entities["composition_cluster"] = [f"cluster-{value:03d}" for value in model.fit_predict(x_scaled)]
    dev_x = x_scaled[development]
    distance = NearestNeighbors(n_neighbors=1, metric="euclidean").fit(dev_x).kneighbors(
        x_scaled, return_distance=True
    )[0][:, 0]
    entities["distance_to_development"] = distance
    entities["ood_quartile"] = 0
    for split in ["validation", "evaluation"]:
        mask = entities["split"].eq(split)
        if mask.sum() >= 4:
            entities.loc[mask, "ood_quartile"] = pd.qcut(
                entities.loc[mask, "distance_to_development"], 4, labels=[1, 2, 3, 4], duplicates="drop"
            ).astype(int)
    return entities


def load_caltech_source(target_keys: set[str], target_dois: set[str]) -> pd.DataFrame:
    columns = [CALTECH_COLUMNS["formula"], CALTECH_COLUMNS["outcome"], CALTECH_COLUMNS["doi"]]
    raw = pd.read_csv(CALTECH_PATH, usecols=columns)
    parsed = raw[CALTECH_COLUMNS["formula"]].map(canonical_formula)
    raw["material_key"] = parsed.map(lambda item: item[0])
    raw["value_raw"] = pd.to_numeric(raw[CALTECH_COLUMNS["outcome"]], errors="coerce")
    raw["normalized_dois"] = raw[CALTECH_COLUMNS["doi"]].map(normalize_dois)
    raw["normalized_icsd"] = [()] * len(raw)
    valid = raw["material_key"].notna() & np.isfinite(raw["value_raw"]) & (raw["value_raw"] > 0)
    raw = raw[valid].copy()
    overlap = raw["material_key"].isin(target_keys) | raw["normalized_dois"].map(
        lambda values: bool(set(values) & target_dois)
    )
    raw = raw[~overlap].reset_index(drop=True)
    raw["value"] = np.log10(raw["value_raw"].astype(float))
    raw["group"] = caltech_connected_groups(raw)
    return (
        raw.groupby("material_key", as_index=False)
        .agg(value=("value", "median"), group=("group", "first"), n_raw=("value", "size"))
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def fit_source(
    source_id: str, frame: pd.DataFrame, target_x: np.ndarray
) -> tuple[np.ndarray, np.ndarray, dict]:
    x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    y = frame["value"].to_numpy(float)
    groups = frame["group"].astype(str).to_numpy()
    n_splits = min(5, len(np.unique(groups)))
    if n_splits < 3:
        raise RuntimeError(f"{source_id}: insufficient independent groups")
    splitter = GroupKFold(n_splits=n_splits, shuffle=True, random_state=stable_seed(source_id))
    oof = np.full(len(frame), np.nan)
    for fold, (train, test) in enumerate(splitter.split(x, y, groups)):
        model = ExtraTreesRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=stable_seed(f"{source_id}|fold|{fold}"),
            n_jobs=-1,
        )
        model.fit(x[train], y[train])
        oof[test] = model.predict(x[test])
    model = ExtraTreesRegressor(
        n_estimators=400,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=stable_seed(f"{source_id}|full"),
        n_jobs=-1,
    )
    model.fit(x, y)
    prediction = model.predict(target_x)
    coverage_distance = NearestNeighbors(n_neighbors=1, metric="euclidean").fit(x).kneighbors(
        target_x, return_distance=True
    )[0][:, 0]
    quality = {
        "source": source_id,
        "entities": int(len(frame)),
        "groups": int(len(np.unique(groups))),
        "oof_r2": float(r2_score(y, oof)),
        "oof_rmse": float(math.sqrt(mean_squared_error(y, oof))),
        "oof_spearman": float(stats.spearmanr(y, oof).statistic),
        "target_formula_exclusions": int(frame.attrs.get("target_formula_exclusions", 0)),
        "target_doi_exclusions": int(frame.attrs.get("target_doi_exclusions", 0)),
    }
    return prediction, coverage_distance, quality


def fit_sources(entities: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_keys = set(entities["material_key"])
    target_dois = {value for value in entities["normalized_doi"] if value}
    target_x = composition_features(entities["material_key"].tolist()).astype(np.float32)
    predictions = entities[["entity_id", "split", "component_id", "composition_cluster"]].copy()
    quality_rows: list[dict] = []
    for source_id in SOURCE_IDS:
        if source_id == "caltech_adjacent_ionic":
            frame = load_caltech_source(target_keys, target_dois)
        else:
            frame = source_entities(SQLITE_SOURCE_MAP[source_id], target_keys, target_dois)
        prediction, coverage_distance, quality = fit_source(source_id, frame, target_x)
        predictions[f"{source_id}_prediction"] = prediction
        predictions[f"{source_id}_rank"] = pd.Series(prediction).rank(method="average", pct=True).to_numpy()
        predictions[f"{source_id}_coverage_distance"] = coverage_distance
        quality_rows.append(quality)
    for source_id in ["obelix_adjacent_ionic", "caltech_adjacent_ionic"]:
        rank = predictions[f"{source_id}_rank"].to_numpy()
        predictions[f"shuffled_{source_id}_rank"] = np.random.default_rng(
            stable_seed(f"preoutcome-shuffle|{source_id}")
        ).permutation(rank)
    rng = np.random.default_rng(stable_seed("equal-capacity-random-features"))
    for index in range(len(SOURCE_IDS)):
        predictions[f"random_feature_{index + 1}"] = rng.standard_normal(len(predictions))
    return predictions, pd.DataFrame(quality_rows)


def family_first_order(frame: pd.DataFrame, score: pd.Series, group_column: str) -> list[int]:
    ordered = list(frame.assign(_score=score).sort_values(["_score", "entity_id"], ascending=[False, True]).index)
    first_pass: list[int] = []
    remainder: list[int] = []
    seen: set[str] = set()
    for index in ordered:
        group = str(frame.at[index, group_column])
        if group not in seen:
            seen.add(group)
            first_pass.append(index)
        else:
            remainder.append(index)
    return first_pass + remainder


def round_robin_order(frame: pd.DataFrame, rank_columns: list[str]) -> list[int]:
    queues = [list(frame.sort_values([column, "entity_id"], ascending=[False, True]).index) for column in rank_columns]
    output: list[int] = []
    used_entities: set[int] = set()
    used_components: set[str] = set()
    deferred: list[int] = []
    while any(queues):
        for queue in queues:
            while queue:
                index = queue.pop(0)
                if index in used_entities:
                    continue
                used_entities.add(index)
                component = str(frame.at[index, "component_id"])
                if component in used_components:
                    deferred.append(index)
                else:
                    used_components.add(component)
                    output.append(index)
                break
    return output + deferred


def build_policy_orders(entities: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    merged = entities.merge(predictions, on=["entity_id", "split", "component_id", "composition_cluster"])
    pool = merged[merged["split"].eq("evaluation")].copy().reset_index(drop=True)
    ranks = {source: f"{source}_rank" for source in SOURCE_IDS}
    neighbor_columns = [ranks["estm_same_domain"], ranks["obelix_adjacent_ionic"], ranks["caltech_adjacent_ionic"]]
    wrong_columns = [ranks["borg_wrong_mechanical"], ranks["ocx_wrong_catalysis"]]
    consensus = pool[neighbor_columns].mean(axis=1)
    wrong_consensus = pool[wrong_columns].mean(axis=1)
    shuffled = pd.Series(
        np.random.default_rng(stable_seed("shuffled-neighbor-policy")).permutation(consensus.to_numpy()),
        index=pool.index,
    )
    random_score = pool["entity_id"].map(lambda value: stable_unit(f"uniform|{value}"))
    policies: dict[str, list[int]] = {
        "uniform_family_first": family_first_order(pool, random_score, "component_id"),
        "composition_novelty_family_first": family_first_order(pool, pool["distance_to_development"], "component_id"),
        "estm_best_same_domain": family_first_order(pool, pool[ranks["estm_same_domain"]], "component_id"),
        "obelix_adjacent_single": family_first_order(pool, pool[ranks["obelix_adjacent_ionic"]], "component_id"),
        "caltech_adjacent_single": family_first_order(pool, pool[ranks["caltech_adjacent_ionic"]], "component_id"),
        "neighbor_entity_consensus": list(pool.assign(_score=consensus).sort_values(["_score", "entity_id"], ascending=[False, True]).index),
        "cca_family_first_consensus": family_first_order(pool, consensus, "component_id"),
        "cca_family_first_round_robin": round_robin_order(pool, neighbor_columns),
        "wrong_source_family_first": family_first_order(pool, wrong_consensus, "component_id"),
        "shuffled_neighbor_family_first": family_first_order(pool, shuffled, "component_id"),
    }
    rows: list[dict] = []
    for policy, order in policies.items():
        for position, index in enumerate(order, start=1):
            row = pool.loc[index]
            rows.append(
                {
                    "policy": policy,
                    "position": position,
                    "entity_id": row["entity_id"],
                    "component_id": row["component_id"],
                    "composition_cluster": row["composition_cluster"],
                    "ood_quartile": int(row["ood_quartile"]),
                }
            )
    return pd.DataFrame(rows)


def element_set(key: str) -> set[str]:
    return {token.split(":", 1)[0] for token in key.split("|")}


def region_summary(pool: pd.DataFrame, indices: list[int]) -> str:
    region = pool.loc[indices]
    counts: defaultdict[str, int] = defaultdict(int)
    for key in region["material_key"]:
        for element in element_set(key):
            counts[element] += 1
    common = sorted(counts, key=lambda element: (-counts[element], element))[:6]
    return "top-ranked evaluation compositions enriched in " + ", ".join(common)


def matched_controls(pool: pd.DataFrame, candidate_indices: list[int], score: pd.Series) -> list[str]:
    selected: list[str] = []
    available = set(pool.index) - set(candidate_indices)
    for index in candidate_indices:
        if not available:
            break
        target = pool.loc[index]
        match = min(
            available,
            key=lambda other: (
                abs(float(pool.at[other, "distance_to_development"]) - float(target["distance_to_development"])),
                abs(float(score.at[other]) - 0.5),
                str(pool.at[other, "entity_id"]),
            ),
        )
        selected.append(str(pool.at[match, "entity_id"]))
        available.remove(match)
    return selected


def build_hypothesis_cards(entities: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    pool = entities.merge(predictions, on=["entity_id", "split", "component_id", "composition_cluster"])
    pool = pool[pool["split"].eq("evaluation")].copy().reset_index(drop=True)
    specifications = [
        (
            "H1_obelix_ionic_region",
            "obelix_adjacent_ionic_rank",
            "Ionic-transport composition rank identifies a thermoelectric target region beyond composition novelty.",
            "Shared lattice softness, disorder and defect-tolerant transport can create a useful composition prior even though ionic and electronic carriers differ.",
        ),
        (
            "H2_caltech_ionic_region",
            "caltech_adjacent_ionic_rank",
            "An independent ionic-conductivity source contributes a distinct high-ZT component beyond ESTM and OBELiX.",
            "Independent conductivity evidence tests whether the signal is a transport-neighborhood prior rather than one source-dataset accident.",
        ),
        (
            "H3_neighbor_consensus_region",
            "neighbor_consensus_rank",
            "Agreement and complementarity across ESTM and two ionic sources enrich distinct high-ZT components in hard OOD.",
            "Consensus supplies joint support while family-first allocation prevents repeated members of one familiar composition family from consuming the budget.",
        ),
    ]
    pool["neighbor_consensus_rank"] = pool[
        ["estm_same_domain_rank", "obelix_adjacent_ionic_rank", "caltech_adjacent_ionic_rank"]
    ].mean(axis=1)
    rows: list[dict] = []
    number = max(5, int(math.ceil(0.05 * len(pool))))
    for card_id, score_column, hypothesis, rationale in specifications:
        score = pool[score_column]
        candidates = list(pool.assign(_score=score).sort_values(["_score", "entity_id"], ascending=[False, True]).head(number).index)
        controls = matched_controls(pool, candidates, score)
        rows.append(
            {
                "card_id": card_id,
                "written_before_target_outcome": True,
                "source_evidence": score_column,
                "hypothesis": hypothesis,
                "candidate_region": region_summary(pool, candidates),
                "candidate_entity_ids": ";".join(pool.loc[candidates, "entity_id"]),
                "matched_target_only_control_entity_ids": ";".join(controls),
                "physical_rationale": rationale,
                "falsifier": "No Holm-adjusted enrichment beyond novelty, shuffled ranks, and size/skill/coverage-matched wrong sources, or no unique adjacent-source component at budget 20.",
                "planned_mechanistic_measurement": "Compare phase/provenance context and temperature-local transport descriptors for every hit and matched control; do not infer microscopic mechanism from feature importance.",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    verify_inputs(design)
    RESULTS.mkdir(parents=True, exist_ok=True)
    curves, audit_counts = build_curve_metadata()
    entities = aggregate_metadata(curves)
    if len(entities) < 100 or entities["component_id"].nunique() < 40 or entities["provenance_group"].nunique() < 20:
        raise AssertionError("Frozen minimum target quality gate failed")
    predictions, source_quality = fit_sources(entities)
    policies = build_policy_orders(entities, predictions)
    cards = build_hypothesis_cards(entities, predictions)

    # None of the written tables contains target ZT or a generic y column.
    for frame in [entities, predictions, source_quality, policies, cards]:
        forbidden = {column.lower() for column in frame.columns} & {"y", "zt", "target_value", "outcome"}
        if forbidden:
            raise AssertionError(f"Outcome leaked into pre-outcome artifact: {sorted(forbidden)}")
    entities.to_csv(METADATA_PATH, index=False)
    predictions.to_csv(SOURCE_PREDICTIONS_PATH, index=False)
    source_quality.to_csv(SOURCE_QUALITY_PATH, index=False)
    policies.to_csv(POLICY_PATH, index=False)
    cards.to_csv(CARDS_PATH, index=False)

    artifacts = [
        DESIGN_PATH,
        SCHEMA_PATH,
        IMPLEMENTATION_PATH,
        Path(__file__).resolve(),
        HERE / "verify_starrydata_reverse_preoutcome.py",
        HERE / "run_starrydata_reverse_transport.py",
        METADATA_PATH,
        SOURCE_PREDICTIONS_PATH,
        SOURCE_QUALITY_PATH,
        POLICY_PATH,
        CARDS_PATH,
    ]
    freeze = {
        "status": "preoutcome-frozen",
        "claim_guard": "Target ZT values were not loaded. Any subsequent design change is outcome-informed and cannot alter the primary family.",
        "input_hashes": {
            "curves": sha256(CURVES_PATH),
            "samples": sha256(SAMPLES_PATH),
            "papers": sha256(PAPERS_PATH),
        },
        "audit_counts": audit_counts,
        "target_entities": int(len(entities)),
        "target_components": int(entities["component_id"].nunique()),
        "composition_clusters": int(entities["composition_cluster"].nunique()),
        "provenance_groups": int(entities["provenance_group"].nunique()),
        "split_counts": entities["split"].value_counts().sort_index().to_dict(),
        "source_quality_rows": int(len(source_quality)),
        "policy_rows": int(len(policies)),
        "hypothesis_cards": int(len(cards)),
        "artifact_hashes": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in artifacts},
    }
    FREEZE_PATH.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
