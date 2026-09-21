#pragma once

#include "so101/runtime/types.hpp"

namespace so101::runtime {

class StateMachine {
 public:
  [[nodiscard]] RuntimeState state() const noexcept { return state_; }
  [[nodiscard]] bool transition_to(RuntimeState requested) noexcept;
  void fault() noexcept { state_ = RuntimeState::kFault; }

 private:
  RuntimeState state_{RuntimeState::kDisarmed};
};

}  // namespace so101::runtime
