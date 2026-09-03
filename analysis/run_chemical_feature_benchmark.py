#!/usr/bin/env python3
"""Chemical-feature-augmented knowledge transfer.

Compares baseline vs chemical-augmented vs contrastive on:
  - SpecGen (catalyst, with spectra)
  - Alloy family (steels/MPEA/BIRDSHOT, composition-only)

Chemical features (electronegativity, d-electrons, atomic radius, etc.)
are domain-invariant properties from the periodic table. They encode
*why* elements interact, not just *which* elements are present.
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import ExtraTreesRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.kimi_chemical import (
    composition_rich_features,
    RICH_CHEMICAL_FEATURE_NAMES,
)
from catalyst_attention.chemical_features import (
    augment_samples_with_chemistry,
    composition_chemical_features,
    samples_to_chemical_features,
)
from catalyst_attention.data import (
    download_pinned, load_specgen_archive,
    SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
RESULTS_DIR = ROOT / "analysis" / "results"


def composition_matrix(samples):
    m = np.zeros((len(samples), 118), dtype=np.float32)
    for i, s in enumerate(samples):
        if len(s.elements):
            m[i, s.elements - 1] = s.fractions
    return m


def chemical_matrix(samples, rich=False):
    if rich:
        return np.stack([
            composition_rich_features(s.elements, s.fractions) for s in samples
        ])
    return samples_to_chemical_features(samples)


def combined_matrix(samples):
    return np.concatenate([composition_matrix(samples), chemical_matrix(samples)], axis=1)


def trees_baseline(source, target, use_chemical=False, use_rich=False):
    if use_rich:
        X_src = chemical_matrix(source, rich=True)
        X_tgt = chemical_matrix(target, rich=True)
    elif use_chemical:
        X_src = chemical_matrix(source, rich=False)
        X_tgt = chemical_matrix(target, rich=False)
    else:
        X_src = composition_matrix(source)
        X_tgt = composition_matrix(target)
    y_src = targets_array(source)
    y_tgt = targets_array(target)
    model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=0.75,
                                random_state=42, n_jobs=1)
    model.fit(X_src, y_src)
    pred = model.predict(X_tgt)
    return metrics(y_tgt, pred)


def run_transformer(name, source, target, model_config, training_config, device,
                    use_chemical=False):
    """Train and evaluate one Transformer variant."""
    if use_chemical:
        source = augment_samples_with_chemistry(source)
        target = augment_samples_with_chemistry(target)

    model, norm, report = train_source_model(source, model_config, training_config, device=device)
    src_sp = report["source_apparent_metrics"]["spearman"]
    pred_arr = predict(model, target, norm, device=device, unknown_program=True)["mean"]
    m = metrics(targets_array(target), pred_arr)
    return {"source_spearman": src_sp, **m}


def main():
    device = torch.device("cpu")
    set_deterministic(20260802)
    t0 = time.time()

    # Load data.
    sp_path = Path("research/data/specgen.zip")
    if not sp_path.is_file():
        download_pinned(SPECGEN_URL, sp_path, SPECGEN_SHA256, SPECGEN_BYTES)

    specgen = load_specgen_archive(sp_path)
    sp_by = {}
    for s in specgen:
        sp_by.setdefault(s.program, []).append(s)

    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")

    print(f"Data: SpecGen={len(sp_by['specgen_source'])} steels={len(steels)} "
          f"mpea={len(mpea)} birdshot={len(birdshot)}")

    # Verify chemical features work.
    print("\nChemical features for Fe-Co alloy:")
    from catalyst_attention.chemical_features import composition_chemical_features
    import numpy as np
    features = composition_chemical_features(
        np.array([26, 27]), np.array([0.4, 0.6])
    )
    names = ["mean_en", "std_en", "w_en", "mean_rad", "std_rad", "mean_mass",
             "max_d", "w_d", "mean_val", "std_val", "max_ox", "min_ox",
             "mean_grp", "en_range", "d_range", "tm_frac", "tm_w",
             "dom_grp", "entropy"]
    for name, val in zip(names, features):
        print(f"  {name}: {val:.4f}")

    # Experiments.
    catalyst_cfg = CatalystAttentionConfig()
    alloy_cfg = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3,
        use_curve=False, use_conditions=False, use_surface=False, dropout=0.1,
    )
    alloy_chem_cfg = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3,
        use_curve=False, use_conditions=True, use_surface=False, dropout=0.1,
    )
    train_cfg = TrainingConfig(seed=20260802, epochs=80, patience=15, batch_size=32)

    experiments = [
        ("specgen_A", "SpecGen→A", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_A"]),
        ("specgen_D", "SpecGen→D", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_D"]),
        ("steel_mpea", "Steels→MPEA", alloy_cfg, steels, mpea),
        ("steel_bird", "Steels→BIRDSHOT", alloy_cfg, steels, birdshot),
        ("mpea_steel", "MPEA→Steels", alloy_cfg, mpea, steels),
        ("mpea_bird", "MPEA→BIRDSHOT", alloy_cfg, mpea, birdshot),
    ]

    all_results = {}

    for exp_id, exp_name, model_cfg, source, target in experiments:
        print(f"\n{'='*55}")
        print(f"  {exp_name}")
        print(f"{'='*55}")

        result = {"name": exp_name}

        # 1. ExtraTrees (raw composition).
        et = trees_baseline(source, target, use_chemical=False)
        result["extra_trees"] = et
        print(f"  ET (raw):              sp={et['spearman']:.4f}")

        # 2. ExtraTrees + chemical features (19-dim).
        etc = trees_baseline(source, target, use_chemical=True)
        result["extra_trees_chem"] = etc
        print(f"  ET (chemical 19d):     sp={etc['spearman']:.4f} "
              f"(gain={etc['spearman']-et['spearman']:+.4f})")

        # 2b. ExtraTrees + rich chemical features (37-dim).
        etr = trees_baseline(source, target, use_rich=True)
        result["extra_trees_rich"] = etr
        print(f"  ET (rich 37d):         sp={etr['spearman']:.4f} "
              f"(gain={etr['spearman']-et['spearman']:+.4f})")

        # 3. Standard Transformer.
        std = run_transformer("standard", source, target, model_cfg, train_cfg, device)
        result["standard"] = std
        print(f"  Standard:              sp={std['spearman']:.4f}")

        # 4. Chemical-augmented Transformer.
        chem_cfg = alloy_chem_cfg if "steel" in exp_id or "mpea" in exp_id else model_cfg
        chem = run_transformer("chemical", source, target, chem_cfg, train_cfg, device,
                               use_chemical=True)
        result["chemical"] = chem
        print(f"  Chemical-augmented:    sp={chem['spearman']:.4f} "
              f"(gain={chem['spearman']-std['spearman']:+.4f})")

        # 5. Contrastive.
        ct_cfg = TrainingConfig(
            seed=20260802, epochs=80, patience=15, batch_size=32,
            contrastive_weight=0.1,
        )
        ct = run_transformer("contrastive", source, target, model_cfg, ct_cfg, device)
        result["contrastive"] = ct
        print(f"  Contrastive:           sp={ct['spearman']:.4f}")

        all_results[exp_id] = result

    # Summary.
    print(f"\n\n{'='*80}")
    print(f"  CHEMICAL FEATURE BENCHMARK")
    print(f"{'='*80}")
    header = f"  {'Experiment':<20s} {'ET':>8s} {'ET+19d':>8s} {'ET+37d':>8s} {'Std':>8s} {'Chem':>8s} {'Contr':>8s} {'Best':>12s}"
    print(header)
    print("  " + "-" * 80)

    for exp_id, exp_name, _, _, _ in experiments:
        r = all_results[exp_id]
        vals = [r["extra_trees"]["spearman"], r["extra_trees_chem"]["spearman"],
                r["extra_trees_rich"]["spearman"],
                r["standard"]["spearman"], r["chemical"]["spearman"],
                r["contrastive"]["spearman"]]
        best_val = max(vals)
        best_idx = vals.index(best_val)
        best_names = ["ET", "ET+19", "ET+37", "Std", "Chem", "Ctr"]
        print(f"  {exp_name:<20s} {vals[0]:8.4f} {vals[1]:8.4f} {vals[2]:8.4f} "
              f"{vals[3]:8.4f} {vals[4]:8.4f} {vals[5]:8.4f} "
              f"{best_names[best_idx]}:{best_val:.4f}")

    # Count wins per method.
    win_counts = {n: 0 for n in ["ET", "ET+19", "ET+37", "Std", "Chem", "Ctr"]}
    for exp_id, _, _, _, _ in experiments:
        r = all_results[exp_id]
        vals = [r["extra_trees"]["spearman"], r["extra_trees_chem"]["spearman"],
                r["extra_trees_rich"]["spearman"],
                r["standard"]["spearman"], r["chemical"]["spearman"],
                r["contrastive"]["spearman"]]
        best_idx = vals.index(max(vals))
        win_counts[["ET", "ET+19", "ET+37", "Std", "Chem", "Ctr"][best_idx]] += 1

    print(f"\n  Wins per method: {win_counts}")

    # Chemical feature gains.
    chem_gains = []
    for exp_id, _, _, _, _ in experiments:
        r = all_results[exp_id]
        std_sp = r["standard"]["spearman"]
        chem_sp = r["chemical"]["spearman"]
        chem_gains.append(chem_sp - std_sp)
    print(f"  Chemical feature gain vs Standard: median={np.median(chem_gains):+.4f}, "
          f"mean={np.mean(chem_gains):+.4f}")

    out = RESULTS_DIR / "chemical_feature_benchmark.json"
    write_json(out, {
        "experiments": all_results,
        "aggregate": {
            "win_counts": win_counts,
            "chemical_gains": chem_gains,
            "median_chemical_gain": float(np.median(chem_gains)),
        },
        "wall_time_s": round(time.time() - t0, 1),
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
