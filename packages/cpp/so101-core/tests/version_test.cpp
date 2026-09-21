#include "so101/core/version.hpp"

#include <cassert>

int main() {
  static_assert(so101::core::kSchemaVersion == 1);
  assert(so101::core::version() == "0.1.0");
  return 0;
}
