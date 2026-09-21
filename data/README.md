# Data infrastructure

The repository stores metadata; object storage or local disks store bulk data.

- `manifests/`: immutable dataset manifests, checksums, schema revisions, and
  train/validation/test membership.
- `raw/`: untouched recordings from simulation, replay, or hardware.
- `processed/`: normalized LeRobot datasets and derived features.
- `cache/`: disposable downloads and transforms.
- `runs/`: local metrics, logs, videos, and profiler traces.

The four bulk directories are gitignored. Keep their `.gitkeep` files so a
fresh checkout exposes the intended mount points.

A dataset manifest should include its source, license, collection code
revision, calibration revision, observation/action schema revision, episode
count, checksums, and parent dataset if it is derived.
