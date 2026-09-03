"""Freeze TRI OER compositions, source ranks, policies, and cards without decoding FOM."""
from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.common import composition_features  # noqa: E402
from analysis.prepare_caltech_acid_oer_neighbor import (  # noqa: E402
    ORR,
    fit_source,
    load_orr_source,
    material_key,
)
from analysis.run_caltech_ionic_external_policy import source_entities  # noqa: E402

DESIGN = HERE / "tri_oer_neighbor_design.json"
SCHEMA = HERE / "TRI_OER_PICKLE_SCHEMA_AMENDMENT.md"
REPLACEMENT = HERE / "TRI_OER_CLEAN_REPLACEMENT_PROTOCOL.md"
PROGRAM = HERE / "outcome_unseen_neighbor_validation_program.json"
PICKLE = ROOT / "data" / "external" / "tri_oer" / "tri_data_share.pck"
ACID_TARGET = ROOT / "data" / "external" / "caltech_acid_oer" / "extracted" / "data" / "OER" / "oer_all_foms.csv"
RESULTS = HERE / "results"
METADATA = RESULTS / "tri_oer_target_metadata.csv"
PREDICTIONS = RESULTS / "tri_oer_source_predictions.csv"
QUALITY = RESULTS / "tri_oer_source_quality.csv"
POLICIES = RESULTS / "tri_oer_policy_orders.csv"
CARDS = RESULTS / "tri_oer_hypothesis_cards.csv"
MATCHED_CONTROLS = RESULTS / "tri_oer_matched_source_controls.csv"
FREEZE = RESULTS / "tri_oer_PREOUTCOME.json"

PLATE_ELEMENTS = {
    "3496": ["Mn", "Fe", "Co", "Ni", "La", "Ce"],
    "3851": ["Mn", "Fe", "Co", "Ni", "Cu", "Ta"],
    "3860": ["Mn", "Fe", "Co", "Cu", "Sn", "Ta"],
    "4098": ["Ca", "Mn", "Co", "Ni", "Sn", "Sb"],
}
SEED = 20260718
SOURCE_MAP = {
    "ocx_adjacent_electrocatalysis": "ocx_catalysis_control",
    "borg_wrong_mechanical": "borg_mechanical_control",
    "obelix_wrong_ionic": "obelix_same_property",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "little")


class DTypeStub:
    def __init__(self, *args):
        self.args = args

    def __setstate__(self, state):
        self.state = state


class ArrayStub:
    def __setstate__(self, state):
        self.shape = tuple(state[1])
        self.dtype_name = str(state[2].args[0])
        self.raw = state[4]

    def decode(self) -> np.ndarray:
        return np.frombuffer(self.raw, dtype=np.dtype(self.dtype_name)).reshape(self.shape).copy()


def reconstruct_array(*_args):
    return ArrayStub()


class SchemaUnpickler(pickle.Unpickler):
    """Allow only the NumPy constructors needed to retain undecoded buffers."""

    def find_class(self, module, name):
        if module in {"numpy.core.multiarray", "numpy._core.multiarray"} and name == "_reconstruct":
            return reconstruct_array
        if module == "numpy" and name == "ndarray":
            return ArrayStub
        if module == "numpy" and name == "dtype":
            return DTypeStub
        raise pickle.UnpicklingError(f"Blocked pickle global: {module}.{name}")


def load_schema() -> dict:
    with PICKLE.open("rb") as handle:
        value = SchemaUnpickler(handle, encoding="latin1").load()
    if not isinstance(value, dict):
        raise AssertionError("TRI target is not a dictionary")
    return value


