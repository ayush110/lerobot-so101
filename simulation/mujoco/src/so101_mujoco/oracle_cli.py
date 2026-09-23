"""Evaluate the scripted oracle or record local LeRobot demonstrations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset import record_oracle_dataset
from .environment import MujocoConfig
from .rollout import evaluate_oracle
from .scene import SPLIT_RANGES


def _seeds(split: str, episodes: int) -> list[int]:
    low, high = SPLIT_RANGES[split]
    if episodes <= 0 or low + episodes - 1 > high:
        raise ValueError(f"episodes must be in [1, {high - low + 1}] for {split}")
    return list(range(low, low + episodes))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    evaluate = subparsers.add_parser("evaluate", help="run deterministic oracle evaluation")
    evaluate.add_argument("--split", choices=tuple(SPLIT_RANGES), default="validation")
    evaluate.add_argument("--episodes", type=int, default=5)
    evaluate.add_argument("--max-steps", type=int, default=400)

    record = subparsers.add_parser("record", help="write a local LeRobotDataset")
    record.add_argument("--split", choices=tuple(SPLIT_RANGES), default="train")
    record.add_argument("--episodes", type=int, default=5)
    record.add_argument("--output", type=Path, required=True)
    record.add_argument("--repo-id", default="local/so101-mujoco-oracle")
    return result


def main() -> None:
    args = parser().parse_args()
    try:
        seeds = _seeds(args.split, args.episodes)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if args.command == "evaluate":
        summary = evaluate_oracle(
            seeds,
            MujocoConfig(split=args.split, max_steps=args.max_steps),
        )
    else:
        summary = record_oracle_dataset(
            root=args.output,
            repo_id=args.repo_id,
            seeds=seeds,
            split=args.split,
        )
    print(json.dumps(summary.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
