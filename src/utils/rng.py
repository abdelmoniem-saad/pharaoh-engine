"""
Seeded random number generation utilities for deterministic simulation.

All game randomness flows through these helpers so outcomes are reproducible
when given the same seed — essential for testing, replays, and debugging.
"""
import random
from typing import TypeVar, Sequence

T = TypeVar("T")

# Global game RNG instance — seeded once per new game
_game_rng = random.Random()


def seed(value: int) -> None:
    """Set the global game RNG seed for deterministic simulations."""
    _game_rng.seed(value)


def get_rng() -> random.Random:
    """Return the global game RNG instance."""
    return _game_rng


def randint(a: int, b: int) -> int:
    """Return a random integer N such that a <= N <= b."""
    return _game_rng.randint(a, b)


def uniform(a: float, b: float) -> float:
    """Return a random float N such that a <= N <= b."""
    return _game_rng.uniform(a, b)


def random_float() -> float:
    """Return a random float in [0.0, 1.0)."""
    return _game_rng.random()


def chance(probability: float) -> bool:
    """Return True with the given probability (0.0 to 1.0)."""
    return _game_rng.random() < probability


def choice(seq: Sequence[T]) -> T:
    """Return a random element from a non-empty sequence."""
    return _game_rng.choice(seq)


def choices(seq: Sequence[T], k: int = 1, weights: list[float] | None = None) -> list[T]:
    """Return k random elements from the sequence with optional weights."""
    return _game_rng.choices(seq, weights=weights, k=k)


def shuffle(seq: list) -> None:
    """Shuffle a list in-place."""
    _game_rng.shuffle(seq)


def weighted_average(values: list[float], weights: list[float]) -> float:
    """Calculate the weighted average of values."""
    if not values or not weights or len(values) != len(weights):
        raise ValueError("Values and weights must be non-empty and same length")
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Total weight must be > 0")
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value between minimum and maximum."""
    return max(minimum, min(maximum, value))


def gaussian(mu: float, sigma: float) -> float:
    """Return a random value from a Gaussian distribution."""
    return _game_rng.gauss(mu, sigma)


def gaussian_clamped(mu: float, sigma: float, minimum: float, maximum: float) -> float:
    """Return a Gaussian random value clamped to [minimum, maximum]."""
    return clamp(gaussian(mu, sigma), minimum, maximum)

