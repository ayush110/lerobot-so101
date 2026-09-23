# MuJoCo backend

This directory contains the official SO-101 URDF/mesh assets, a Gymnasium
environment, deterministic scene splits, and a LeRobot-compatible vector
environment entry point.

MuJoCo is a physics engine for rigid-body dynamics and contact. Here it is used
to develop without risking the arm, generate demonstrations, verify geometry
and controllers, run regression tests, and train policies against randomized
conditions. It is not a perfect replica of servo backlash, camera latency,
friction, or compliant contact; those gaps must be measured and modeled.

The first environment gate is a reset-and-step smoke test on CPU. The next is
agreement between simulator FK/Jacobians and `packages/cpp/so101-core`.

## Run it

From the monorepo root, use Python 3.12 with the `robotics` dependency group
installed:

```bash
uv sync --all-packages --group robotics
uv run so101-mujoco-smoke --steps 20
```

The smoke command prints a JSON result and does not open a window. Rendering is
opt-in because CI and remote training workers are normally headless.

Validate the complete scripted oracle on the hidden benchmark split:

```bash
uv run so101-mujoco-oracle evaluate --split hidden --episodes 25
```

Record state/action demonstrations directly in LeRobotDataset v3 format:

```bash
uv sync --all-packages --group robotics --extra lerobot
uv run so101-mujoco-oracle record \
  --split train \
  --episodes 25 \
  --output data/processed/so101-mujoco-oracle \
  --repo-id local/so101-mujoco-oracle
```

Dataset recording is local by default and does not upload anything. Each frame
contains the 19-value privileged benchmark state, five arm joints, normalized
gripper position, task stage, six-value action, reward, success/done flags, task
instruction, and simulation seed. Camera-video recording will be added after
the state-only oracle dataset validates the control and task semantics.

Python API:

```python
from so101_mujoco import So101AssemblyEnv, make_env

env = So101AssemblyEnv()
observation, info = env.reset(seed=2000)
vector_env = make_env(n_envs=4, use_async_envs=False, cfg={"split": "train"})
```

The environment takes six joint-position targets: five arm joints followed by
the gripper. It returns joints, normalized gripper position, task stage,
privileged benchmark state, and an optional RGB frame.
