# Repository operating guide

## Scope

This is the root of all SO-101 projects. Prefer domain boundaries over a large
shared framework, and keep simulation-only assumptions out of hardware APIs.

## Required checks

Run `make test` after cross-language changes. Run the narrow language-specific
target during iteration: `make test-python` or `make test-cpp`.

## Safety

Code that can actuate hardware must default to dry-run/disarmed. A learned
policy never writes directly to a servo bus; it proposes an action chunk that
the C++ runtime validates. Do not commit calibration files containing machine
or user-specific device identifiers unless they are sanitized examples.

## Data and experiments

Do not commit recordings, model weights, raw camera data, or generated build
trees. Commit manifests, checksums, schemas, metrics, and small test fixtures.
Every reported experiment must include its config, random seed, code revision,
dataset revision, and environment revision.

## Compatibility

Version public schemas. Breaking changes require a migration note or an ADR.
Keep optional CUDA and Isaac dependencies behind explicit feature/profile
boundaries so the base workspace remains usable on macOS.
