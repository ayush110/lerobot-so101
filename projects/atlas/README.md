# Project Atlas

Atlas is the flagship long-horizon keyed-assembly project. The currently
working implementation remains at the parent workspace root until the staged
migration in `docs/migration-atlas.md` is complete and verified.

This directory will own task-level configuration, composition, benchmark
entry points, and project-specific documentation. Reusable runtime, simulation,
perception, and learning code should graduate into `packages/`, `simulation/`,
or `training/` only after its boundary is stable.
