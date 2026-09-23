"""Oracle rollout and benchmark evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .environment import MujocoConfig, So101AssemblyEnv
from .expert import MujocoAssemblyExpert


@dataclass(frozen=True, slots=True)
class EpisodeRollout:
    seed: int
    observations: tuple[dict[str, Any], ...]
    actions: NDArray[np.float32]
    rewards: NDArray[np.float32]
    terminated: bool
    truncated: bool
    final_info: dict[str, Any]

    @property
    def steps(self) -> int:
        return len(self.actions)


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    episodes: int
    successes: int
    success_rate: float
    retrieve_rate: float
    mate_rate: float
    inspect_rate: float
    mean_steps: float
    seeds: tuple[int, ...]

    def as_dict(self) -> dict[str, float | int | list[int]]:
        return {
            "episodes": self.episodes,
            "successes": self.successes,
            "success_rate": self.success_rate,
            "retrieve_rate": self.retrieve_rate,
            "mate_rate": self.mate_rate,
            "inspect_rate": self.inspect_rate,
            "mean_steps": self.mean_steps,
            "seeds": list(self.seeds),
        }


def run_oracle_episode(env: So101AssemblyEnv, seed: int) -> EpisodeRollout:
    observation, _ = env.reset(seed=seed)
    expert = MujocoAssemblyExpert(env)
    observations: list[dict[str, Any]] = []
    actions: list[NDArray[np.float32]] = []
    rewards: list[float] = []
    terminated = truncated = False
    final_info: dict[str, Any] = {}

    while not (terminated or truncated):
        action = expert.act()
        observations.append(env._copy_observation(observation))
        actions.append(action.copy())
        observation, reward, terminated, truncated, final_info = env.step(action)
        rewards.append(float(reward))

    return EpisodeRollout(
        seed=seed,
        observations=tuple(observations),
        actions=np.asarray(actions, dtype=np.float32),
        rewards=np.asarray(rewards, dtype=np.float32),
        terminated=terminated,
        truncated=truncated,
        final_info=final_info,
    )


def evaluate_oracle(seeds: list[int], config: MujocoConfig | None = None) -> EvaluationSummary:
    if not seeds:
        raise ValueError("at least one evaluation seed is required")
    env = So101AssemblyEnv(config or MujocoConfig(max_steps=400))
    try:
        rollouts = [run_oracle_episode(env, seed) for seed in seeds]
    finally:
        env.close()

    metrics = [rollout.final_info["metrics"] for rollout in rollouts]
    successes = sum(rollout.terminated for rollout in rollouts)
    return EvaluationSummary(
        episodes=len(rollouts),
        successes=successes,
        success_rate=successes / len(rollouts),
        retrieve_rate=mean(metric["retrieve_success"] for metric in metrics),
        mate_rate=mean(metric["mate_success"] for metric in metrics),
        inspect_rate=mean(metric["inspect_success"] for metric in metrics),
        mean_steps=mean(rollout.steps for rollout in rollouts),
        seeds=tuple(seeds),
    )
