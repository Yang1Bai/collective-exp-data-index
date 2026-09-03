"""Genetic algorithm for catalyst model architecture and hyperparameter search.

Searches over model architecture and training hyperparameters to find
configurations that maximize source validation Spearman. The GA avoids
target labels entirely — fitness comes from source validation only.
"""
from __future__ import annotations

import copy
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from .data import CatalystSample
from .model import CatalystAttentionConfig
from .training import (
    FeatureNormalizer,
    TrainingConfig,
    set_deterministic,
    targets_array,
    train_source_model,
    write_json,
)


# ---- Gene space definition ----

INT_GENES = {
    "d_model": [32, 48, 64, 96, 128],
    "n_heads": [2, 4, 8],
    "composition_layers": [1, 2, 3],
    "curve_layers": [1, 2, 3, 4],
    "condition_layers": [1, 2],
    "fusion_layers": [1, 2],
    "feedforward_multiplier": [2, 3, 4],
    "patch_size": [4, 8, 16],
    "perceiver_latents": [6, 8, 12, 16],
    "perceiver_layers": [1, 2, 3],
}

FLOAT_GENES = {
    "dropout": (0.0, 0.3),
    "modality_dropout": (0.0, 0.3),
    "learning_rate": (-4.0, -2.3),     # log10 scale: 1e-4 to 5e-3
    "weight_decay": (-5.0, -2.0),      # log10 scale: 1e-5 to 1e-2
    "rank_weight": (0.0, 0.5),
    "nll_weight": (0.0, 0.4),
    "support_weight": (0.0, 0.1),
}

CATEGORICAL_GENES = {
    "composition_mode": ["set_query", "crabnet"],
    "fusion_mode": ["cross_attention", "perceiver"],
    "depth_routing": ["standard", "delta_mhar_sublayer"],
}


@dataclass
class Individual:
    """One candidate configuration with optional fitness."""
    genes: dict[str, Any] = field(default_factory=dict)
    fitness: float | None = None
    model_report: dict | None = None

    def to_model_config(self) -> CatalystAttentionConfig:
        g = self.genes
        d_model = int(g["d_model"])
        n_heads = int(g["n_heads"])
        # Ensure divisibility.
        while d_model % n_heads:
            n_heads = max(2, n_heads - 1)
        return CatalystAttentionConfig(
            d_model=d_model,
            n_heads=n_heads,
            composition_layers=int(g["composition_layers"]),
            curve_layers=int(g["curve_layers"]),
            condition_layers=int(g["condition_layers"]),
            fusion_layers=int(g["fusion_layers"]),
            feedforward_multiplier=int(g["feedforward_multiplier"]),
            dropout=float(g["dropout"]),
            modality_dropout=float(g.get("modality_dropout", 0.0)),
            composition_mode=str(g["composition_mode"]),
            fusion_mode=str(g["fusion_mode"]),
            depth_routing=str(g["depth_routing"]),
            patch_size=int(g.get("patch_size", 8)),
            perceiver_latents=int(g.get("perceiver_latents", 12)),
            perceiver_layers=int(g.get("perceiver_layers", 2)),
        )

    def to_training_config(self) -> TrainingConfig:
        g = self.genes
        return TrainingConfig(
            learning_rate=10.0 ** float(g["learning_rate"]),
            weight_decay=10.0 ** float(g["weight_decay"]),
            rank_weight=float(g["rank_weight"]),
            nll_weight=float(g["nll_weight"]),
            support_weight=float(g.get("support_weight", 0.02)),
        )


def _random_gene(gene_name: str) -> Any:
    if gene_name in INT_GENES:
        return random.choice(INT_GENES[gene_name])
    if gene_name in FLOAT_GENES:
        lo, hi = FLOAT_GENES[gene_name]
        return random.uniform(lo, hi)
    if gene_name in CATEGORICAL_GENES:
        return random.choice(CATEGORICAL_GENES[gene_name])
    raise KeyError(f"unknown gene: {gene_name}")


def random_individual() -> Individual:
    genes = {}
    all_genes = list(INT_GENES) + list(FLOAT_GENES) + list(CATEGORICAL_GENES)
    for name in all_genes:
        genes[name] = _random_gene(name)
    return Individual(genes=genes)


def _mutate_value(name: str, current: Any) -> Any:
    if name in INT_GENES:
        options = INT_GENES[name]
        idx = options.index(int(current)) if int(current) in options else 0
        delta = random.choice([-1, 1])
        return options[(idx + delta) % len(options)]
    if name in FLOAT_GENES:
        lo, hi = FLOAT_GENES[name]
        noise = random.gauss(0, 0.1 * (hi - lo))
        return max(lo, min(hi, float(current) + noise))
    if name in CATEGORICAL_GENES:
        options = CATEGORICAL_GENES[name]
        return random.choice([o for o in options if o != str(current)])
    return current


def crossover(parent_a: Individual, parent_b: Individual) -> Individual:
    child_genes = {}
    for key in parent_a.genes:
        if random.random() < 0.5:
            child_genes[key] = parent_a.genes[key]
        else:
            child_genes[key] = parent_b.genes[key]
    return Individual(genes=child_genes)


def mutate(individual: Individual, rate: float = 0.2) -> Individual:
    genes = dict(individual.genes)
    for key in genes:
        if random.random() < rate:
            genes[key] = _mutate_value(key, genes[key])
    return Individual(genes=genes)


