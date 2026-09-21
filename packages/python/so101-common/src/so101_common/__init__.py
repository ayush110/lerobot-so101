"""Shared, dependency-light contracts for the SO-101 workspace."""

from .contracts import ActionChunk, Observation, SafetyDecision, SafetyStatus

__all__ = ["ActionChunk", "Observation", "SafetyDecision", "SafetyStatus"]
__version__ = "0.1.0"
