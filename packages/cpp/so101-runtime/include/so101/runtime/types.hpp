#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace so101::runtime {

inline constexpr std::uint32_t kSchemaVersion = 1;

enum class RuntimeState {
  kDisarmed,
  kHoming,
  kReady,
  kExecuting,
  kPaused,
  kFault,
  kRecovery,
};

struct Observation {
  std::uint64_t timestamp_ns{};
  std::uint64_t sequence{};
  std::vector<double> joint_positions_rad;
  double gripper_position{};
  std::string calibration_version;
};

struct ActionChunk {
  std::uint64_t created_at_ns{};
  std::uint64_t valid_until_ns{};
  std::uint64_t period_ns{};
  std::vector<std::vector<double>> joint_targets_rad;
  float confidence{};
  std::string source_model;
};

enum class SafetyStatus {
  kAccepted,
  kClipped,
  kPaused,
  kRejected,
};

struct SafetyDecision {
  SafetyStatus status{SafetyStatus::kRejected};
  std::string reason_code;
  std::string message;
};

struct BackendHealth {
  bool ready{};
  std::string detail;
};

}  // namespace so101::runtime
