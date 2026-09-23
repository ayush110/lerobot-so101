"""LeRobotDataset writer for scripted MuJoCo demonstrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .environment import MujocoConfig, So101AssemblyEnv
from .rollout import EvaluationSummary, evaluate_oracle, run_oracle_episode

TASK_INSTRUCTION = (
    "Retrieve the blue keyed part, mate it with the orange part, "
    "and place the assembly in the inspection fixture."
)

LEROBOT_FEATURES = {
    "observation.state": {"dtype": "float32", "shape": (19,), "names": None},
    "observation.joints": {"dtype": "float32", "shape": (5,), "names": None},
    "observation.gripper": {"dtype": "float32", "shape": (1,), "names": ["gripper"]},
    "observation.stage": {"dtype": "float32", "shape": (1,), "names": ["stage"]},
    "simulation.seed": {"dtype": "int64", "shape": (1,), "names": ["seed"]},
    "action": {"dtype": "float32", "shape": (6,), "names": None},
    "next.reward": {"dtype": "float32", "shape": (1,), "names": None},
    "next.success": {"dtype": "bool", "shape": (1,), "names": None},
    "next.done": {"dtype": "bool", "shape": (1,), "names": None},
}


def _lerobot_dataset_type() -> Any:
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as error:
        raise RuntimeError(
            "LeRobot dataset support is optional. Install it with "
            "`uv sync --all-packages --group robotics --extra lerobot`."
        ) from error
    return LeRobotDataset


def record_oracle_dataset(
    root: str | Path,
    repo_id: str,
    seeds: list[int],
    *,
    fps: int = 20,
    split: str = "train",
) -> EvaluationSummary:
    """Record successful or failed oracle rollouts as a local LeRobot dataset."""
    if not seeds:
        raise ValueError("at least one recording seed is required")
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"dataset root must be empty or absent: {root}")
    dataset_type = _lerobot_dataset_type()
    dataset = dataset_type.create(
        repo_id=repo_id,
        fps=fps,
        root=root,
        robot_type="so101_mujoco",
        features=LEROBOT_FEATURES,
        use_videos=False,
    )
    config = MujocoConfig(split=split, max_steps=400)
    env = So101AssemblyEnv(config)
    try:
        for seed in seeds:
            rollout = run_oracle_episode(env, seed)
            for index, (observation, action, reward) in enumerate(
                zip(rollout.observations, rollout.actions, rollout.rewards, strict=True)
            ):
                is_last = index == rollout.steps - 1
                frame = {
                    "observation.state": observation["state"].astype(np.float32),
                    "observation.joints": observation["joints"].astype(np.float32),
                    "observation.gripper": np.atleast_1d(observation["gripper"]).astype(np.float32),
                    "observation.stage": np.atleast_1d(observation["stage"]).astype(np.float32),
                    "simulation.seed": np.atleast_1d(np.int64(seed)),
                    "action": action.astype(np.float32),
                    "next.reward": np.atleast_1d(np.float32(reward)),
                    "next.success": np.atleast_1d(np.bool_(is_last and rollout.terminated)),
                    "next.done": np.atleast_1d(np.bool_(is_last)),
                    "task": TASK_INSTRUCTION,
                }
                dataset.add_frame(frame)
            dataset.save_episode()
    finally:
        env.close()
        dataset.finalize()

    return evaluate_oracle(seeds, config)
