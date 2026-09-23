# LeRobot SO-101 Lab

This is the home for simulation, robot learning, research, data infrastructure,
deployment, and hardware work for the SO-101 arm. It is a Python/C++ monorepo:
Python owns experiments and ML, C++ owns the production robot runtime and
numerical robotics, and Protobuf defines the contracts between them.

The repository starts small on purpose. New code should enter a reusable
package only after a project proves the interface it needs.

## Repository map

```text
apps/          Human-facing CLIs, dashboards, and operators
configs/       Versioned robot, task, policy, and environment configuration
data/          Dataset manifests and local data mount points
deployment/    Containers, launch definitions, and machine setup
docs/          Architecture, decisions, runbooks, and experiment standards
hardware/      SO-101 bring-up, calibration, fixtures, and hardware adapters
packages/      Shared Python, C++, CUDA, and Protobuf components
projects/      End-to-end robot projects and benchmark applications
research/      Experiment records, papers, and reusable research tooling
simulation/    MuJoCo primary simulator and optional Isaac integration
training/      LeRobot datasets, policies, training, evaluation, and export
```

## Design rules

- Simulation and hardware implement the same observation/action contract.
- The C++ supervisor is the final authority over physical commands.
- Large datasets, checkpoints, recordings, build outputs, and secrets are not
  committed. Their small manifests and metadata are committed.
- Experiments are immutable records: config, code revision, seed, metrics, and
  artifact references travel together.
- MuJoCo is the local and CI simulator. Isaac is an optional GPU-scale backend.
- LeRobot is integrated through adapters so upstream upgrades do not leak into
  every project.

## First commands

```bash
cd /Users/ayushshah/Documents/Robotics/lerobot-so101
make doctor
make test
```

Python 3.12 is the supported robotics/ML environment. The system Python may be
newer than PyTorch, LeRobot, or MuJoCo support.

Create the Python environment with `uv` when installed:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync --all-packages --group robotics
```

The old Atlas workspace has deliberately not been moved yet. See
[`docs/migration-atlas.md`](docs/migration-atlas.md) for the staged migration
that preserves the working arm setup.

## Current milestone

The first vertical slice is operational: the official SO-101 URDF compiles in
MuJoCo, deterministic train/validation/hidden scenes reset and step through the
Gymnasium API, and `make_env(...)` creates synchronous or asynchronous vector
environments. The simulator models sampled friction, command delay, observation
delay, and backlash, and packages its licensed URDF/STL assets in the wheel. A
damped-least-squares IK oracle completes the three-stage benchmark and records
state/action demonstrations directly into LeRobotDataset format.

```bash
uv run so101-mujoco-smoke --steps 20 --seed 2000
uv run so101-mujoco-oracle evaluate --split hidden --episodes 25
```

## Project lifecycle

1. Define the task and acceptance metrics in `projects/<name>/`.
2. Validate it in `simulation/mujoco/` with deterministic seeds.
3. Collect data using versioned schemas and manifests in `data/`.
4. Train and evaluate from `training/`, recording an experiment in `research/`.
5. Export an immutable model bundle to `deployment/`.
6. Execute through the C++ supervisor and hardware adapter, never directly
   from a learned policy.

## License

MIT. See [`LICENSE`](LICENSE).
