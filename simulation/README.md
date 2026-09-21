# Simulation

MuJoCo is the canonical local and continuous-integration backend. It should be
fast, deterministic under fixed seeds, headless-capable, and semantically
identical to hardware at the `Observation` and `ActionChunk` boundary.

Isaac integration is optional and reserved for GPU-parallel domain
randomization and profiling. It must consume the same task definitions and
produce the same benchmark metrics.
