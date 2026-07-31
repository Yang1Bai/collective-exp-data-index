"""Freeze acid-OER target metadata, neighbor ranks, policies, and cards without target outcomes."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

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

from analysis.common import ELEMENTS, composition_features  # noqa: E402
from analysis.run_caltech_ionic_external_policy import source_entities  # noqa: E402

DESIGN = HERE / "caltech_acid_oer_neighbor_design.json"
ACCESS_AMENDMENT = HERE / "CALTECH_ACID_OER_ACCIDENTAL_ACCESS_AMENDMENT.md"
PROGRAM = HERE / "outcome_unseen_neighbor_validation_program.json"
ZIP = ROOT / "data" / "external" / "caltech_acid_oer" / "AcidOER-MnSbSnTiCo.zip"
TARGET = ROOT / "data" / "external" / "caltech_acid_oer" / "extracted" / "data" / "OER" / "oer_all_foms.csv"
ORR = ROOT / "data" / "external" / "caltech_acid_oer" / "sources" / "ORR_catalyst_metrics_MnNiMgCaFeLaYIn.csv"
RESULTS = HERE / "results"
METADATA = RESULTS / "caltech_acid_oer_target_metadata.csv"
PREDICTIONS = RESULTS / "caltech_acid_oer_source_predictions.csv"
QUALITY = RESULTS / "caltech_acid_oer_source_quality.csv"
POLICIES = RESULTS / "caltech_acid_oer_policy_orders.csv"
CARDS = RESULTS / "caltech_acid_oer_hypothesis_cards.csv"
FREEZE = RESULTS / "caltech_acid_oer_PREOUTCOME.json"

TARGET_ELEMENTS = ["Mn", "Sb", "Sn", "Ti", "Co"]
ORR_ELEMENTS = ["Mn", "Ni", "Mg", "Ca", "Fe", "La", "Y", "In"]
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


def material_key(elements: list[str], fractions: np.ndarray) -> str | None:
    fractions = np.asarray(fractions, dtype=float)
    if not np.isfinite(fractions).all() or np.any(fractions < 0) or fractions.sum() <= 0:
        return None
    fractions = fractions / fractions.sum()
    return "|".join(
        f"{element}:{fraction:.10g}"
        for element, fraction in sorted(zip(elements, fractions))
        if fraction > 1e-12
    )


def verify_inputs() -> None:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    expected = design["target_snapshot"]
    if sha256(ZIP) != expected["sha256"]:
        raise AssertionError("Acid-OER archive hash mismatch")
    if sha256(ORR) != "f9f74e75d1c6dafe359593b16c81e71cbb605546194da6d8016f5020c2b9c26e":
        raise AssertionError("ORR neighbor-source hash mismatch")


def target_metadata() -> pd.DataFrame:
    # Target outcomes J_t20/J_t200/Jmax_* are deliberately not requested.
    columns = ["plate", "elements"] + TARGET_ELEMENTS
    raw = pd.read_csv(TARGET, usecols=columns)
    raw["original_row"] = raw.index.astype(int)
    raw["plate"] = pd.to_numeric(raw["plate"], errors="coerce").astype("Int64")
    for element in TARGET_ELEMENTS:
        raw[element] = pd.to_numeric(raw[element], errors="coerce")
    exposed = (
        raw["plate"].eq(5411)
        & np.isclose(raw["Mn"], 0.58)
        & np.isclose(raw["Sb"], 0.09)
        & np.isclose(raw["Sn"], 0.26)
        & np.isclose(raw["Ti"], 0.07)
        & np.isclose(raw["Co"], 0.0)
    )
    raw["permanent_exclusion"] = np.where(
        raw["plate"].eq(5029), "accidental-access:plate-5029", np.where(exposed, "accidental-access:exposed-5411-row", "")
    )
    raw = raw[raw["permanent_exclusion"].eq("")].copy()
    keys = [material_key(TARGET_ELEMENTS, row) for row in raw[TARGET_ELEMENTS].to_numpy(float)]
    raw["material_key"] = keys
    raw = raw[raw["material_key"].notna()].copy().reset_index(drop=True)
    raw["entity_id"] = [
        "acid-oer-" + hashlib.sha256(f"{plate}|{row}|{key}".encode()).hexdigest()[:20]
        for plate, row, key in zip(raw["plate"], raw["original_row"], raw["material_key"])
    ]
    x = composition_features(raw["material_key"].tolist()).astype(np.float32)
    scaler = StandardScaler().fit(x)
    x_scaled = scaler.transform(x)
    clusters = min(80, max(40, len(raw) // 20), len(raw))
    labels = MiniBatchKMeans(
        n_clusters=clusters, random_state=SEED, n_init=10, batch_size=512
    ).fit_predict(x_scaled)
    raw["composition_cluster"] = [f"acid-cluster-{label:03d}" for label in labels]
    raw["ood_distance_leave_plate_out"] = np.nan
    raw["ood_quartile"] = 0
    for plate in sorted(raw["plate"].unique()):
        evaluation = raw["plate"].eq(plate).to_numpy()
        development = ~evaluation
        distance = NearestNeighbors(n_neighbors=1).fit(x_scaled[development]).kneighbors(
            x_scaled[evaluation], return_distance=True
        )[0][:, 0]
        raw.loc[evaluation, "ood_distance_leave_plate_out"] = distance
        if evaluation.sum() >= 4:
            raw.loc[evaluation, "ood_quartile"] = pd.qcut(
                pd.Series(distance), 4, labels=[1, 2, 3, 4], duplicates="drop"
            ).astype(int).to_numpy()
    raw["outer_fold"] = raw["plate"].map(lambda plate: f"holdout-plate-{int(plate)}")
    return raw


def load_orr_source(target_keys: set[str]) -> pd.DataFrame:
    raw = pd.read_csv(ORR)
    for element in ORR_ELEMENTS:
        raw[element] = pd.to_numeric(raw[element], errors="coerce")
    raw["value"] = pd.to_numeric(raw["J.uAcm2_0.63_secondCA"], errors="coerce")
    raw["material_key"] = [material_key(ORR_ELEMENTS, row) for row in raw[ORR_ELEMENTS].to_numpy(float)]
    raw = raw[raw["material_key"].notna() & np.isfinite(raw["value"])].copy()
    raw = raw[~raw["material_key"].isin(target_keys)].copy().reset_index(drop=True)
    x = composition_features(raw["material_key"].tolist()).astype(np.float32)
    clusters = min(50, max(10, len(raw) // 30), len(raw))
    labels = MiniBatchKMeans(n_clusters=clusters, random_state=SEED, n_init=10).fit_predict(x)
    raw["group"] = [f"orr-cluster-{label:03d}" for label in labels]
    return (
        raw.groupby("material_key", as_index=False)
        .agg(value=("value", "median"), group=("group", "first"), n_raw=("value", "size"))
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def fit_source(source_id: str, frame: pd.DataFrame, target_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    x = composition_features(frame["material_key"].tolist()).astype(np.float32)
    y = frame["value"].to_numpy(float)
    groups = frame["group"].astype(str).to_numpy()
    folds = min(5, len(np.unique(groups)))
    splitter = GroupKFold(n_splits=folds, shuffle=True, random_state=stable_seed(source_id))
    oof = np.full(len(frame), np.nan)
    for fold, (train, test) in enumerate(splitter.split(x, y, groups)):
        model = ExtraTreesRegressor(
            n_estimators=200, min_samples_leaf=2, max_features=0.7,
            random_state=stable_seed(f"{source_id}|fold|{fold}"), n_jobs=-1,
        )
        model.fit(x[train], y[train])
        oof[test] = model.predict(x[test])
    model = ExtraTreesRegressor(
        n_estimators=400, min_samples_leaf=2, max_features=0.7,
        random_state=stable_seed(f"{source_id}|full"), n_jobs=-1,
    )
    model.fit(x, y)
    prediction = model.predict(target_x)
    coverage = NearestNeighbors(n_neighbors=1).fit(x).kneighbors(target_x, return_distance=True)[0][:, 0]
    return prediction, coverage, {
        "source": source_id,
        "entities": len(frame),
        "groups": len(np.unique(groups)),
        "oof_r2": float(r2_score(y, oof)),
        "oof_rmse": float(math.sqrt(mean_squared_error(y, oof))),
        "oof_spearman": float(stats.spearmanr(y, oof).statistic),
    }


def sources(metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_keys = set(metadata["material_key"])
    target_x = composition_features(metadata["material_key"].tolist()).astype(np.float32)
    frames = {
        "orr_adjacent_oxygen_electrocatalysis": load_orr_source(target_keys),
        "ocx_adjacent_electrocatalysis": source_entities(
            SOURCE_MAP["ocx_adjacent_electrocatalysis"], target_keys, set()
        ),
        "borg_wrong_mechanical": source_entities(SOURCE_MAP["borg_wrong_mechanical"], target_keys, set()),
        "obelix_wrong_ionic": source_entities(SOURCE_MAP["obelix_wrong_ionic"], target_keys, set()),
    }
    output = metadata[["entity_id", "plate", "composition_cluster"]].copy()
    quality: list[dict] = []
    for source_id, frame in frames.items():
        prediction, coverage, row = fit_source(source_id, frame, target_x)
        output[f"{source_id}_prediction"] = prediction
        output[f"{source_id}_rank"] = pd.Series(prediction).rank(method="average", pct=True).to_numpy()
        output[f"{source_id}_coverage_distance"] = coverage
        quality.append(row)
    rng = np.random.default_rng(stable_seed("acid-oer-random-features"))
    for index in range(4):
        output[f"random_feature_{index + 1}"] = rng.standard_normal(len(output))
    for source_id in ["orr_adjacent_oxygen_electrocatalysis", "ocx_adjacent_electrocatalysis"]:
        output[f"shuffled_{source_id}_rank"] = np.random.default_rng(
            stable_seed(f"acid-oer-shuffle|{source_id}")
        ).permutation(output[f"{source_id}_rank"].to_numpy())
    return output, pd.DataFrame(quality)


def family_first(frame: pd.DataFrame, score: pd.Series) -> list[int]:
    ordered = list(frame.assign(_score=score).sort_values(["_score", "entity_id"], ascending=[False, True]).index)
    seen: set[str] = set()
    first: list[int] = []
    later: list[int] = []
    for index in ordered:
        group = str(frame.at[index, "composition_cluster"])
        if group in seen:
            later.append(index)
        else:
            seen.add(group)
            first.append(index)
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


def policy_orders(metadata: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    merged = metadata.merge(predictions, on=["entity_id", "plate", "composition_cluster"])
    rows: list[dict] = []
    for plate, pool in merged.groupby("plate", sort=True):
        pool = pool.copy().reset_index(drop=True)
        orr = pool["orr_adjacent_oxygen_electrocatalysis_rank"]
        ocx = pool["ocx_adjacent_electrocatalysis_rank"]
        neighbor = (orr + ocx) / 2
        wrong = (pool["borg_wrong_mechanical_rank"] + pool["obelix_wrong_ionic_rank"]) / 2
        shuffled = (
            pool["shuffled_orr_adjacent_oxygen_electrocatalysis_rank"]
            + pool["shuffled_ocx_adjacent_electrocatalysis_rank"]
        ) / 2
        random = pool["entity_id"].map(
            lambda value: int.from_bytes(hashlib.sha256(f"acid-random|{value}".encode()).digest()[:8], "big")
        )
        policies = {
            "uniform_family_first": family_first(pool, random),
            "composition_novelty_family_first": family_first(pool, pool["ood_distance_leave_plate_out"]),
            "orr_adjacent_single": family_first(pool, orr),
            "ocx_adjacent_single": family_first(pool, ocx),
            "neighbor_entity_consensus": list(pool.assign(_score=neighbor).sort_values(["_score", "entity_id"], ascending=[False, True]).index),
            "cca_family_first_consensus": family_first(pool, neighbor),
            "cca_family_first_round_robin": round_robin(
                pool, ["orr_adjacent_oxygen_electrocatalysis_rank", "ocx_adjacent_electrocatalysis_rank"]
            ),
            "wrong_source_family_first": family_first(pool, wrong),
            "shuffled_neighbor_family_first": family_first(pool, shuffled),
        }
        for policy, order in policies.items():
            for position, index in enumerate(order, start=1):
                rows.append(
                    {
                        "outer_fold": f"holdout-plate-{int(plate)}",
                        "plate": int(plate),
                        "policy": policy,
                        "position": position,
                        "entity_id": pool.at[index, "entity_id"],
                        "composition_cluster": pool.at[index, "composition_cluster"],
                        "ood_quartile": int(pool.at[index, "ood_quartile"]),
                    }
                )
    return pd.DataFrame(rows)


def cards(metadata: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    pool = metadata.merge(predictions, on=["entity_id", "plate", "composition_cluster"])
    pool["neighbor_consensus_rank"] = (
        pool["orr_adjacent_oxygen_electrocatalysis_rank"]
        + pool["ocx_adjacent_electrocatalysis_rank"]
    ) / 2
    specifications = [
        (
            "A1_orr_oxygen_electrocatalysis",
            "orr_adjacent_oxygen_electrocatalysis_rank",
            "ORR oxide activity enriches acid-OER composition clusters beyond novelty.",
            "Shared oxide surface redox, stability, and oxygen-intermediate energetics can nominate regions without assuming identical ORR and OER coefficients.",
        ),
        (
            "A2_ocx_electrocatalysis",
            "ocx_adjacent_electrocatalysis_rank",
            "Independent OCx electrocatalysis ranks contribute acid-OER regions not supplied by ORR.",
            "A second synthesis and electrocatalysis platform tests cross-platform complementarity rather than same-repository memorization.",
        ),
        (
            "A3_electrocatalysis_consensus",
            "neighbor_consensus_rank",
            "CCA family-first consensus enriches distinct active acid-OER clusters while suppressing repeated local compositions.",
            "Agreement supplies credibility and separate ranks retain complementary proposals; family-first allocation tests breadth.",
        ),
    ]
    rows: list[dict] = []
    for card_id, column, hypothesis, rationale in specifications:
        candidate_ids: list[str] = []
        control_ids: list[str] = []
        for plate, local in pool.groupby("plate"):
            number = max(3, int(math.ceil(0.05 * len(local))))
            candidates = local.nlargest(number, column)
            available = local[~local["entity_id"].isin(candidates["entity_id"])].copy()
            for candidate in candidates.itertuples(index=False):
                if available.empty:
                    break
                match_index = (available["ood_distance_leave_plate_out"] - candidate.ood_distance_leave_plate_out).abs().idxmin()
                candidate_ids.append(candidate.entity_id)
                control_ids.append(available.at[match_index, "entity_id"])
                available = available.drop(match_index)
        rows.append(
            {
                "card_id": card_id,
                "written_before_remaining_target_outcome": True,
                "source_evidence": column,
                "hypothesis": hypothesis,
                "candidate_entity_ids": ";".join(candidate_ids),
                "ood_matched_control_entity_ids": ";".join(control_ids),
                "physical_rationale": rationale,
                "falsifier": "No Holm-adjusted enrichment over matched controls, novelty, wrong sources, and frozen shuffles, or no unique source-contributed cluster by budget 20.",
                "planned_measurement": "Compare phase assignment, stable-current trajectory, and post-test structural context for every candidate and matched control.",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    verify_inputs()
    RESULTS.mkdir(parents=True, exist_ok=True)
    metadata = target_metadata()
    if len(metadata) < 100 or metadata["plate"].nunique() != 4 or metadata["composition_cluster"].nunique() < 40:
        raise AssertionError("Acid-OER outcome-free minimum gate failed")
    predictions, quality = sources(metadata)
    policies = policy_orders(metadata, predictions)
    hypothesis_cards = cards(metadata, predictions)
    for frame in [metadata, predictions, quality, policies, hypothesis_cards]:
        forbidden = {column.lower() for column in frame.columns} & {
            "j_t20", "j_t200", "jmax_post", "jmax_pre", "target_value", "outcome"
        }
        if forbidden:
            raise AssertionError(f"Target outcome leaked into pre-outcome file: {sorted(forbidden)}")
    metadata.to_csv(METADATA, index=False)
    predictions.to_csv(PREDICTIONS, index=False)
    quality.to_csv(QUALITY, index=False)
    policies.to_csv(POLICIES, index=False)
    hypothesis_cards.to_csv(CARDS, index=False)
    artifacts = [
        DESIGN, ACCESS_AMENDMENT, PROGRAM, Path(__file__).resolve(), METADATA,
        PREDICTIONS, QUALITY, POLICIES, CARDS,
    ]
    freeze = {
        "status": "preoutcome-frozen-with-recorded-exclusions",
        "claim_guard": "Remaining target outcomes were not loaded. The two accidental-access exclusions are immutable.",
        "target_zip_sha256": sha256(ZIP),
        "orr_source_sha256": sha256(ORR),
        "target_entities": len(metadata),
        "plates": sorted(int(value) for value in metadata["plate"].unique()),
        "plate_counts": {str(key): int(value) for key, value in metadata["plate"].value_counts().sort_index().items()},
        "composition_clusters": int(metadata["composition_cluster"].nunique()),
        "source_quality_rows": len(quality),
        "policy_rows": len(policies),
        "hypothesis_cards": len(hypothesis_cards),
        "permanent_exclusions": {
            "plate_5029": "all rows",
            "plate_5411_exposed_composition": "Mn0.58 Sb0.09 Sn0.26 Ti0.07 Co0",
        },
        "artifact_hashes": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in artifacts
        },
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