def target_metadata() -> tuple[pd.DataFrame, dict]:
    schema = load_schema()
    if not set(PLATE_ELEMENTS).issubset(schema) or "3875" not in schema:
        raise AssertionError("Unexpected TRI plate dictionary")
    rows: list[dict] = []
    decoded_buffers: list[str] = []
    for plate, elements in PLATE_ELEMENTS.items():
        entry = schema[plate]
        comp = entry["comp"].decode()
        decoded_buffers.append(f"{plate}:comp")
        if comp.ndim != 2 or comp.shape[1] != len(elements):
            raise AssertionError(f"{plate}: composition shape mismatch")
        for row_index, fractions in enumerate(comp):
            key = material_key(elements, fractions)
            if key is None:
                continue
            identity = f"{plate}|{row_index}|{key}"
            rows.append(
                {
                    "entity_id": "tri-oer-" + hashlib.sha256(identity.encode()).hexdigest()[:20],
                    "plate": plate,
                    "original_row": row_index,
                    "material_key": key,
                    "element_system": "-".join(elements),
                }
            )
        # Outcome and indexing buffers are explicitly discarded undecoded.
        for forbidden in ["fom", "sno", "runint"]:
            del entry[forbidden].raw
        del entry["comp"].raw
    metadata = pd.DataFrame(rows).sort_values(["plate", "original_row"]).reset_index(drop=True)
    x = composition_features(metadata["material_key"].tolist()).astype(np.float32)
    x_scaled = StandardScaler().fit_transform(x)
    clusters = min(240, max(80, len(metadata) // 30), len(metadata))
    labels = MiniBatchKMeans(
        n_clusters=clusters, random_state=SEED, n_init=10, batch_size=1024
    ).fit_predict(x_scaled)
    metadata["composition_cluster"] = [f"tri-cluster-{label:03d}" for label in labels]
    metadata["ood_distance_leave_plate_out"] = np.nan
    metadata["ood_quartile"] = 0
    for plate in PLATE_ELEMENTS:
        evaluation = metadata["plate"].eq(plate).to_numpy()
        development = ~evaluation
        distance = NearestNeighbors(n_neighbors=1).fit(x_scaled[development]).kneighbors(
            x_scaled[evaluation], return_distance=True
        )[0][:, 0]
        metadata.loc[evaluation, "ood_distance_leave_plate_out"] = distance
        metadata.loc[evaluation, "ood_quartile"] = pd.qcut(
            pd.Series(distance), 4, labels=[1, 2, 3, 4], duplicates="drop"
        ).astype(int).to_numpy()
    metadata["outer_fold"] = metadata["plate"].map(lambda plate: f"holdout-plate-{plate}")
    schema_audit = {
        "pickle_keys": sorted(schema),
        "retained_plates": sorted(PLATE_ELEMENTS),
        "excluded_plate": "3875",
        "decoded_buffers": decoded_buffers,
        "undecoded_target_buffers": [f"{plate}:fom" for plate in sorted(PLATE_ELEMENTS)],
    }
    return metadata, schema_audit


def load_acid_source(target_keys: set[str]) -> pd.DataFrame:
    columns = ["plate", "Mn", "Sb", "Sn", "Ti", "Co", "J_t200"]
    raw = pd.read_csv(ACID_TARGET, usecols=columns)
    elements = ["Mn", "Sb", "Sn", "Ti", "Co"]
    for column in elements + ["J_t200"]:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    raw["material_key"] = [material_key(elements, fractions) for fractions in raw[elements].to_numpy(float)]
    raw["value"] = raw["J_t200"]
    raw = raw[raw["material_key"].notna() & np.isfinite(raw["value"])].copy()
    raw = raw[~raw["material_key"].isin(target_keys)].copy()
    raw["group"] = raw["plate"].astype(str).map(lambda value: f"acid-plate-{value}")
    return (
        raw.groupby("material_key", as_index=False)
        .agg(value=("value", "median"), group=("group", "first"), n_raw=("value", "size"))
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def source_predictions(
    metadata: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    target_keys = set(metadata["material_key"])
    target_x = composition_features(metadata["material_key"].tolist()).astype(np.float32)
    frames = {
        "acid_oer_same_reaction": load_acid_source(target_keys),
        "orr_adjacent_oxygen_electrocatalysis": load_orr_source(target_keys),
        "ocx_adjacent_electrocatalysis": source_entities(
            SOURCE_MAP["ocx_adjacent_electrocatalysis"], target_keys, set()
        ),
        "borg_wrong_mechanical": source_entities(SOURCE_MAP["borg_wrong_mechanical"], target_keys, set()),
        "obelix_wrong_ionic": source_entities(SOURCE_MAP["obelix_wrong_ionic"], target_keys, set()),
    }
    output = metadata[["entity_id", "plate", "composition_cluster"]].copy()
    quality_rows: list[dict] = []
    for source_id, frame in frames.items():
        prediction, coverage, quality = fit_source(source_id, frame, target_x)
        output[f"{source_id}_prediction"] = prediction
        output[f"{source_id}_rank"] = pd.Series(prediction).rank(method="average", pct=True).to_numpy()
        output[f"{source_id}_coverage_distance"] = coverage
        quality_rows.append(quality)
    rng = np.random.default_rng(stable_seed("tri-oer-random-features"))
    for index in range(5):
        output[f"random_feature_{index + 1}"] = rng.standard_normal(len(output))
    for source_id in [
        "acid_oer_same_reaction",
        "orr_adjacent_oxygen_electrocatalysis",
        "ocx_adjacent_electrocatalysis",
    ]:
        output[f"shuffled_{source_id}_rank"] = np.random.default_rng(
            stable_seed(f"tri-shuffle|{source_id}")
        ).permutation(output[f"{source_id}_rank"].to_numpy())
    return output, pd.DataFrame(quality_rows), frames


def group_subset(frame: pd.DataFrame, target_n: int, label: str) -> pd.DataFrame:
    groups = {str(group): local.index.to_numpy(int) for group, local in frame.groupby("group")}
    order = sorted(groups, key=lambda group: hashlib.sha256(f"{label}|{group}".encode()).hexdigest())
    selected: list[int] = []
    deferred: list[str] = []
    for group in order:
        members = list(groups[group])
        if len(selected) + len(members) <= target_n:
            selected.extend(members)
        else:
            deferred.append(group)
    if deferred:
        best = min(deferred, key=lambda group: (abs(len(selected) + len(groups[group]) - target_n), group))
        if abs(len(selected) + len(groups[best]) - target_n) < abs(len(selected) - target_n):
            selected.extend(groups[best])
    return frame.loc[sorted(selected)].reset_index(drop=True)


def full_rank(frame: pd.DataFrame, target_x: np.ndarray, label: str) -> np.ndarray:
    x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    model = ExtraTreesRegressor(
        n_estimators=400,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=stable_seed(label),
        n_jobs=-1,
    )
    model.fit(x, frame["value"].to_numpy(float))
    return pd.Series(model.predict(target_x)).rank(method="average", pct=True).to_numpy()


def matched_controls(
    metadata: pd.DataFrame,
    predictions: pd.DataFrame,
    quality: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    target_x = composition_features(metadata["material_key"].tolist()).astype(np.float32)
    real = [
        "acid_oer_same_reaction",
        "orr_adjacent_oxygen_electrocatalysis",
        "ocx_adjacent_electrocatalysis",
    ]
    wrong = ["borg_wrong_mechanical", "obelix_wrong_ionic"]
    output = metadata[["entity_id", "plate", "composition_cluster"]].copy()
    for source in real:
        for control in wrong:
            matched_n = min(len(frames[source]), len(frames[control]))
            source_subset = group_subset(frames[source], matched_n, f"tri-size|{source}|{control}|source")
            control_subset = group_subset(frames[control], matched_n, f"tri-size|{source}|{control}|control")
            output[f"size_matched_{source}_for_{control}_rank"] = full_rank(
                source_subset, target_x, f"tri-size-rank|{source}|{control}|source"
            )
            output[f"size_matched_{control}_for_{source}_rank"] = full_rank(
                control_subset, target_x, f"tri-size-rank|{source}|{control}|control"
            )
            source_decile = np.minimum(
                9,
                np.floor(
                    predictions[f"{source}_coverage_distance"].rank(method="average", pct=True).to_numpy() * 10
                ).astype(int),
            )
            control_decile = np.minimum(
                9,
                np.floor(
                    predictions[f"{control}_coverage_distance"].rank(method="average", pct=True).to_numpy() * 10
                ).astype(int),
            )
            output[f"coverage_matched_{source}_vs_{control}"] = source_decile == control_decile
    skill = quality.set_index("source")["oof_spearman"].to_dict()
    for source in real:
        closest = min(wrong, key=lambda control: (abs(skill[source] - skill[control]), control))
        output[f"skill_matched_{source}_control"] = closest
        output[f"skill_matched_{source}_wrong_rank"] = predictions[f"{closest}_rank"].to_numpy()
        output[f"skill_gap_{source}"] = abs(float(skill[source]) - float(skill[closest]))
    return output


def family_first(frame: pd.DataFrame, score: pd.Series) -> list[int]:
    order = list(frame.assign(_score=score).sort_values(["_score", "entity_id"], ascending=[False, True]).index)
    seen: set[str] = set()
    first: list[int] = []
    later: list[int] = []
    for index in order:
        cluster = str(frame.at[index, "composition_cluster"])
        (later if cluster in seen else first).append(index)
        seen.add(cluster)
    return first + later


def round_robin(frame: pd.DataFrame, columns: list[str]) -> list[int]:
    queues = [list(frame.sort_values([column, "entity_id"], ascending=[False, True]).index) for column in columns]
    used: set[int] = set()
    clusters: set[str] = set()
    first: list[int] = []
    later: list[int] = []
    while any(queues):
        for queue in queues:
            while queue:
                index = queue.pop(0)
                if index in used:
                    continue
                used.add(index)
                cluster = str(frame.at[index, "composition_cluster"])
                (later if cluster in clusters else first).append(index)
                clusters.add(cluster)
                break
    return first + later


def fixed_policies(metadata: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    merged = metadata.merge(predictions, on=["entity_id", "plate", "composition_cluster"])
    rows: list[dict] = []
    real_columns = [
        "acid_oer_same_reaction_rank",
        "orr_adjacent_oxygen_electrocatalysis_rank",
        "ocx_adjacent_electrocatalysis_rank",
    ]
    for plate, pool in merged.groupby("plate", sort=True):
        pool = pool.copy().reset_index(drop=True)
        consensus = pool[real_columns].mean(axis=1)
        wrong = pool[["borg_wrong_mechanical_rank", "obelix_wrong_ionic_rank"]].mean(axis=1)
        shuffled = pool[[f"shuffled_{column}" for column in real_columns]].mean(axis=1)
        random = pool["entity_id"].map(
            lambda value: int.from_bytes(hashlib.sha256(f"tri-uniform|{value}".encode()).digest()[:8], "big")
        )
        policies = {
            "uniform_family_first": family_first(pool, random),
            "composition_novelty_family_first": family_first(pool, pool["ood_distance_leave_plate_out"]),
            "acid_oer_same_reaction_single": family_first(pool, pool[real_columns[0]]),
            "orr_adjacent_single": family_first(pool, pool[real_columns[1]]),
            "ocx_adjacent_single": family_first(pool, pool[real_columns[2]]),
            "neighbor_entity_consensus": list(pool.assign(_score=consensus).sort_values(["_score", "entity_id"], ascending=[False, True]).index),
            "cca_family_first_consensus": family_first(pool, consensus),
            "cca_family_first_round_robin": round_robin(pool, real_columns),
            "wrong_source_family_first": family_first(pool, wrong),
            "shuffled_neighbor_family_first": family_first(pool, shuffled),
        }
        for policy, order in policies.items():
            for position, index in enumerate(order, start=1):
                rows.append(
                    {
                        "outer_fold": f"holdout-plate-{plate}",
                        "plate": plate,
                        "policy": policy,
                        "position": position,
                        "entity_id": pool.at[index, "entity_id"],
                        "composition_cluster": pool.at[index, "composition_cluster"],
                        "ood_quartile": int(pool.at[index, "ood_quartile"]),
                    }
                )
    return pd.DataFrame(rows)


def hypothesis_cards(metadata: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    pool = metadata.merge(predictions, on=["entity_id", "plate", "composition_cluster"])
    pool["consensus_rank"] = pool[
        [
            "acid_oer_same_reaction_rank",
            "orr_adjacent_oxygen_electrocatalysis_rank",
            "ocx_adjacent_electrocatalysis_rank",
        ]
    ].mean(axis=1)
    specifications = [
        (
            "T1_same_oer_reference",
            "acid_oer_same_reaction_rank",
            "Independent acid-OER measurements nominate active alkaline-OER regions beyond composition novelty despite changed electrolyte and composition system.",
            "Same-reaction evidence tests transferable oxygen-evolution tendencies without transporting a numerical coefficient.",
        ),
        (
            "T2_adjacent_oxygen_electrocatalysis",
            "orr_adjacent_oxygen_electrocatalysis_rank",
            "ORR metal-oxide evidence adds OER regions beyond the same-reaction source.",
            "Shared surface redox and oxygen-intermediate physics can yield a soft neighboring prior while ORR/OER directionality remains separately falsifiable.",
        ),
        (
            "T3_electrocatalysis_consensus",
            "consensus_rank",
            "CCA family-first consensus enriches distinct high-FOM OER clusters and preserves unique adjacent-source proposals.",
            "Credibility, complementarity, and breadth are tested jointly against wrong, shuffled, novelty, and same-source-only controls.",
        ),
    ]
    rows: list[dict] = []
    for card_id, column, hypothesis, rationale in specifications:
        candidate_ids: list[str] = []
        control_ids: list[str] = []
        for plate, local in pool.groupby("plate"):
            number = max(5, int(math.ceil(0.02 * len(local))))
            candidates = local.nlargest(number, column)
            available = local[~local["entity_id"].isin(candidates["entity_id"])].copy()
            for candidate in candidates.itertuples(index=False):
                match_index = (available["ood_distance_leave_plate_out"] - candidate.ood_distance_leave_plate_out).abs().idxmin()
                candidate_ids.append(candidate.entity_id)
                control_ids.append(available.at[match_index, "entity_id"])
                available = available.drop(match_index)
        rows.append(
            {
                "card_id": card_id,
                "written_before_target_fom_decode": True,
                "source_evidence": column,
                "hypothesis": hypothesis,
                "candidate_entity_ids": ";".join(candidate_ids),
                "ood_matched_control_entity_ids": ";".join(control_ids),
                "physical_rationale": rationale,
                "falsifier": "No Holm-adjusted FOM enrichment over OOD-matched controls and no distinct-component increment over same-source, novelty, wrong, and shuffled policies.",
                "planned_measurement": "Compare composition-family membership, stability-conditioned overpotential, and targeted structural characterization for candidates and matched controls.",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    if sha256(PICKLE) != design["target_record"]["sha256"]:
        raise AssertionError("TRI target hash mismatch")
    metadata, schema_audit = target_metadata()
    plate_counts = metadata["plate"].value_counts()
    if len(metadata) < 100 or set(plate_counts.index) != set(PLATE_ELEMENTS) or int(plate_counts.min()) < 20:
        raise AssertionError("TRI target outcome-free minimum gate failed")
    predictions, quality, source_frames = source_predictions(metadata)
    controls = matched_controls(metadata, predictions, quality, source_frames)
    policies = fixed_policies(metadata, predictions)
    cards = hypothesis_cards(metadata, predictions)
    for frame in [metadata, predictions, quality, controls, policies, cards]:
        if {column.lower() for column in frame.columns} & {"fom", "target_value", "outcome"}:
            raise AssertionError("TRI FOM leaked into pre-outcome artifact")
    metadata.to_csv(METADATA, index=False)
    predictions.to_csv(PREDICTIONS, index=False)
    quality.to_csv(QUALITY, index=False)
    controls.to_csv(MATCHED_CONTROLS, index=False)
    policies.to_csv(POLICIES, index=False)
    cards.to_csv(CARDS, index=False)
    artifacts = [
        DESIGN, SCHEMA, REPLACEMENT, PROGRAM, HERE / "tri_oer_implementation.json",
        Path(__file__).resolve(), HERE / "verify_tri_oer_preoutcome.py",
        HERE / "run_tri_oer_neighbor.py", HERE / "verify_tri_oer_neighbor_results.py",
        METADATA, PREDICTIONS, QUALITY, MATCHED_CONTROLS, POLICIES, CARDS,
    ]
    freeze = {
        "status": "preoutcome-frozen",
        "claim_guard": "Only composition buffers were decoded. Target fom buffers remain undecoded; later design changes are outcome-informed.",
        "target_sha256": sha256(PICKLE),
        "orr_source_sha256": sha256(ORR),
        "schema_audit": schema_audit,
        "target_entities": len(metadata),
        "plate_counts": {str(key): int(value) for key, value in plate_counts.sort_index().items()},
        "composition_clusters": int(metadata["composition_cluster"].nunique()),
        "source_quality_rows": len(quality),
        "matched_control_rows": len(controls),
        "policy_rows": len(policies),
        "hypothesis_cards": len(cards),
        "artifact_hashes": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in artifacts
        },
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
