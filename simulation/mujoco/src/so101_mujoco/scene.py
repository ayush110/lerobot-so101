"""Deterministic train, validation, and hidden scene distributions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

SPLIT_RANGES = {
    "train": (1000, 1999),
    "validation": (2000, 2199),
    "hidden": (9000, 9199),
}


@dataclass(frozen=True, slots=True)
class Scene:
    seed: int
    part_a: NDArray[np.float64]
    part_b: NDArray[np.float64]
    fixture: NDArray[np.float64]
    friction: float
    motor_delay_steps: int
    backlash_rad: float
    observation_delay_steps: int


def seed_for(split: str, episode_index: int) -> int:
    if split not in SPLIT_RANGES:
        raise ValueError(f"unknown split {split!r}")
    low, high = SPLIT_RANGES[split]
    seed = low + episode_index
    if seed > high:
        raise ValueError(f"episode {episode_index} exceeds {split} split capacity")
    return seed


def sample_scene(seed: int) -> Scene:
    rng = np.random.default_rng(seed)

    def pose(center: tuple[float, float, float]) -> NDArray[np.float64]:
        xyz = np.asarray(center, dtype=np.float64) + rng.uniform(
            [-0.04, -0.06, 0.0], [0.04, 0.06, 0.0]
        )
        return np.concatenate([xyz, [rng.uniform(-1.8, 1.8)]])

    return Scene(
        seed=seed,
        part_a=pose((0.24, -0.07, 0.02)),
        part_b=pose((0.24, 0.07, 0.02)),
        fixture=np.array([0.34, 0.0, 0.018, 0.0], dtype=np.float64),
        friction=float(rng.uniform(0.5, 1.2)),
        motor_delay_steps=int(rng.integers(0, 4)),
        backlash_rad=float(rng.uniform(0.0, 0.02)),
        observation_delay_steps=int(rng.integers(0, 3)),
    )
