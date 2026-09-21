# SO-101 CUDA operators

This package will hold measured PyTorch C++/CUDA extensions such as fused
RGB-D unprojection, workspace filtering, and voxel aggregation.

An operator belongs here only after a portable PyTorch implementation and
profiler trace identify a real bottleneck. Every operator must retain a CPU or
standard-PyTorch fallback, pass numerical and gradient checks, and report
end-to-end policy impact—not just isolated kernel timing.

CUDA builds are optional and are expected to run on a Linux NVIDIA machine;
the base macOS workspace must remain functional without them.
