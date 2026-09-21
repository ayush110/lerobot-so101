# Training and evaluation

This area owns adapters to LeRobot, dataset loading, policy configuration,
training entry points, evaluation, and model export. It does not own robot
actuation.

Initial baselines should use identical splits and evaluation seeds:

1. privileged-state behavior cloning;
2. ACT from vision and proprioception;
3. diffusion or transformer policy with the same observations;
4. hierarchical action chunking after the flat baselines are understood.

Every run records a resolved config, git revision, dataset revision, random
seeds, package versions, stage metrics, full-task success, confidence
intervals, and latency distributions.