class CatalystGASearch:
    """Genetic algorithm for catalyst model configuration search.

    Parameters
    ----------
    source_samples:
        Training samples (source programme only).
    device:
        Torch device.
    population_size:
        Number of individuals per generation.
    generations:
        Number of generations to evolve.
    mutation_rate:
        Probability of mutating each gene.
    elitism:
        Number of top individuals carried forward unchanged.
    epochs:
        Training epochs per evaluation (use lower values for speed).
    checkpoint_dir:
        Optional directory to save best configurations.
    """

    def __init__(
        self,
        source_samples: Sequence[CatalystSample],
        *,
        device: torch.device,
        population_size: int = 16,
        generations: int = 8,
        mutation_rate: float = 0.2,
        elitism: int = 2,
        epochs: int = 60,
        checkpoint_dir: Path | None = None,
    ) -> None:
        if len(source_samples) < 20:
            raise ValueError("GA requires at least 20 source samples")
        self.source_samples = list(source_samples)
        self.device = device
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elitism = elitism
        self.epochs = epochs
        self.checkpoint_dir = checkpoint_dir
        self.history: list[dict] = []

    def _evaluate(self, individual: Individual, seed: int) -> float:
        """Train a model with this config and return validation Spearman."""
        try:
            model_config = individual.to_model_config()
            training_config = individual.to_training_config()
        except (ValueError, KeyError) as e:
            return -float("inf")

        eval_config = TrainingConfig(
            seed=seed,
            epochs=self.epochs,
            patience=max(10, self.epochs // 6),
            batch_size=32,
            learning_rate=training_config.learning_rate,
            weight_decay=training_config.weight_decay,
            rank_weight=training_config.rank_weight,
            nll_weight=training_config.nll_weight,
            support_weight=training_config.support_weight,
        )

        try:
            model, normalizer, report = train_source_model(
                self.source_samples,
                model_config,
                eval_config,
                device=self.device,
            )
        except Exception:
            return -float("inf")

        individual.model_report = report
        return float(
            report.get("source_apparent_metrics", {}).get("spearman", 0.0)
        )

    def run(self, seed: int = 20260802) -> Individual:
        """Evolve and return the best configuration found."""
        # Initialize population.
        population = [random_individual() for _ in range(self.population_size)]

        best_overall: Individual | None = None
        best_fitness = -float("inf")

        for gen in range(self.generations):
            print(f"  Generation {gen + 1}/{self.generations}")

            # Evaluate all individuals.
            for ind in population:
                if ind.fitness is None:
                    ind.fitness = self._evaluate(ind, seed + gen * 100)
                if ind.fitness > best_fitness:
                    best_fitness = ind.fitness
                    best_overall = ind
                    print(f"    New best: Spearman={ind.fitness:.4f} "
                          f"d_model={ind.genes['d_model']} "
                          f"n_heads={ind.genes['n_heads']} "
                          f"depth_routing={ind.genes['depth_routing']}")

            # Sort by fitness (descending).
            population.sort(key=lambda ind: ind.fitness or -float("inf"), reverse=True)

            gen_stats = {
                "generation": gen + 1,
                "best_fitness": float(population[0].fitness or -float("inf")),
                "median_fitness": float(
                    np.median([ind.fitness or -float("inf") for ind in population])
                ),
                "best_genes": population[0].genes,
                "population_fitness": [
                    ind.fitness or -float("inf") for ind in population
                ],
            }
            self.history.append(gen_stats)
            print(f"    Best: {gen_stats['best_fitness']:.4f}, "
                  f"Median: {gen_stats['median_fitness']:.4f}")

            if gen == self.generations - 1:
                break

            # Selection + reproduction.
            new_population = population[:self.elitism]  # Elitism.
            while len(new_population) < self.population_size:
                # Tournament selection.
                tournament = random.sample(population[:self.population_size // 2], k=3)
                parent_a = max(tournament, key=lambda ind: ind.fitness or -float("inf"))
                tournament = random.sample(population[:self.population_size // 2], k=3)
                parent_b = max(tournament, key=lambda ind: ind.fitness or -float("inf"))

                child = crossover(parent_a, parent_b)
                child = mutate(child, rate=self.mutation_rate)
                child.fitness = None
                new_population.append(child)

            population = new_population[:self.population_size]

        assert best_overall is not None
        if self.checkpoint_dir:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            write_json(
                self.checkpoint_dir / "ga_history.json",
                {"history": self.history, "best_genes": best_overall.genes},
            )

        return best_overall


def run_ga_search(
    source_samples: Sequence[CatalystSample],
    *,
    device: torch.device,
    population_size: int = 16,
    generations: int = 8,
    epochs: int = 60,
    seed: int = 20260802,
    output_dir: Path | None = None,
) -> dict:
    """Run GA search and return results dictionary."""
    set_deterministic(seed)
    searcher = CatalystGASearch(
        source_samples,
        device=device,
        population_size=population_size,
        generations=generations,
        epochs=epochs,
        checkpoint_dir=output_dir,
    )
    best = searcher.run(seed=seed)

    return {
        "best_fitness": best.fitness,
        "best_genes": best.genes,
        "best_model_config": best.to_model_config().__dict__,
        "best_training_config": best.to_training_config().__dict__,
        "ga_history": searcher.history,
        "ga_params": {
            "population_size": population_size,
            "generations": generations,
            "epochs_per_evaluation": epochs,
        },
    }
