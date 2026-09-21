# Repository layout conventions

## Where new work goes

- A complete capability or demo starts in `projects/<name>/`.
- A reusable library with multiple consumers goes in `packages/<language>/`.
- Simulation backends and assets go in `simulation/`.
- Training/evaluation pipelines go in `training/`.
- Empirical studies and ablations go in `research/experiments/`.
- Operations, containers, services, and launch files go in `deployment/`.
- Real-arm procedures, adapters, fixtures, and calibration tooling go in
  `hardware/`.
- Dataset metadata goes in `data/manifests/`; large data stays in ignored
  directories or external storage.

## Naming

Use lowercase kebab-case for filesystem packages and project directories,
snake_case for Python modules, and standard ecosystem conventions for C++.
Include `so101` in published package names to avoid generic collisions.

## Configuration

Committed config is portable and contains no personal paths. Put host-specific
overrides in `configs/local/`. Resolve and save the final merged config beside
every run so results do not depend on invisible defaults.

## Versioning

The Protobuf package version (`so101.v1`) is the compatibility boundary.
Adding optional fields is compatible; changing meaning, units, numbering, or
required behavior creates a new package version. Units belong in field names.
