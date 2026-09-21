#!/usr/bin/env bash
set -euo pipefail

if command -v cmake >/dev/null 2>&1; then
    cmake -S . -B build/cmake -DBUILD_TESTING=ON
    cmake --build build/cmake
    ctest --test-dir build/cmake --output-on-failure
    exit 0
fi

if command -v c++ >/dev/null 2>&1; then
    printf "[fallback] C++ tests: compiling directly because cmake is unavailable\n"
    mkdir -p build/cpp-fallback
    c++ -std=c++20 -Wall -Wextra -Werror \
        -Ipackages/cpp/so101-core/include \
        packages/cpp/so101-core/src/version.cpp \
        packages/cpp/so101-core/tests/version_test.cpp \
        -o build/cpp-fallback/so101_core_test
    build/cpp-fallback/so101_core_test
    c++ -std=c++20 -Wall -Wextra -Wpedantic -Werror \
        -Ipackages/cpp/so101-core/include \
        -Ipackages/cpp/so101-runtime/include \
        packages/cpp/so101-core/src/version.cpp \
        packages/cpp/so101-runtime/src/safety.cpp \
        packages/cpp/so101-runtime/src/state_machine.cpp \
        packages/cpp/so101-runtime/tests/runtime_test.cpp \
        -o build/cpp-fallback/so101_runtime_test
    build/cpp-fallback/so101_runtime_test
    exit 0
fi

printf "[skip] C++ tests: neither cmake nor a C++ compiler is installed\n"
