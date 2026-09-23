"""SO-101 MuJoCo digital twin and benchmark environment.

Environment symbols are imported lazily so metadata and deterministic scene
utilities remain inspectable before optional MuJoCo dependencies are installed.
"""

from typing import Any

from .scene import SPLIT_RANGES, Scene, sample_scene, seed_for
from .task import EpisodeMetrics, Stage

__all__ = [
    "EpisodeMetrics",
    "JOINT_NAMES",
    "MujocoConfig",
    "MujocoAssemblyExpert",
    "SPLIT_RANGES",
    "Scene",
    "So101AssemblyEnv",
    "Stage",
    "build_model",
    "evaluate_oracle",
    "make_env",
    "sample_scene",
    "seed_for",
]

__version__ = "0.1.0"


def __getattr__(name: str) -> Any:
    if name in {"JOINT_NAMES", "MujocoConfig", "So101AssemblyEnv", "build_model"}:
        from . import environment

        return getattr(environment, name)
    if name == "MujocoAssemblyExpert":
        from .expert import MujocoAssemblyExpert

        return MujocoAssemblyExpert
    if name == "evaluate_oracle":
        from .rollout import evaluate_oracle

        return evaluate_oracle
    if name == "make_env":
        from .envhub import make_env

        return make_env
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
