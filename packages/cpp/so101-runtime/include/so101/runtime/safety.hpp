#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "so101/runtime/types.hpp"

namespace so101::runtime {

struct SafetyLimits {
  std::vector<double> joint_min_rad;
  std::vector<double> joint_max_rad;
  double maximum_step_rad{0.08};
  std::size_t maximum_chunk_steps{16};
};

class SafetyValidator {
 public:
  explicit SafetyValidator(SafetyLimits limits);

  [[nodiscard]] SafetyDecision validate(const Observation& observation,
                                        const ActionChunk& action,
                                        std::uint64_t now_ns) const;

 private:
  SafetyLimits limits_;
};

}  // namespace so101::runtime
