"""In-process representations of the public robot contract.

Network and log serialization is defined in packages/proto. These dataclasses
remain dependency-light so simulators, dataset tools, and tests can import them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import math

SCHEMA_VERSION = 1


def _require_finite(values: tuple[float, ...], name: str) -> None:
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"{name} must be non-empty and finite")


@dataclass(frozen=True, slots=True)
class Observation:
    """A timestamped robot observation independent of simulator or hardware."""

    timestamp_ns: int
    sequence: int
    joint_positions_rad: tuple[float, ...]
    gripper_position: float
    calibration_version: str
    frame_ids: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.timestamp_ns < 0 or self.sequence < 0:
            raise ValueError("timestamp and sequence must be non-negative")
        _require_finite(self.joint_positions_rad, "joint_positions_rad")
        if not math.isfinite(self.gripper_position):
            raise ValueError("gripper_position must be finite")
        if not self.calibration_version:
            raise ValueError("calibration_version is required")


@dataclass(frozen=True, slots=True)
class ActionChunk:
    """A policy proposal; the safety runtime must validate it before execution."""

    created_at_ns: int
    valid_until_ns: int
    joint_targets_rad: tuple[tuple[float, ...], ...]
    period_ns: int
    confidence: float
    source_model: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.created_at_ns < 0 or self.valid_until_ns <= self.created_at_ns:
            raise ValueError("action validity interval is invalid")
        if self.period_ns <= 0:
            raise ValueError("period_ns must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not self.source_model or not self.joint_targets_rad:
            raise ValueError("source_model and at least one target are required")
        width = len(self.joint_targets_rad[0])
        if width == 0 or any(len(row) != width for row in self.joint_targets_rad):
            raise ValueError("joint targets must have one consistent non-zero width")
        for index, target in enumerate(self.joint_targets_rad):
            _require_finite(target, f"joint_targets_rad[{index}]")


class SafetyStatus(StrEnum):
    ACCEPTED = "accepted"
    CLIPPED = "clipped"
    PAUSED = "paused"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    status: SafetyStatus
    reason_code: str
    message: str = ""
    clipped_targets_rad: tuple[tuple[float, ...], ...] = field(default_factory=tuple)
    schema_version: int = SCHEMA_VERSION
