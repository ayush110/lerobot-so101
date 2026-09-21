add_library(so101_core STATIC src/version.cpp)
add_library(so101::core ALIAS so101_core)

target_include_directories(so101_core PUBLIC include)
target_compile_features(so101_core PUBLIC cxx_std_20)

if(BUILD_TESTING)
  add_executable(so101_core_test tests/version_test.cpp)
  target_link_libraries(so101_core_test PRIVATE so101::core)
  add_test(NAME so101_core_test COMMAND so101_core_test)
endif()
