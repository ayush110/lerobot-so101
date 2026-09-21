# Deployment

Deployment turns an evaluated checkpoint into an immutable model bundle with a
contract version, preprocessing definition, expected tensor shapes, runtime
requirements, latency budget, checksum, and rollback target.

The policy process proposes actions. The C++ runtime owns command freshness,
trajectory validation, safety state, hardware access, logging, and emergency
stop behavior.
