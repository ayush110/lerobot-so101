#!/usr/bin/env bash
set -u

failures=0

check_required() {
    if command -v "$1" >/dev/null 2>&1; then
        printf "[ok]      %-12s %s\n" "$1" "$(command -v "$1")"
    else
        printf "[missing] %-12s required for %s\n" "$1" "$2"
        failures=$((failures + 1))
    fi
}

check_optional() {
    if command -v "$1" >/dev/null 2>&1; then
        printf "[ok]      %-12s %s\n" "$1" "$(command -v "$1")"
    else
        printf "[optional] %-11s install for %s\n" "$1" "$2"
    fi
}

printf "SO-101 workspace doctor\n"
check_required python3 "Python packages and orchestration"
check_required c++ "the C++ robot runtime"
check_optional uv "reproducible Python environments"
check_optional cmake "the C++ robotics core"
check_optional protoc "generated cross-process protocol bindings"
check_optional docker "deployment containers"
check_optional nvidia-smi "CUDA development on a Linux GPU host"

python3 - <<'PY'
import importlib.util
import platform
import sys

print(f"[info]     platform     {platform.platform()}")
print(f"[info]     python       {sys.version.split()[0]}")
for module, purpose in (
    ("torch", "training and inference"),
    ("mujoco", "local simulation"),
    ("lerobot", "datasets and policies"),
):
    state = "ok" if importlib.util.find_spec(module) else "not installed"
    print(f"[python]   {module:<12} {state} ({purpose})")
PY

if [ "$failures" -ne 0 ]; then
    printf "Doctor found %d missing required tool(s).\n" "$failures"
    exit 1
fi

printf "Required base toolchain is ready. Optional capabilities are listed above.\n"
