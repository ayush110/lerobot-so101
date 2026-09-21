import sys
from pathlib import Path
import unittest

PACKAGE_SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from so101_common import ActionChunk, Observation  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_valid_observation(self) -> None:
        observation = Observation(
            timestamp_ns=1,
            sequence=0,
            joint_positions_rad=(0.0, 0.1),
            gripper_position=0.5,
            calibration_version="test-v1",
        )
        self.assertEqual(observation.schema_version, 1)

    def test_action_rejects_nan(self) -> None:
        with self.assertRaises(ValueError):
            ActionChunk(
                created_at_ns=1,
                valid_until_ns=2,
                joint_targets_rad=((float("nan"),),),
                period_ns=1,
                confidence=1.0,
                source_model="test",
            )


if __name__ == "__main__":
    unittest.main()
