#include "so101/runtime/state_machine.hpp"

namespace so101::runtime {

bool StateMachine::transition_to(const RuntimeState requested) noexcept {
  if (requested == state_) {
    return true;
  }

  const bool allowed = [&] {
    switch (state_) {
      case RuntimeState::kDisarmed:
        return requested == RuntimeState::kHoming;
      case RuntimeState::kHoming:
        return requested == RuntimeState::kReady || requested == RuntimeState::kFault;
      case RuntimeState::kReady:
        return requested == RuntimeState::kExecuting || requested == RuntimeState::kDisarmed ||
               requested == RuntimeState::kFault;
      case RuntimeState::kExecuting:
        return requested == RuntimeState::kReady || requested == RuntimeState::kPaused ||
               requested == RuntimeState::kFault;
      case RuntimeState::kPaused:
        return requested == RuntimeState::kReady || requested == RuntimeState::kRecovery ||
               requested == RuntimeState::kDisarmed || requested == RuntimeState::kFault;
      case RuntimeState::kFault:
        return requested == RuntimeState::kRecovery || requested == RuntimeState::kDisarmed;
      case RuntimeState::kRecovery:
        return requested == RuntimeState::kReady || requested == RuntimeState::kPaused ||
               requested == RuntimeState::kFault;
    }
    return false;
  }();

  if (allowed) {
    state_ = requested;
  }
  return allowed;
}

}  // namespace so101::runtime
