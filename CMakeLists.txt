cmake_minimum_required(VERSION 3.20)
project(lerobot_so101 LANGUAGES CXX)

include(CTest)
add_subdirectory(packages/cpp/so101-core)
add_subdirectory(packages/cpp/so101-runtime)
