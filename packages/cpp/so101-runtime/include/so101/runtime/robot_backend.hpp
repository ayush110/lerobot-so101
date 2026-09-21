#pragma once

#include <string_view>

#include "so101/runtime/types.hpp"

namespace so101::runtime {

// Simulation, replay, and physical SO-101 drivers implement the same contract.
// submit_validated deliberately advertises that callers must pass safety review.
class RobotBackend {
 public:
  virtual ~RobotBackend() = default;

  RobotBackend(const RobotBackend&) = delete;
  RobotBackend& operator=(const RobotBackend&) = delete;
  RobotBackend(RobotBackend&&) = delete;
  RobotBackend& operator=(RobotBackend&&) = delete;

  virtual void reset() = 0;
  [[nodiscard]] virtual Observation observe() = 0;
  virtual void submit_validated(const ActionChunk& action) = 0;
  virtual void stop() noexcept = 0;
  [[nodiscard]] virtual BackendHealth health() const = 0;
  [[nodiscard]] virtual std::string_view calibration_version() const noexcept = 0;

 protected:
  RobotBackend() = default;
};

}  // namespace so101::runtime
