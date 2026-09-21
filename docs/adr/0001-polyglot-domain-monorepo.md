# ADR 0001: Python/C++ domain monorepo

- Status: accepted
- Date: 2026-09-20

## Context

SO-101 projects need fast ML iteration, a robust hardware runtime, portable
robotics math, GPU acceleration, deterministic simulation, durable data
contracts, and deployable artifacts. C++ provides one implementation language
for the runtime, robotics math, native inference, and CUDA integration, avoiding
an additional foreign-function boundary.

## Decision

Use domain-oriented top-level directories and language-oriented shared package
directories. Version the robot boundary with Protobuf. Keep C++ in authority
for physical execution and numerical robotics, Python/PyTorch in authority for
learning and research, and CUDA optional.

## Consequences

Cross-language schema compatibility and root-level testing remain mandatory.
C++ offers direct access to mature robotics and inference libraries, at the
cost of requiring stricter memory-safety practices, sanitizers, and careful
ownership at process boundaries. macOS remains a supported development
environment even though CUDA and Isaac workloads run elsewhere.
