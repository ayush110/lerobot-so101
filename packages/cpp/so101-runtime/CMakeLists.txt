add_library(so101_runtime STATIC
  src/safety.cpp
  src/state_machine.cpp
)
add_library(so101::runtime ALIAS so101_runtime)

target_include_directories(so101_runtime PUBLIC include)
target_compile_features(so101_runtime PUBLIC cxx_std_20)
target_link_libraries(so101_runtime PUBLIC so101::core)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(so101_runtime PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

option(SO101_ENABLE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)
if(SO101_ENABLE_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(so101_runtime PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(so101_runtime PRIVATE -fsanitize=address,undefined)
endif()

if(BUILD_TESTING)
  add_executable(so101_runtime_test tests/runtime_test.cpp)
  target_link_libraries(so101_runtime_test PRIVATE so101::runtime)
  add_test(NAME so101_runtime_test COMMAND so101_runtime_test)
endif()
