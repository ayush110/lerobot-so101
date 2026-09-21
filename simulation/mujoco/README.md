# MuJoCo backend

This directory will contain SO-101 MJCF/URDF assets, Gymnasium environments,
scripted oracle controllers, domain randomization, and deterministic tests.

MuJoCo is a physics engine for rigid-body dynamics and contact. Here it is used
to develop without risking the arm, generate demonstrations, verify geometry
and controllers, run regression tests, and train policies against randomized
conditions. It is not a perfect replica of servo backlash, camera latency,
friction, or compliant contact; those gaps must be measured and modeled.

The first environment gate is a reset-and-step smoke test on CPU. The next is
agreement between simulator FK/Jacobians and `packages/cpp/so101-core`.
