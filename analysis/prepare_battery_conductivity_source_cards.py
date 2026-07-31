"""Build publication-out-of-fold source-property cards for battery targets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import r2_score
from sklearn.neighbors import NearestNeighbors


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "battery_conductivity_borrowing_design.json"
IMPLEMENTATION_PATH = HERE / "battery_conductivity_implementation.json"
RELEASE_MANIFEST_PATH = (
    HERE / "results" / "battery_conductivity_formal_release_manifest.json"
)
RELEASE_PATH = (
    HERE / "results" / "battery_conductivity_formal_release.csv"
)
AGGREGATION_AMENDMENT_PATH = (
    HERE / "BATTERY_CONDUCTIVITY_SOURCE_AGGREGATION_AMENDMENT.md"
)
DEFAULT_CARDS = (
    HERE / "results" / "battery_conductivity_source_cards.csv"
)
DEFAULT_SUMMARY = (
    HERE / "results" / "battery_conductivity_source_summary.json"
)

SOURCE_PROPERTIES = ["conductivity", "voltage", "energy"]
SOURCE_SEEDS = {
    "conductivity": 2026072711,
    "shuffled_conductivity": 2026072712,
    "voltage": 2026072713,
    "energy": 2026072714,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)


def doi_fold(values: pd.Series, folds: int) -> np.ndarray:
    return np.array(
        [stable_int(str(value)) % folds for value in values],
        dtype=np.int16,
    )


def target_transform(values: np.ndarray, property_name: str) -> np.ndarray:
    if property_name in {"conductivity", "shuffled_conductivity"}:
        return np.log10(values)
    if property_name == "energy":
        return np.log1p(values)
    return values.astype(float, copy=False)


def target_inverse(values: np.ndarray, property_name: str) -> np.ndarray:
    if property_name in {"conductivity", "shuffled_conductivity"}:
        return np.power(10.0, values)
    if property_name == "energy":
        return np.expm1(values)
    return values


def vectorizer_from_config(config: dict[str, Any]) -> HashingVectorizer:
    representation = config["representation"]
    return HashingVectorizer(
        analyzer=representation["analyzer"],
        ngram_range=tuple(representation["ngram_range"]),
        n_features=representation["n_features"],
        alternate_sign=representation["alternate_sign"],
        norm=representation["norm"],
        lowercase=True,
        dtype=np.float32,
    )


def aggregate_source(
    release: pd.DataFrame, property_name: str
) -> pd.DataFrame:
    source = release.loc[
        release["property_class"].eq(property_name),
        ["doi_normalized", "material_normalized", "normalized_value"],
    ].copy()
    return (
        source.groupby(
            ["doi_normalized", "material_normalized"],
            as_index=False,
            sort=True,
        )["normalized_value"]
        .median()
        .reset_index(drop=True)
    )


def aggregate_target(release: pd.DataFrame) -> pd.DataFrame:
    target = release.loc[
        release["property_class"].eq("capacity")
    ].copy()
    target["cycle_group"] = target["cycle_number"].fillna(-1.0)
    group_columns = [
        "doi_normalized",
        "material_normalized",
        "current_a_per_g",
        "cycle_group",
        "Type",
        "Specifier",
        "Tag",
        "Info",
    ]
    target = (
        target.groupby(group_columns, as_index=False, sort=True)
        .agg(
            capacity_mAh_g=("normalized_value", "median"),
            is_early_cycle=("is_early_cycle", "max"),
            warning=(
                "Warning",
                lambda values: "|".join(
                    sorted({str(value) for value in values})
                ),
            ),
            date=("Date", "first"),
        )
        .reset_index(drop=True)
    )
    target["cycle_number"] = target["cycle_group"].replace(-1.0, np.nan)
    id_columns = [
        "doi_normalized",
        "material_normalized",
        "current_a_per_g",
        "cycle_group",
        "Type",
        "Specifier",
        "Tag",
        "Info",
    ]
    target.insert(
        0,
        "target_id",
        [
            hashlib.sha256(
                "\x1f".join(str(row[column]) for column in id_columns).encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
            for _, row in target.iterrows()
        ],
    )
    return target.drop(columns=["cycle_group"])


def shuffled_labels(source: pd.DataFrame, seed: int) -> np.ndarray:
    counts = source.groupby("doi_normalized")["doi_normalized"].transform(
        "size"
    )
    quartiles = pd.qcut(
        counts.rank(method="first"),
        q=4,
        labels=False,
        duplicates="drop",
    ).to_numpy()
    labels = source["normalized_value"].to_numpy(float).copy()
    rng = np.random.default_rng(seed)
    for quartile in np.unique(quartiles):
        rows = np.flatnonzero(quartiles == quartile)
        labels[rows] = labels[rng.permutation(rows)]
    return labels


def tree_dispersion(
    model: ExtraTreesRegressor, features: Any
) -> np.ndarray:
    predictions = np.vstack(
        [tree.predict(features) for tree in model.estimators_]
    )
    return predictions.std(axis=0, ddof=1)


def build_card(
    source: pd.DataFrame,
    target: pd.DataFrame,
    property_name: str,
    vectorizer: HashingVectorizer,
    config: dict[str, Any],
    shuffled: bool = False,
    workers: int = 1,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_cards = config["source_cards"]
    folds = int(source_cards["folds"])
    source_fold = doi_fold(source["doi_normalized"], folds)
    target_fold = doi_fold(target["doi_normalized"], folds)
    source_features = vectorizer.transform(source["material_normalized"])
    target_features = vectorizer.transform(target["material_normalized"])

    raw_labels = source["normalized_value"].to_numpy(float)
    if shuffled:
        raw_labels = shuffled_labels(
            source, seed=2026072707
        )
        card_name = "shuffled_conductivity"
    else:
        card_name = property_name
    labels = target_transform(raw_labels, card_name)

    source_oof = np.full(len(source), np.nan, dtype=float)
    target_prediction = np.full(len(target), np.nan, dtype=float)
    target_dispersion = np.full(len(target), np.nan, dtype=float)
    target_support = np.full(len(target), np.nan, dtype=float)

    for fold in range(folds):
        source_train = source_fold != fold
        source_test = source_fold == fold
        target_test = target_fold == fold
        if not source_train.any() or not source_test.any():
            raise RuntimeError(f"Empty source fold for {card_name}: {fold}")
        model = ExtraTreesRegressor(
            n_estimators=source_cards["n_estimators"],
            min_samples_leaf=source_cards["min_samples_leaf"],
            max_features=source_cards["max_features"],
            random_state=SOURCE_SEEDS[card_name] + fold,
            n_jobs=workers,
        )
        model.fit(source_features[source_train], labels[source_train])
        source_oof[source_test] = model.predict(
            source_features[source_test]
        )
        if target_test.any():
            target_rows = np.flatnonzero(target_test)
            target_materials = target.loc[
                target_test, "material_normalized"
            ].to_numpy()
            unique_target_materials, target_inverse = np.unique(
                target_materials, return_inverse=True
            )
            unique_target_features = vectorizer.transform(
                unique_target_materials
            )
            unique_predictions = model.predict(unique_target_features)
            unique_dispersion = tree_dispersion(
                model, unique_target_features
            )
            target_prediction[target_rows] = unique_predictions[
                target_inverse
            ]
            target_dispersion[target_rows] = unique_dispersion[
                target_inverse
            ]
            unique_source_materials = np.unique(
                source.loc[
                    source_train, "material_normalized"
                ].to_numpy()
            )
            unique_source_features = vectorizer.transform(
                unique_source_materials
            )
            neighbors = NearestNeighbors(
                n_neighbors=1,
                metric="cosine",
                algorithm="brute",
                n_jobs=workers,
            )
            neighbors.fit(unique_source_features)
            distances, _ = neighbors.kneighbors(
                unique_target_features, return_distance=True
            )
            unique_support = np.clip(1.0 - distances[:, 0], 0.0, 1.0)
            target_support[target_rows] = unique_support[target_inverse]

    if not np.isfinite(source_oof).all():
        raise RuntimeError(f"Incomplete source OOF predictions: {card_name}")
    if not np.isfinite(target_prediction).all():
        raise RuntimeError(f"Incomplete target card: {card_name}")

    r2 = float(r2_score(labels, source_oof))
    spearman = float(stats.spearmanr(labels, source_oof).statistic)
    card = pd.DataFrame(
        {
            f"{card_name}_prediction": target_prediction,
            f"{card_name}_dispersion": target_dispersion,
            f"{card_name}_support": target_support,
            f"{card_name}_missing": np.zeros(len(target), dtype=np.int8),
        }
    )
    summary = {
        "property": card_name,
        "source_records": int(len(source)),
        "source_materials": int(source["material_normalized"].nunique()),
        "source_publications": int(source["doi_normalized"].nunique()),
        "oof_r2_transformed": r2,
        "oof_spearman_transformed": spearman,
        "target_support_quantiles": {
            str(q): float(np.quantile(target_support, q))
            for q in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
        },
        "transformed_target": (
            "log10"
            if card_name in {"conductivity", "shuffled_conductivity"}
            else "log1p"
            if card_name == "energy"
            else "identity"
        ),
    }
    return card, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, default=RELEASE_PATH)
    parser.add_argument("--cards-output", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--n-estimators", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--properties",
        nargs="+",
        choices=SOURCE_PROPERTIES,
        default=SOURCE_PROPERTIES,
    )
    parser.add_argument("--skip-shuffled", action="store_true")
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    config = json.loads(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
    release_manifest = json.loads(
        RELEASE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if release_manifest["release_sha256"] != sha256(args.release):
        raise RuntimeError("Formal release hash changed")
    if release_manifest["design_sha256"] != sha256(DESIGN_PATH):
        raise RuntimeError("Design hash changed")
    if release_manifest["implementation_sha256"] != sha256(
        IMPLEMENTATION_PATH
    ):
        raise RuntimeError("Implementation hash changed")
    if args.n_estimators is not None:
        if args.n_estimators <= 0:
            raise ValueError("--n-estimators must be positive")
        config["source_cards"]["n_estimators"] = args.n_estimators

    release = pd.read_csv(
        args.release, low_memory=False, keep_default_na=False
    )
    target = aggregate_target(release)
    vectorizer = vectorizer_from_config(config)

    cards = [target]
    summaries = []
    conductivity_source = aggregate_source(release, "conductivity")
    for property_name in args.properties:
        source = aggregate_source(release, property_name)
        card, summary = build_card(
            source,
            target,
            property_name,
            vectorizer,
            config,
            shuffled=False,
            workers=args.workers,
        )
        cards.append(card)
        summaries.append(summary)
        if property_name == "conductivity" and not args.skip_shuffled:
            shuffled_card, shuffled_summary = build_card(
                conductivity_source,
                target,
                property_name,
                vectorizer,
                config,
                shuffled=True,
                workers=args.workers,
            )
            cards.append(shuffled_card)
            summaries.append(shuffled_summary)

    combined = pd.concat(cards, axis=1)
    args.cards_output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.cards_output, index=False)

    real_summary = next(
        item for item in summaries if item["property"] == "conductivity"
    )
    gate = config["source_cards"]["conductivity_skill_gate"]
    skill_pass = (
        real_summary["oof_r2_transformed"]
        > gate["minimum_source_oof_r2"]
        and real_summary["oof_spearman_transformed"]
        > gate["minimum_source_oof_spearman"]
    )
    summary = {
        "status": (
            "source-card-gate-passed"
            if skill_pass
            else "source-card-gate-failed"
        ),
        "design_sha256": sha256(DESIGN_PATH),
        "implementation_sha256": sha256(IMPLEMENTATION_PATH),
        "release_sha256": sha256(args.release),
        "aggregation_amendment_sha256": sha256(
            AGGREGATION_AMENDMENT_PATH
        ),
        "formal_n_estimators": config["source_cards"]["n_estimators"],
        "cards_sha256": sha256(args.cards_output),
        "target_records": int(len(target)),
        "target_materials": int(target["material_normalized"].nunique()),
        "target_publications": int(target["doi_normalized"].nunique()),
        "source_summaries": summaries,
        "conductivity_skill_gate": {
            **gate,
            "passed": skill_pass,
        },
        "claim_guard": config["claim_guard"],
    }
    args.summary_output.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
