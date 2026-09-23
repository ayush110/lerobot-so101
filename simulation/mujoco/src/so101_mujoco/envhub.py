"""Gymnasium/LeRobot environment-factory compatibility boundary."""

from __future__ import annotations

from dataclasses import fields
from functools import partial
from typing import Any

import gymnasium as gym

from .environment import MujocoConfig, So101AssemblyEnv


def _config_from(cfg: MujocoConfig | dict[str, Any] | None) -> MujocoConfig:
    if cfg is None:
        return MujocoConfig()
    if isinstance(cfg, MujocoConfig):
        return cfg
    if isinstance(cfg, dict):
        allowed = {field.name for field in fields(MujocoConfig)}
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"unknown MuJoCo configuration keys: {sorted(unknown)}")
        return MujocoConfig(**cfg)
    raise TypeError("cfg must be MujocoConfig, dict, or None")


def _make_single(config: MujocoConfig) -> So101AssemblyEnv:
    return So101AssemblyEnv(config)


def make_env(
    n_envs: int = 1,
    use_async_envs: bool = False,
    cfg: MujocoConfig | dict[str, Any] | None = None,
) -> gym.vector.VectorEnv:
    """Return vectorized environments using the LeRobot EnvHub-style contract."""
    if n_envs <= 0:
        raise ValueError("n_envs must be positive")
    config = _config_from(cfg)
    constructors = [partial(_make_single, config) for _ in range(n_envs)]
    vector_type = (
        gym.vector.AsyncVectorEnv if use_async_envs and n_envs > 1 else gym.vector.SyncVectorEnv
    )
    return vector_type(constructors)
