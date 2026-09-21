#pragma once

#include <string_view>

namespace so101::core {

inline constexpr int kSchemaVersion = 1;
std::string_view version() noexcept;

}  // namespace so101::core
