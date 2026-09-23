"""Headless smoke-test entry point for local machines and CI."""

from __future__ import annotations

import argparse
import json

import numpy as np

from .environment import MujocoConfig, So101AssemblyEnv


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--steps", type=int, default=20)
    result.add_argument("--seed", type=int, default=2000)
    result.add_argument("--split", choices=("train", "validation", "hidden"), default="validation")
    return result


def main() -> None:
    args = parser().parse_args()
    if args.steps <= 0:
        raise SystemExit("--steps must be positive")
    env = So101AssemblyEnv(MujocoConfig(split=args.split, max_steps=max(args.steps, 1)))
    try:
        observation, reset_info = env.reset(seed=args.seed)
        final_info: dict[str, object] = {}
        for _ in range(args.steps):
            observation, _, terminated, truncated, final_info = env.step(
                np.zeros(6, dtype=np.float32)
            )
            if terminated or truncated:
                break
        print(
            json.dumps(
                {
                    "backend": reset_info["backend"],
                    "seed": reset_info["seed"],
                    "steps": final_info.get("metrics", {}).get("steps", 0.0),
                    "stage": final_info.get("stage", "unknown"),
                    "state_shape": list(observation["state"].shape),
                    "action_shape": list(env.action_space.shape),
                    "finite": bool(np.isfinite(observation["state"]).all()),
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        env.close()


if __name__ == "__main__":
    main()
