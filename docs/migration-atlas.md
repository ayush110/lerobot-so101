# Staged Atlas migration

The current Atlas workspace is working with real SO-101 hardware, calibration,
recordings, and generated artifacts. It has therefore not been moved or copied
automatically. Copying the entire tree would also duplicate the large virtual
environment and legacy Rust build output.

## Target mapping

| Current path | Monorepo destination | Treatment |
| --- | --- | --- |
| `atlas_py/` | `projects/atlas/` and reusable Python packages | Split by responsibility |
| `runtime/` | `packages/cpp/so101-runtime/` | Port behavior and tests; replace the implementation |
| `robotics_core/` | `packages/cpp/so101-core/` | Port behind a stable C ABI |
| `cuda/` | `packages/cuda/so101-ops/` | Keep portable fallback and benchmarks |
| `proto/` | `packages/proto/so101/v1/` | Reconcile with the new versioned schema |
| `configs/` | `configs/` | Commit portable examples; local values stay ignored |
| `tests/` | Co-located package tests and end-to-end project tests | Move with ownership |
| `docs/` | `docs/` or `projects/atlas/` | Separate system docs from project docs |
| `artifacts/` | `data/runs/` or external object storage | Do not commit bulk artifacts |
| `.venv/`, `target/` | None | Recreate environments; discard legacy Rust output |

## Migration gates

1. Record the current Atlas tests and one known replay fixture as the baseline.
2. Port contracts and pure libraries without changing hardware behavior.
3. Port simulation and compare deterministic seeds and benchmark metrics.
4. Port replay and require identical safety/state-machine decisions.
5. Copy sanitized calibration examples; retain live local calibration outside
   Git and reference it through host config.
6. Port the hardware backend in dry-run mode, then verify read-only telemetry.
7. Perform a deliberately small bounded-motion test under the supervisor.
8. Switch the working commands only after all prior gates pass.
9. Archive the old layout after a full simulation and hardware smoke test.

The migration should preserve history where practical with `git mv` once the
new ownership split is agreed. Do not move the active virtual environment,
build trees, recordings, or live gateway state.
