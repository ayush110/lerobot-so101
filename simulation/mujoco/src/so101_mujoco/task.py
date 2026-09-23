"""Task state and benchmark metrics independent of policy implementation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum


class Stage(IntEnum):
    RETRIEVE = 0
    MATE = 1
    INSPECT = 2
    COMPLETE = 3


@dataclass(slots=True)
class EpisodeMetrics:
    stage_success: list[bool] = field(default_factory=lambda: [False, False, False])
    collisions: int = 0
    safety_stops: int = 0
    recoveries: int = 0
    interventions: int = 0
    steps: int = 0

    def as_dict(self) -> Mapping[str, float]:
        return {
            "retrieve_success": float(self.stage_success[0]),
            "mate_success": float(self.stage_success[1]),
            "inspect_success": float(self.stage_success[2]),
            "full_success": float(all(self.stage_success)),
            "collisions": float(self.collisions),
            "safety_stops": float(self.safety_stops),
            "recoveries": float(self.recoveries),
            "interventions": float(self.interventions),
            "steps": float(self.steps),
        }
