#include "so101/runtime/safety.hpp"
#include "so101/runtime/state_machine.hpp"

#include <cassert>
#include <limits>

using so101::runtime::ActionChunk;
using so101::runtime::Observation;
using so101::runtime::RuntimeState;
using so101::runtime::SafetyLimits;
using so101::runtime::SafetyStatus;
using so101::runtime::SafetyValidator;
using so101::runtime::StateMachine;

int main() {
  StateMachine machine;
  assert(machine.state() == RuntimeState::kDisarmed);
  assert(!machine.transition_to(RuntimeState::kExecuting));
  assert(machine.transition_to(RuntimeState::kHoming));
  assert(machine.transition_to(RuntimeState::kReady));
  assert(machine.transition_to(RuntimeState::kExecuting));
  machine.fault();
  assert(machine.state() == RuntimeState::kFault);

  const SafetyValidator validator(SafetyLimits{
      .joint_min_rad = {-1.0, -1.0},
      .joint_max_rad = {1.0, 1.0},
      .maximum_step_rad = 0.1,
      .maximum_chunk_steps = 4,
  });
  const Observation observation{
      .timestamp_ns = 1,
      .sequence = 0,
      .joint_positions_rad = {0.0, 0.0},
      .gripper_position = 0.0,
      .calibration_version = "test-v1",
  };
  ActionChunk action{
      .created_at_ns = 10,
      .valid_until_ns = 100,
      .period_ns = 10,
      .joint_targets_rad = {{0.05, -0.05}, {0.1, -0.1}},
      .confidence = 0.9F,
      .source_model = "test",
  };

  assert(validator.validate(observation, action, 20).status == SafetyStatus::kAccepted);
  action.joint_targets_rad = {{std::numeric_limits<double>::quiet_NaN(), 0.0}};
  assert(validator.validate(observation, action, 20).status == SafetyStatus::kRejected);
  action.joint_targets_rad = {{0.2, 0.0}};
  assert(validator.validate(observation, action, 20).reason_code == "step_limit");
  assert(validator.validate(observation, action, 101).reason_code == "stale_action");
  return 0;
}
