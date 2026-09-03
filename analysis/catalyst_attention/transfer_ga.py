"""Genetic algorithm for transfer-learning-aware architecture search.

Unlike standard hyperparameter search, this GA optimizes for TRANSFER
PERFORMANCE, not source-domain performance. Each individual is evaluated
on its ability to transfer to a held-out domain, not on its source fit.

Key insight: The best source model is not the best transfer model.
We need to search for architectures that learn TRANSFERABLE features.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
import torch

from .data import CatalystSample
from .model import CatalystAttentionConfig
from .training import (
    TrainingConfig,
    metrics,
    predict,
    targets_array,
    train_source_model,
)


# ---- GA Configuration for Transfer Learning ----

@dataclass
class TransferIndividual:
    """One candidate configuration evaluated on transfer performance."""
    genes: dict[str, Any] = field(default_factory=dict)
    source_fitness: float | None = None
    transfer_fitness: float | None = None  # Key: evaluated on target domain
    combined_fitness: float | None = None  # Weighted combination

    def to_model_config(self) -> CatalystAttentionConfig:
        g = self.genes
        d_model = int(g["d_model"])
        n_heads = int(g["n_heads"])
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
            composition_mode=str(g["composition_mode"]),
            fusion_mode=str(g["fusion_mode"]),
            depth_routing=str(g["depth_routing"]),
        )

    def to_training_config(self) -> TrainingConfig:
        g = self.genes
        return TrainingConfig(
            learning_rate=10.0 ** float(g["learning_rate"]),
            weight_decay=10.0 ** float(g["weight_decay"]),
            rank_weight=float(g["rank_weight"]),
            nll_weight=float(g["nll_weight"]),
            contrastive_weight=float(g.get("contrastive_weight", 0.0)),
            domain_adversarial_weight=float(g.get("adversarial_weight", 0.0)),
            grl_lambda=float(g.get("grl_lambda", 1.0)),
        )


# Gene space for transfer learning.
TRANSFER_GENES = {
    # Architecture.
    "d_model": [32, 48, 64, 96],
    "n_heads": [2, 4, 8],
    "composition_layers": [1, 2, 3, 4],
    "curve_layers": [1, 2, 3],
    "condition_layers": [1, 2],
    "fusion_layers": [1, 2],
    "feedforward_multiplier": [2, 3, 4],
    "dropout": [0.0, 0.1, 0.2, 0.3],

    # Training.
    "learning_rate": [-4.0, -3.5, -3.0, -2.5, -2.0],  # log10 scale
    "weight_decay": [-5.0, -4.0, -3.0, -2.0],
    "rank_weight": [0.0, 0.1, 0.2, 0.3, 0.4],
    "nll_weight": [0.0, 0.1, 0.2, 0.3],

    # Transfer-specific.
    "contrastive_weight": [0.0, 0.05, 0.1, 0.2, 0.3],
    "adversarial_weight": [0.0, 0.05, 0.1, 0.2],
    "grl_lambda": [0.5, 1.0, 2.0],

    # Architecture choices.
    "composition_mode": ["set_query", "crabnet"],
    "fusion_mode": ["cross_attention", "perceiver"],
    "depth_routing": ["standard", "delta_mhar_sublayer"],

    # Feature augmentation.
    "use_chemical_features": [True, False],
    "use_kinetic_features": [True, False],
}


def random_transfer_individual() -> TransferIndividual:
    """Create a random individual from the gene space."""
    genes = {}
    for name, values in TRANSFER_GENES.items():
        if isinstance(values[0], bool):
            genes[name] = random.choice(values)
        elif isinstance(values[0], int):
            genes[name] = random.choice(values)
        elif isinstance(values[0], float):
            genes[name] = random.uniform(min(values), max(values))
        else:
            genes[name] = random.choice(values)
    return TransferIndividual(genes=genes)


def transfer_crossover(parent_a: TransferIndividual, parent_b: TransferIndividual) -> TransferIndividual:
    """Uniform crossover."""
    child_genes = {}
    for key in parent_a.genes:
        child_genes[key] = parent_a.genes[key] if random.random() < 0.5 else parent_b.genes[key]
    return TransferIndividual(genes=child_genes)


def transfer_mutate(individual: TransferIndividual, rate: float = 0.15) -> TransferIndividual:
    """Mutate genes with given probability."""
    genes = dict(individual.genes)
    for name, values in TRANSFER_GENES.items():
        if random.random() < rate:
            if isinstance(values[0], bool):
                genes[name] = not genes[name]
            elif isinstance(values[0], int):
                genes[name] = random.choice(values)
            elif isinstance(values[0], float):
                genes[name] = random.uniform(min(values), max(values))
            else:
                genes[name] = random.choice(values)
    return TransferIndividual(genes=genes)


class TransferGASearch:
    """Genetic algorithm that optimizes for transfer performance.

    Key difference from standard GA: fitness is computed on the TARGET
    domain, not the source domain. This finds architectures that learn
    transferable features, not just good source fit.

    Parameters
    ----------
    source_samples: Source domain samples.
    target_samples: Target domain samples (for evaluation only, no training).
    device: Torch device.
    population_size: Number of individuals per generation.
    generations: Number of generations.
    transfer_weight: Weight for transfer fitness vs source fitness.
        1.0 = only transfer matters, 0.0 = only source matters.
        0.7 = mostly transfer with some source regularization.
    """

    def __init__(
        self,
        source_samples: Sequence[CatalystSample],
        target_samples: Sequence[CatalystSample],
        *,
        device: torch.device,
        population_size: int = 12,
        generations: int = 6,
        transfer_weight: float = 0.7,
        mutation_rate: float = 0.15,
        elitism: int = 2,
        epochs: int = 40,
    ) -> None:
        self.source = list(source_samples)
        self.target = list(target_samples)
        self.device = device
        self.population_size = population_size
        self.generations = generations
        self.transfer_weight = transfer_weight
        self.mutation_rate = mutation_rate
        self.elitism = elitism
        self.epochs = epochs
        self.history: list[dict] = []

    def evaluate(self, individual: TransferIndividual, seed: int) -> TransferIndividual:
        """Train and evaluate on both source and target."""
        from .chemical_features import augment_samples_with_chemistry
        from .kinetic_tokens import augment_with_kinetic_tokens

        try:
            model_config = individual.to_model_config()
            training_config = individual.to_training_config()
        except (ValueError, KeyError):
            individual.combined_fitness = -float("inf")
            return individual

        # Apply augmentations.
        source = self.source
        target = self.target
        if individual.genes.get("use_chemical_features", False):
            source = augment_samples_with_chemistry(list(source))
            target = augment_samples_with_chemistry(list(target))
        if individual.genes.get("use_kinetic_features", False):
            source = augment_with_kinetic_tokens(list(source))
            target = augment_with_kinetic_tokens(list(target))

        # Adjust epochs.
        training_config = TrainingConfig(
            **{**training_config.__dict__, "epochs": self.epochs, "seed": seed}
        )

        try:
            model, normalizer, report = train_source_model(
                source, model_config, training_config, device=self.device,
            )
        except Exception:
            individual.combined_fitness = -float("inf")
            return individual

        # Source fitness.
        individual.source_fitness = float(
            report["source_apparent_metrics"]["spearman"]
        )

        # Transfer fitness (zero-shot).
        transfer_pred = predict(
            model, target, normalizer, device=self.device, unknown_program=True,
        )["mean"]
        transfer_metrics = metrics(targets_array(target), transfer_pred)
        individual.transfer_fitness = float(transfer_metrics["spearman"])

        # Combined fitness: weighted sum.
        # Transfer fitness is the primary objective.
        # Source fitness prevents catastrophic forgetting.
        individual.combined_fitness = (
            self.transfer_weight * individual.transfer_fitness
            + (1 - self.transfer_weight) * individual.source_fitness
        )

        return individual

    def run(self, seed: int = 20260802) -> TransferIndividual:
        """Run GA and return the best individual found."""
        population = [random_transfer_individual() for _ in range(self.population_size)]
        best_overall = None
        best_fitness = -float("inf")

        for gen in range(self.generations):
            print(f"  Generation {gen + 1}/{self.generations}")

            # Evaluate all individuals.
            for ind in population:
                if ind.combined_fitness is None:
                    ind = self.evaluate(ind, seed + gen * 100)
                if ind.combined_fitness > best_fitness:
                    best_fitness = ind.combined_fitness
                    best_overall = copy.deepcopy(ind)
                    print(f"    New best: transfer={ind.transfer_fitness:.4f} "
                          f"source={ind.source_fitness:.4f} "
                          f"chem={ind.genes.get('use_chemical_features', False)} "
                          f"kin={ind.genes.get('use_kinetic_features', False)} "
                          f"ct={ind.genes.get('contrastive_weight', 0):.2f}")

            # Sort by combined fitness.
            population.sort(key=lambda x: x.combined_fitness or -float("inf"), reverse=True)

            # Record history.
            gen_stats = {
                "generation": gen + 1,
                "best_transfer": population[0].transfer_fitness,
                "best_source": population[0].source_fitness,
                "best_combined": population[0].combined_fitness,
                "median_transfer": float(np.median([
                    ind.transfer_fitness or -float("inf") for ind in population
                ])),
                "median_combined": float(np.median([
                    ind.combined_fitness or -float("inf") for ind in population
                ])),
                "best_genes": population[0].genes,
            }
            self.history.append(gen_stats)
            print(f"    Best: transfer={gen_stats['best_transfer']:.4f} "
                  f"combined={gen_stats['best_combined']:.4f}")

            if gen == self.generations - 1:
                break

            # Selection + reproduction.
            new_population = population[:self.elitism]
            while len(new_population) < self.population_size:
                # Tournament selection.
                tournament = random.sample(population[:self.population_size // 2], k=3)
                parent_a = max(tournament, key=lambda x: x.combined_fitness or -float("inf"))
                tournament = random.sample(population[:self.population_size // 2], k=3)
                parent_b = max(tournament, key=lambda x: x.combined_fitness or -float("inf"))

                child = transfer_crossover(parent_a, parent_b)
                child = transfer_mutate(child, rate=self.mutation_rate)
                child.combined_fitness = None  # Reset for evaluation.
                new_population.append(child)

            population = new_population[:self.population_size]

        assert best_overall is not None
        return best_overall


def run_transfer_ga(
    source_samples: Sequence[CatalystSample],
    target_samples: Sequence[CatalystSample],
    *,
    device: torch.device,
    population_size: int = 12,
    generations: int = 6,
    epochs: int = 40,
    seed: int = 20260802,
) -> dict:
    """Run transfer-aware GA search and return results."""
    from .training import set_deterministic
    set_deterministic(seed)

    searcher = TransferGASearch(
        source_samples,
        target_samples,
        device=device,
        population_size=population_size,
        generations=generations,
        epochs=epochs,
    )
    best = searcher.run(seed=seed)

    return {
        "best_transfer_fitness": best.transfer_fitness,
        "best_source_fitness": best.source_fitness,
        "best_combined_fitness": best.combined_fitness,
        "best_genes": best.genes,
        "best_model_config": best.to_model_config().__dict__,
        "best_training_config": best.to_training_config().__dict__,
        "ga_history": searcher.history,
    }
