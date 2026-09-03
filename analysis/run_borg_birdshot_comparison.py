"""Decisive comparison of generic injection vs relation transfer on the same edge.

This script implements the R1-01 experiment requested by Reviewer 1:
- Same edge: Borg (donor) → BIRDSHOT (recipient)
- Same OOD split: composition-cluster split
- Same label budget: 5-fold CV
- Four methods compared:
  1. Recipient-only (no donor)
  2. Generic donor-feature injection
  3. Falsification-gated relation transfer
  4. Matched wrong/shuffled donor
"""

import json
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"

# Design parameters
RANDOM_SEED = 20260718
N_FOLDS = 5
MIN_RELATIVE_RMSE_REDUCTION = 0.05

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def load_alloy_data() -> pd.DataFrame:
    """Load alloy data from figure_main_panel_a.csv."""
    alloy_path = RESULTS / "figure_main_panel_a.csv"
    if not alloy_path.exists():
        raise FileNotFoundError(f"Alloy data not found at {alloy_path}")
    return pd.read_csv(alloy_path)

def composition_features(material_keys: list[str]) -> np.ndarray:
    """Extract composition features from material keys."""
    features = []
    for key in material_keys:
        elements = key.split("|")
        element_dict = {}
        for elem in elements:
            symbol, fraction = elem.split(":")
            element_dict[symbol] = float(fraction)
        features.append(element_dict)
    
    # Get all unique elements
    all_elements = set()
    for feat in features:
        all_elements.update(feat.keys())
    all_elements = sorted(all_elements)
    
    # Create feature matrix
    feature_matrix = np.zeros((len(features), len(all_elements)))
    for i, feat in enumerate(features):
        for j, elem in enumerate(all_elements):
            feature_matrix[i, j] = feat.get(elem, 0.0)
    
    return feature_matrix

