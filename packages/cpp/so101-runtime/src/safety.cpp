#include "so101/runtime/safety.hpp"

#include <cmath>
#include <stdexcept>
#include <utility>

namespace so101::runtime {
namespace {

SafetyDecision Reject(std::string reason, std::string message) {
  return {SafetyStatus::kRejected, std::move(reason), std::move(message)};
}

bool AllFinite(const std::vector<double>& values) {
  for (const double value : values) {
    if (!std::isfinite(value)) {
      return false;
    }
  }
  return true;
}

}  // namespace

SafetyValidator::SafetyValidator(SafetyLimits limits) : limits_(std::move(limits)) {
  if (limits_.joint_min_rad.empty() ||
      limits_.joint_min_rad.size() != limits_.joint_max_rad.size()) {
    throw std::invalid_argument("joint limits must have equal non-zero size");
  }
  if (!(limits_.maximum_step_rad > 0.0) || limits_.maximum_chunk_steps == 0) {
    throw std::invalid_argument("step and chunk limits must be positive");
  }
  for (std::size_t i = 0; i < limits_.joint_min_rad.size(); ++i) {
    if (!std::isfinite(limits_.joint_min_rad[i]) ||
        !std::isfinite(limits_.joint_max_rad[i]) ||
        limits_.joint_min_rad[i] >= limits_.joint_max_rad[i]) {
      throw std::invalid_argument("each joint minimum must be finite and below its maximum");
    }
  }
}

SafetyDecision SafetyValidator::validate(const Observation& observation,
                                         const ActionChunk& action,
                                         const std::uint64_t now_ns) const {
  const std::size_t joint_count = limits_.joint_min_rad.size();
  if (observation.joint_positions_rad.size() != joint_count ||
      !AllFinite(observation.joint_positions_rad)) {
    return Reject("invalid_observation", "joint observation has an invalid shape or value");
  }
  if (action.created_at_ns >= action.valid_until_ns || now_ns > action.valid_until_ns) {
    return Reject("stale_action", "action validity window has expired or is malformed");
  }
  if (action.period_ns == 0 || !std::isfinite(action.confidence) || action.confidence < 0.0F ||
      action.confidence > 1.0F || action.source_model.empty()) {
    return Reject("invalid_metadata", "action metadata is incomplete or malformed");
  }
  if (action.joint_targets_rad.empty() ||
      action.joint_targets_rad.size() > limits_.maximum_chunk_steps) {
    return Reject("invalid_chunk_length", "action chunk length is outside configured limits");
  }

  std::vector<double> previous = observation.joint_positions_rad;
  for (const auto& target : action.joint_targets_rad) {
    if (target.size() != joint_count || !AllFinite(target)) {
      return Reject("invalid_target", "joint target has an invalid shape or value");
    }
    for (std::size_t joint = 0; joint < joint_count; ++joint) {
      if (target[joint] < limits_.joint_min_rad[joint] ||
          target[joint] > limits_.joint_max_rad[joint]) {
        return Reject("joint_limit", "joint target exceeds configured position limits");
      }
      if (std::abs(target[joint] - previous[joint]) > limits_.maximum_step_rad) {
        return Reject("step_limit", "consecutive joint targets exceed the maximum step");
      }
    }
    previous = target;
  }

  return {SafetyStatus::kAccepted, "ok", "action passed structural safety validation"};
}

}  // namespace so101::runtime
