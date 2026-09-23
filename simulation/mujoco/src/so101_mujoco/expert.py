"""Scripted operational-space oracle for validating the assembly benchmark."""

from __future__ import annotations

from enum import Enum, auto

import mujoco
import numpy as np

from .environment import GRIPPER_CLOSED, GRIPPER_OPEN, So101AssemblyEnv
from .task import Stage


class ExpertPhase(Enum):
    ABOVE_A = auto()
    DESCEND_A = auto()
    CLOSE_A = auto()
    LIFT_A = auto()
    ABOVE_MATE = auto()
    ALIGN_MATE = auto()
    LIFT_ASSEMBLY = auto()
    ABOVE_FIXTURE = auto()
    LOWER_FIXTURE = auto()
    PLACE_SETTLE = auto()
    RELEASE = auto()
    SETTLE = auto()


class MujocoAssemblyExpert:
    """Damped-least-squares IK oracle whose actions pass through simulation.

    This is deliberately not a teleporter. It emits the same six joint-position
    targets as a learned policy, and the environment applies actuator delay,
    backlash, position limits, and MuJoCo dynamics.
    """

    def __init__(self, env: So101AssemblyEnv):
        self.env = env
        self._scratch = mujoco.MjData(env.model)
        self.phase = ExpertPhase.ABOVE_A
        self.phase_steps = 0
        self._cached_target: np.ndarray | None = None
        self._cached_goal: np.ndarray | None = None

    def reset(self) -> None:
        self.phase = ExpertPhase.ABOVE_A
        self.phase_steps = 0
        self._cached_target = None
        self._cached_goal = None

    def _transition(self, phase: ExpertPhase) -> None:
        if phase != self.phase:
            self.phase = phase
            self.phase_steps = 0
            self._cached_target = None
            self._cached_goal = None

    def _solve_ik(self, target: np.ndarray) -> np.ndarray:
        model = self.env.model
        q = self.env.data.ctrl[:5].copy()
        self._scratch.qpos[:] = self.env.data.qpos
        site_id = model.site("end_effector").id
        for _ in range(80):
            self._scratch.qpos[:5] = q
            mujoco.mj_forward(model, self._scratch)
            error = target - self._scratch.site("end_effector").xpos
            if np.linalg.norm(error) < 0.003:
                break
            jacobian_position = np.zeros((3, model.nv))
            jacobian_rotation = np.zeros((3, model.nv))
            mujoco.mj_jacSite(
                model,
                self._scratch,
                jacobian_position,
                jacobian_rotation,
                site_id,
            )
            arm_jacobian = jacobian_position[:, :5]
            delta = arm_jacobian.T @ np.linalg.solve(
                arm_jacobian @ arm_jacobian.T + 0.05**2 * np.eye(3), error
            )
            q = np.clip(
                q + np.clip(delta, -0.10, 0.10),
                model.actuator_ctrlrange[:5, 0],
                model.actuator_ctrlrange[:5, 1],
            )
        return q

    def _ik_action(self, target: np.ndarray, gripper: float) -> np.ndarray:
        target = np.asarray(target)
        if self._cached_target is None or np.linalg.norm(target - self._cached_target) > 0.008:
            self._cached_target = target.copy()
            self._cached_goal = self._solve_ik(target)
        assert self._cached_goal is not None
        current_command = self.env.data.ctrl[:5]
        # Use the runtime's conservative 0.08 rad/action limit. A smaller
        # increment can be swallowed by the worst-case sampled servo backlash.
        smooth_goal = current_command + np.clip(self._cached_goal - current_command, -0.08, 0.08)
        return np.concatenate([smooth_goal, [gripper]]).astype(np.float32)

    def act(self) -> np.ndarray:
        self.phase_steps += 1
        env = self.env
        end_effector = env.data.site("end_effector").xpos.copy()
        grasp = env.data.site("part_a_grasp").xpos.copy()
        mate_a = env.data.site("part_a_mate").xpos.copy()
        mate_b = env.data.site("part_b_mate").xpos.copy()
        fixture = np.array([0.34, 0.0, 0.04])

        if env.stage == Stage.RETRIEVE:
            target, gripper = self._retrieve(end_effector, grasp)
        elif env.stage == Stage.MATE:
            target, gripper = self._mate(end_effector, mate_a, mate_b)
        else:
            target, gripper = self._inspect(end_effector, fixture)
        return self._ik_action(target, gripper)

    def _retrieve(self, end_effector: np.ndarray, grasp: np.ndarray) -> tuple[np.ndarray, float]:
        allowed = {
            ExpertPhase.ABOVE_A,
            ExpertPhase.DESCEND_A,
            ExpertPhase.CLOSE_A,
            ExpertPhase.LIFT_A,
        }
        if self.phase not in allowed:
            self._transition(ExpertPhase.ABOVE_A)
        if self.phase == ExpertPhase.ABOVE_A:
            target = grasp + np.array([0, 0, 0.09])
            if np.linalg.norm(end_effector - target) < 0.025:
                self._transition(ExpertPhase.DESCEND_A)
        elif self.phase == ExpertPhase.DESCEND_A:
            target = grasp
            if np.linalg.norm(end_effector - target) < 0.025:
                self._transition(ExpertPhase.CLOSE_A)
        elif self.phase == ExpertPhase.CLOSE_A:
            target = grasp
            if self.env._equality_active("grasp_part_a") or self.phase_steps > 16:
                self._transition(ExpertPhase.LIFT_A)
        else:
            target = grasp + np.array([0, 0, 0.12])
        gripper = (
            GRIPPER_OPEN
            if self.phase in {ExpertPhase.ABOVE_A, ExpertPhase.DESCEND_A}
            else GRIPPER_CLOSED
        )
        return target, gripper

    def _mate(
        self, end_effector: np.ndarray, mate_a: np.ndarray, mate_b: np.ndarray
    ) -> tuple[np.ndarray, float]:
        if self.phase not in {ExpertPhase.ABOVE_MATE, ExpertPhase.ALIGN_MATE}:
            self._transition(ExpertPhase.ABOVE_MATE)
        correction = mate_b - mate_a
        if self.phase == ExpertPhase.ABOVE_MATE:
            target = end_effector + correction + np.array([0, 0, 0.07])
            if np.linalg.norm(correction[:2]) < 0.025 and mate_a[2] > mate_b[2] + 0.04:
                self._transition(ExpertPhase.ALIGN_MATE)
        else:
            target = end_effector + correction
        return target, GRIPPER_CLOSED

    def _inspect(self, end_effector: np.ndarray, fixture: np.ndarray) -> tuple[np.ndarray, float]:
        allowed = {
            ExpertPhase.LIFT_ASSEMBLY,
            ExpertPhase.ABOVE_FIXTURE,
            ExpertPhase.LOWER_FIXTURE,
            ExpertPhase.PLACE_SETTLE,
            ExpertPhase.RELEASE,
            ExpertPhase.SETTLE,
        }
        if self.phase not in allowed:
            self._transition(ExpertPhase.LIFT_ASSEMBLY)
        part_a = self.env._body_pose("part_a")[:3]
        part_b = self.env._body_pose("part_b")[:3]
        assembly_center = np.mean(np.stack([part_a, part_b]), axis=0)
        if self.phase == ExpertPhase.LIFT_ASSEMBLY:
            target = end_effector + np.array([0, 0, 0.10])
            if part_a[2] > 0.10:
                self._transition(ExpertPhase.ABOVE_FIXTURE)
        elif self.phase == ExpertPhase.ABOVE_FIXTURE:
            target = end_effector.copy()
            target[:2] += fixture[:2] - assembly_center[:2]
            target[2] = fixture[2] + 0.10
            if np.linalg.norm(assembly_center[:2] - fixture[:2]) < 0.015:
                self._transition(ExpertPhase.LOWER_FIXTURE)
        elif self.phase == ExpertPhase.LOWER_FIXTURE:
            target = end_effector.copy()
            target[:2] += fixture[:2] - assembly_center[:2]
            target[2] = fixture[2]
            # The mated pair can contact the fixture before the end-effector
            # reaches its nominal Cartesian target. Release based on horizontal
            # alignment and a conservative height gate instead of integrating
            # forever against the work surface.
            horizontally_aligned = np.linalg.norm(assembly_center[:2] - fixture[:2]) < 0.015
            if np.linalg.norm(end_effector - target) < 0.025 or (
                horizontally_aligned and end_effector[2] < 0.11
            ):
                self._transition(ExpertPhase.PLACE_SETTLE)
        elif self.phase == ExpertPhase.PLACE_SETTLE:
            target = end_effector.copy()
            part_velocity = np.linalg.norm(self.env.data.qvel[6:18])
            if self.phase_steps >= 8 and part_velocity < 0.08:
                self._transition(ExpertPhase.RELEASE)
        elif self.phase == ExpertPhase.RELEASE:
            target = end_effector.copy()
            if not self.env._equality_active("grasp_part_a"):
                self._transition(ExpertPhase.SETTLE)
        else:
            target = fixture + np.array([0, 0, 0.10])
        gripper = (
            GRIPPER_OPEN
            if self.phase in {ExpertPhase.RELEASE, ExpertPhase.SETTLE}
            else GRIPPER_CLOSED
        )
        return target, gripper