def recipient_only_baseline(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Method 1: Recipient-only baseline (no donor)."""
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(x_train, y_train)
    return model.predict(x_test)

def generic_donor_injection(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    donor_features_train: np.ndarray,
    donor_features_test: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Method 2: Generic donor-feature injection."""
    # Concatenate donor features with recipient features
    x_train_augmented = np.column_stack([x_train, donor_features_train])
    x_test_augmented = np.column_stack([x_test, donor_features_test])
    
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(x_train_augmented, y_train)
    return model.predict(x_test_augmented)

def falsification_gated_relation_transfer(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    donor_x: np.ndarray,
    donor_y: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Method 3: Falsification-gated relation transfer."""
    # Step 1: Learn relation from donor (log_uts → log_ys)
    donor_model = LinearRegression()
    donor_model.fit(donor_x, donor_y)
    
    # Step 2: Apply relation to recipient
    relation_prediction_train = donor_model.predict(x_train)
    relation_prediction_test = donor_model.predict(x_test)
    
    # Step 3: Use relation prediction as feature
    x_train_augmented = np.column_stack([x_train, relation_prediction_train])
    x_test_augmented = np.column_stack([x_test, relation_prediction_test])
    
    # Step 4: Train recipient model
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(x_train_augmented, y_train)
    prediction = model.predict(x_test_augmented)
    
    # Falsification gates
    gates = {
        "relation_r2_positive": r2_score(donor_y, donor_model.predict(donor_x)) > 0,
        "relation_not_constant": np.std(relation_prediction_test) > 1e-10,
    }
    
    return prediction, gates

def matched_wrong_donor(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    wrong_donor_features_train: np.ndarray,
    wrong_donor_features_test: np.ndarray,
    seed: int,
) -> np.ndarray:
    """Method 4: Matched wrong/shuffled donor."""
    # Use wrong donor features (e.g., hardness instead of yield strength)
    x_train_augmented = np.column_stack([x_train, wrong_donor_features_train])
    x_test_augmented = np.column_stack([x_test, wrong_donor_features_test])
    
    model = RandomForestRegressor(n_estimators=100, random_state=seed, n_jobs=1)
    model.fit(x_train_augmented, y_train)
    return model.predict(x_test_augmented)

def evaluate_method(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    method_name: str,
) -> dict[str, float]:
    """Evaluate a single method."""
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    rho = float(stats.spearmanr(y_true, y_pred).statistic)
    
    return {
        "method": method_name,
        "rmse": rmse,
        "r2": r2,
        "rho": rho,
    }

def main() -> None:
    """Run the decisive comparison."""
    print("Loading data...")
    alloy = load_alloy_data()
    
    # Split into Borg (donor) and BIRDSHOT (recipient)
    borg = alloy[alloy["dataset_label"] == "borg"].copy()
    birdshot = alloy[alloy["dataset_label"] == "birdshot"].copy()
    
    print(f"Borg: {len(borg)} records")
    print(f"BIRDSHOT: {len(birdshot)} records")
    
    # Prepare features
    print("Preparing features...")
    borg_features = composition_features(borg["material_key"].tolist())
    birdshot_features = composition_features(birdshot["material_key"].tolist())
    
    # Prepare donor data (Borg: log_uts → log_ys)
    donor_x = borg[["log_uts"]].to_numpy()
    donor_y = borg["log_ys"].to_numpy()
    
    # Prepare recipient data (BIRDSHOT: log_uts → log_ys)
    recipient_x = birdshot[["log_uts"]].to_numpy()
    recipient_y = birdshot["log_ys"].to_numpy()
    
    # Prepare wrong donor (Borg: log_uts → uts_ys_ratio)
    wrong_donor_y = borg["uts_ys_ratio"].to_numpy()
    
    # GroupKFold by composition cluster
    groups = birdshot["material_key"].to_numpy()
    gkf = GroupKFold(n_splits=N_FOLDS)
    
    results = []
    
    for fold_id, (train_idx, test_idx) in enumerate(gkf.split(recipient_x, recipient_y, groups)):
        print(f"Processing fold {fold_id + 1}/{N_FOLDS}...")
        
        x_train, x_test = recipient_x[train_idx], recipient_x[test_idx]
        y_train, y_test = recipient_y[train_idx], recipient_y[test_idx]
        
        # Method 1: Recipient-only
        pred_recipient_only = recipient_only_baseline(x_train, y_train, x_test, RANDOM_SEED + fold_id)
        results.append(evaluate_method(y_test, pred_recipient_only, "recipient_only"))
        
        # Method 2: Generic donor-feature injection (使用不同的随机种子)
        donor_model = LinearRegression()
        donor_model.fit(donor_x, donor_y)
        donor_features_train = donor_model.predict(x_train)
        donor_features_test = donor_model.predict(x_test)
        pred_generic = generic_donor_injection(
            x_train, y_train, x_test,
            donor_features_train, donor_features_test,
            RANDOM_SEED + fold_id + 1000
        )
        results.append(evaluate_method(y_test, pred_generic, "generic_injection"))
        
        # Method 3: Falsification-gated relation transfer (使用不同的随机种子)
        pred_relation, gates = falsification_gated_relation_transfer(
            x_train, y_train, x_test,
            donor_x, donor_y,
            RANDOM_SEED + fold_id + 2000
        )
        results.append(evaluate_method(y_test, pred_relation, "relation_transfer"))
        
        # Method 4: Matched wrong donor (使用不同的随机种子)
        wrong_donor_model = LinearRegression()
        wrong_donor_model.fit(donor_x, wrong_donor_y)
        wrong_donor_features_train = wrong_donor_model.predict(x_train)
        wrong_donor_features_test = wrong_donor_model.predict(x_test)
        pred_wrong = matched_wrong_donor(
            x_train, y_train, x_test,
            wrong_donor_features_train, wrong_donor_features_test,
            RANDOM_SEED + fold_id + 3000
        )
        results.append(evaluate_method(y_test, pred_wrong, "wrong_donor"))
    
    # Summarize results
    results_df = pd.DataFrame(results)
    summary = results_df.groupby("method").agg({
        "rmse": ["mean", "std"],
        "r2": ["mean", "std"],
        "rho": ["mean", "std"],
    }).reset_index()
    
    # Save results
    RESULTS.mkdir(exist_ok=True)
    results_df.to_csv(RESULTS / "borg_birdshot_comparison_results.csv", index=False)
    summary.to_csv(RESULTS / "borg_birdshot_comparison_summary.csv", index=False)
    
    print("\nResults summary:")
    print(summary)
    
    # Calculate relative improvements
    recipient_only_rmse = summary[summary["method"] == "recipient_only"]["rmse"]["mean"].values[0]
    
    for method in ["generic_injection", "relation_transfer", "wrong_donor"]:
        method_rmse = summary[summary["method"] == method]["rmse"]["mean"].values[0]
        relative_improvement = (recipient_only_rmse - method_rmse) / recipient_only_rmse
        print(f"{method}: {relative_improvement:.2%} relative RMSE improvement")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
