"""Gymnasium environment for the SO-101 keyed-assembly benchmark."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import gymnasium as gym
import mujoco
import numpy as np

from .scene import Scene, sample_scene, seed_for
from .task import EpisodeMetrics, Stage

JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
GRIPPER_CLOSED = 0.0
GRIPPER_OPEN = 1.2


def _asset_root() -> Path:
    packaged = Path(__file__).resolve().parent / "assets" / "so101"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[2] / "assets" / "so101"


@dataclass(frozen=True, slots=True)
class MujocoConfig:
    split: str = "train"
    max_steps: int = 500
    control_dt: float = 0.05
    width: int = 640
    height: int = 480
    include_rgb: bool = False
    render_mode: str | None = None

    def __post_init__(self) -> None:
        if self.split not in {"train", "validation", "hidden"}:
            raise ValueError(f"unknown split {self.split!r}")
        if self.max_steps <= 0 or self.control_dt <= 0.0:
            raise ValueError("max_steps and control_dt must be positive")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("render dimensions must be positive")
        if self.render_mode not in {None, "rgb_array"}:
            raise ValueError("render_mode must be None or 'rgb_array'")


def build_model() -> mujoco.MjModel:
    """Compile the official URDF into an instrumented assembly scene."""
    urdf = _asset_root() / "so101_new_calib.urdf"
    if not urdf.exists():
        raise FileNotFoundError(f"SO-101 model is missing: {urdf}")

    spec = mujoco.MjSpec.from_file(str(urdf))
    spec.modelname = "so101_keyed_assembly"
    spec.option.timestep = 0.002
    spec.option.gravity = [0.0, 0.0, -9.81]

    # Printed visual meshes overlap at adjacent joints. Until measured convex
    # proxies are available, disable those mesh collisions rather than report
    # false self-collisions.
    for geom in spec.geoms:
        geom.contype = 0
        geom.conaffinity = 0

    world = spec.worldbody
    world.add_light(name="key_light", pos=[0.0, -0.3, 0.8], dir=[0.2, 0.2, -1.0])
    world.add_camera(
        name="overview",
        pos=[0.55, -0.55, 0.48],
        xyaxes=[0.72, 0.69, 0.0, -0.35, 0.36, 0.86],
        fovy=48,
    )
    world.add_geom(
        name="floor",
        type=mujoco.mjtGeom.mjGEOM_PLANE,
        size=[1.0, 1.0, 0.05],
        rgba=[0.16, 0.18, 0.21, 1.0],
        friction=[0.9, 0.02, 0.001],
        contype=1,
        conaffinity=1,
    )
    world.add_geom(
        name="work_surface",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.22, 0.0, 0.005],
        size=[0.24, 0.24, 0.005],
        rgba=[0.34, 0.36, 0.40, 1.0],
        friction=[0.9, 0.02, 0.001],
        contype=1,
        conaffinity=1,
    )

    part_a = world.add_body(name="part_a", pos=[0.24, -0.08, 0.03])
    part_a.add_freejoint(name="part_a_free")
    part_a.add_geom(
        name="part_a_geom",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=[0.025, 0.018, 0.015],
        mass=0.025,
        rgba=[0.12, 0.48, 0.92, 1.0],
        friction=[0.8, 0.02, 0.001],
        contype=1,
        conaffinity=1,
    )
    part_a.add_site(name="part_a_grasp", pos=[0, 0, 0.018], size=[0.006, 0, 0])
    part_a.add_site(name="part_a_mate", pos=[0.036, 0, 0], size=[0.005, 0, 0])
    part_a.add_geom(
        name="part_a_key",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.028, 0.0, 0.0],
        size=[0.008, 0.008, 0.008],
        mass=0.004,
        rgba=[0.08, 0.30, 0.72, 1.0],
        contype=1,
        conaffinity=1,
    )

    part_b = world.add_body(name="part_b", pos=[0.24, 0.08, 0.03])
    part_b.add_freejoint(name="part_b_free")
    part_b.add_geom(
        name="part_b_geom",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=[0.028, 0.022, 0.015],
        mass=0.03,
        rgba=[0.94, 0.48, 0.12, 1.0],
        friction=[0.8, 0.02, 0.001],
        contype=1,
        conaffinity=1,
    )
    part_b.add_site(name="part_b_mate", pos=[-0.030, 0, 0], size=[0.005, 0, 0])

    world.add_geom(
        name="inspection_fixture",
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0.34, 0.0, 0.018],
        size=[0.075, 0.055, 0.008],
        rgba=[0.18, 0.72, 0.32, 1.0],
        contype=1,
        conaffinity=1,
    )
    # A shallow tray makes the inspection goal physically meaningful: the
    # assembly must be released inside the fixture and remain contained while
    # settling, rather than balancing on an unbounded marker plate.
    for name, position, size in (
        ("fixture_wall_left", [0.262, 0.0, 0.046], [0.003, 0.061, 0.020]),
        ("fixture_wall_right", [0.418, 0.0, 0.046], [0.003, 0.061, 0.020]),
        ("fixture_wall_front", [0.34, -0.058, 0.046], [0.081, 0.003, 0.020]),
        ("fixture_wall_back", [0.34, 0.058, 0.046], [0.081, 0.003, 0.020]),
    ):
        world.add_geom(
            name=name,
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=position,
            size=size,
            rgba=[0.12, 0.50, 0.24, 1.0],
            friction=[0.9, 0.02, 0.001],
            contype=1,
            conaffinity=1,
        )
    spec.body("gripper_frame_link").add_site(
        name="end_effector",
        type=mujoco.mjtGeom.mjGEOM_SPHERE,
        size=[0.008, 0.0, 0.0],
        rgba=[1.0, 0.1, 0.1, 0.6],
    )

    for body in spec.bodies:
        if body.name not in {"world", "part_a", "part_b"}:
            body.gravcomp = 1.0

    spec.add_equality(
        name="grasp_part_a",
        type=mujoco.mjtEq.mjEQ_WELD,
        objtype=mujoco.mjtObj.mjOBJ_SITE,
        name1="end_effector",
        name2="part_a_grasp",
        active=0,
        solref=[0.01, 1.0],
        solimp=[0.9, 0.95, 0.001, 0.5, 2.0],
    )
    spec.add_equality(
        name="mate_parts",
        type=mujoco.mjtEq.mjEQ_WELD,
        objtype=mujoco.mjtObj.mjOBJ_SITE,
        name1="part_a_mate",
        name2="part_b_mate",
        active=0,
        solref=[0.01, 1.0],
        solimp=[0.9, 0.95, 0.001, 0.5, 2.0],
    )

    for joint in spec.joints:
        if joint.name not in JOINT_NAMES:
            continue
        joint.damping = [0.8 if joint.name != "gripper" else 0.25, 0.0, 0.0]
        joint.armature = 0.03 if joint.name != "gripper" else 0.01
        joint.frictionloss = 0.03
        low, high = float(joint.range[0]), float(joint.range[1])
        kp = 24.0 if joint.name != "gripper" else 8.0
        spec.add_actuator(
            name=f"{joint.name}_position",
            gaintype=mujoco.mjtGain.mjGAIN_FIXED,
            gainprm=[kp, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            biastype=mujoco.mjtBias.mjBIAS_AFFINE,
            biasprm=[0, -kp, -0.8, 0, 0, 0, 0, 0, 0, 0],
            dyntype=mujoco.mjtDyn.mjDYN_NONE,
            trntype=mujoco.mjtTrn.mjTRN_JOINT,
            target=joint.name,
            ctrllimited=1,
            ctrlrange=[low, high],
            forcelimited=1,
            forcerange=[-4.0, 4.0],
        )
    return spec.compile()


class So101AssemblyEnv(gym.Env):
    metadata: ClassVar = {"render_modes": ["rgb_array"], "render_fps": 20}

    def __init__(self, config: MujocoConfig | None = None):
        super().__init__()
        self.config = config or MujocoConfig()
        self.render_mode = self.config.render_mode
        self.model = build_model()
        self.data = mujoco.MjData(self.model)
        self.frame_skip = max(1, round(self.config.control_dt / self.model.opt.timestep))
        self.action_space = gym.spaces.Box(
            low=self.model.actuator_ctrlrange[:, 0].astype(np.float32),
            high=self.model.actuator_ctrlrange[:, 1].astype(np.float32),
            dtype=np.float32,
        )
        self.observation_space = gym.spaces.Dict(
            {
                "state": gym.spaces.Box(-np.inf, np.inf, shape=(19,), dtype=np.float32),
                "joints": gym.spaces.Box(-np.inf, np.inf, shape=(5,), dtype=np.float32),
                "gripper": gym.spaces.Box(0.0, 1.0, shape=(), dtype=np.float32),
                "stage": gym.spaces.Discrete(4),
                "rgb": gym.spaces.Box(
                    0,
                    255,
                    shape=(self.config.height, self.config.width, 3),
                    dtype=np.uint8,
                ),
            }
        )
        self.renderer: mujoco.Renderer | None = None
        self.stage = Stage.RETRIEVE
        self.metrics = EpisodeMetrics()
        self.episode_index = 0
        self.scene: Scene | None = None
        self._settled_steps = 0
        self._action_queue: deque[np.ndarray] = deque()
        self._observation_queue: deque[dict[str, Any]] = deque()
        self._last_applied = np.zeros(6, dtype=np.float64)

    def _equality_active(self, name: str) -> bool:
        return bool(self.data.eq_active[self.model.equality(name).id])

    def _set_equality(self, name: str, active: bool) -> None:
        self.data.eq_active[self.model.equality(name).id] = active

    def _body_pose(self, name: str) -> np.ndarray:
        body_id = self.model.body(name).id
        matrix = self.data.xmat[body_id].reshape(3, 3)
        yaw = float(np.arctan2(matrix[1, 0], matrix[0, 0]))
        return np.concatenate([self.data.xpos[body_id].copy(), [yaw]])

    def _current_observation(self) -> dict[str, Any]:
        joints = self.data.qpos[:5].astype(np.float32).copy()
        gripper_joint = float(self.data.qpos[5])
        low, high = self.model.jnt_range[5]
        gripper = np.float32(np.clip((gripper_joint - low) / (high - low), 0.0, 1.0))
        part_a, part_b = self._body_pose("part_a"), self._body_pose("part_b")
        fixture = np.array([0.34, 0.0, 0.018, 0.0])
        state = np.concatenate([joints, [gripper], part_a, part_b, fixture, [self.stage]]).astype(
            np.float32
        )
        rgb = (
            self.render()
            if self.config.include_rgb or self.render_mode == "rgb_array"
            else np.zeros((self.config.height, self.config.width, 3), dtype=np.uint8)
        )
        return {
            "state": state,
            "joints": joints,
            "gripper": gripper,
            "stage": int(self.stage),
            "rgb": rgb,
        }

    @staticmethod
    def _copy_observation(observation: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.copy() if isinstance(value, np.ndarray) else value
            for key, value in observation.items()
        }

    def _delayed_observation(self) -> dict[str, Any]:
        assert self.scene is not None
        current = self._current_observation()
        self._observation_queue.append(self._copy_observation(current))
        while len(self._observation_queue) > self.scene.observation_delay_steps + 1:
            self._observation_queue.popleft()
        return self._copy_observation(self._observation_queue[0])

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        super().reset(seed=seed)
        del options
        actual_seed = seed if seed is not None else seed_for(self.config.split, self.episode_index)
        self.episode_index += 1
        self.scene = sample_scene(actual_seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:6] = 0.0

        for body_name, pose in (("part_a", self.scene.part_a), ("part_b", self.scene.part_b)):
            joint_id = self.model.joint(f"{body_name}_free").id
            address = self.model.jnt_qposadr[joint_id]
            self.data.qpos[address : address + 3] = pose[:3] + np.array([0, 0, 0.015])
            self.data.qpos[address + 3 : address + 7] = [
                np.cos(pose[3] / 2),
                0,
                0,
                np.sin(pose[3] / 2),
            ]
            self.model.geom(f"{body_name}_geom").friction[0] = self.scene.friction

        self.data.ctrl[:] = 0.0
        self.stage = Stage.RETRIEVE
        self.metrics = EpisodeMetrics()
        self._settled_steps = 0
        self._last_applied = np.zeros(6, dtype=np.float64)
        self._action_queue = deque(
            np.zeros(6, dtype=np.float64) for _ in range(self.scene.motor_delay_steps)
        )
        self._observation_queue.clear()
        mujoco.mj_forward(self.model, self.data)
        initial = self._current_observation()
        for _ in range(self.scene.observation_delay_steps + 1):
            self._observation_queue.append(self._copy_observation(initial))
        return self._copy_observation(initial), {
            "seed": actual_seed,
            "split": self.config.split,
            "backend": "mujoco",
            "motor_delay_steps": self.scene.motor_delay_steps,
            "observation_delay_steps": self.scene.observation_delay_steps,
            "backlash_rad": self.scene.backlash_rad,
        }

    def step(self, action: np.ndarray):
        if self.scene is None:
            raise RuntimeError("reset must be called before step")
        command = np.asarray(action, dtype=np.float64)
        if command.shape != (6,) or not np.isfinite(command).all():
            raise ValueError("action must contain six finite SO-101 actuator targets")
        command = np.clip(
            command, self.model.actuator_ctrlrange[:, 0], self.model.actuator_ctrlrange[:, 1]
        )
        self._action_queue.append(command.copy())
        applied = self._action_queue.popleft()
        delta = applied - self._last_applied
        applied = self._last_applied + np.sign(delta) * np.maximum(
            np.abs(delta) - self.scene.backlash_rad, 0.0
        )
        self._last_applied = applied
        self.data.ctrl[:] = applied
        mujoco.mj_step(self.model, self.data, self.frame_skip)
        self._update_task_constraints(applied[5])
        mujoco.mj_step(self.model, self.data)
        self.metrics.steps += 1
        reward = self._update_stage()
        terminated = self.stage == Stage.COMPLETE
        truncated = self.metrics.steps >= self.config.max_steps and not terminated
        info = {
            "stage": self.stage.name.lower(),
            "metrics": dict(self.metrics.as_dict()),
            "contacts": int(self.data.ncon),
            "grasped": self._equality_active("grasp_part_a"),
            "mated": self._equality_active("mate_parts"),
            "applied_action": applied.astype(np.float32),
        }
        return self._delayed_observation(), reward, terminated, truncated, info

    def _update_task_constraints(self, gripper_command: float) -> None:
        end_effector = self.data.site("end_effector").xpos
        grasp = self.data.site("part_a_grasp").xpos
        if (
            self.stage == Stage.RETRIEVE
            and gripper_command < 0.25
            and np.linalg.norm(end_effector - grasp) < 0.035
        ):
            self._set_equality("grasp_part_a", True)
        if self.stage == Stage.MATE:
            mate_distance = np.linalg.norm(
                self.data.site("part_a_mate").xpos - self.data.site("part_b_mate").xpos
            )
            # A compliant keyed guide captures near-aligned parts before the
            # low-cost arm stalls against rigid contact. The 6.5 cm envelope
            # is an explicit fixture assumption and must be measured on the
            # physical connector before sim-to-real evaluation.
            if mate_distance < 0.065:
                self._set_equality("mate_parts", True)
        if self.stage == Stage.INSPECT and gripper_command > 0.9:
            self._set_equality("grasp_part_a", False)

    def _update_stage(self) -> float:
        if self.stage == Stage.RETRIEVE:
            success = self._equality_active("grasp_part_a") and self._body_pose("part_a")[2] > 0.07
            distance = np.linalg.norm(
                self.data.site("end_effector").xpos - self.data.site("part_a_grasp").xpos
            )
        elif self.stage == Stage.MATE:
            success = self._equality_active("mate_parts")
            distance = np.linalg.norm(
                self.data.site("part_a_mate").xpos - self.data.site("part_b_mate").xpos
            )
        else:
            positions = np.stack([self._body_pose("part_a")[:3], self._body_pose("part_b")[:3]])
            fixture = np.array([0.34, 0.0])
            offsets = np.abs(positions[:, :2] - fixture)
            inside = bool(np.all(offsets[:, 0] < 0.075) and np.all(offsets[:, 1] < 0.055))
            released = not self._equality_active("grasp_part_a")
            part_velocity = np.linalg.norm(self.data.qvel[6:18])
            self._settled_steps = (
                self._settled_steps + 1 if inside and released and part_velocity < 0.15 else 0
            )
            success = self._settled_steps >= 6
            distance = float(np.mean(np.linalg.norm(positions[:, :2] - fixture, axis=1)))
        if success:
            index = int(self.stage)
            self.metrics.stage_success[index] = True
            self.stage = Stage(index + 1)
            return 1.0
        return -0.01 * float(distance)

    def render(self) -> np.ndarray:
        if self.renderer is None:
            self.renderer = mujoco.Renderer(
                self.model, height=self.config.height, width=self.config.width
            )
        self.renderer.update_scene(self.data, camera="overview")
        return self.renderer.render().copy()

    def close(self) -> None:
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None
