# Hardware

Hardware code and procedures live here; user-specific calibration output lives
under `hardware/calibration/local/` and is ignored by Git.

Bring-up order:

1. identify devices without commanding motion;
2. verify emergency power cutoff;
3. read one motor at a time and confirm ID/direction;
4. calibrate offsets and limits at conservative speeds;
5. validate the replay backend, then dry-run hardware commands;
6. execute small, bounded motions under the C++ supervisor;
7. validate each task stage before running a full learned policy.

Camera applications on macOS can select the wrist USB camera as a continuity
or conferencing camera. Give devices stable logical names in local config and
explicitly select the Mac camera in conferencing applications.
