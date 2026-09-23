import sys
import unittest
from pathlib import Path

PACKAGE_SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

try:
    import mujoco  # noqa: F401
except ImportError:
    mujoco = None


@unittest.skipIf(mujoco is None, "MuJoCo dependencies are not installed")
class RolloutTests(unittest.TestCase):
    def test_oracle_evaluation_reports_all_stages(self) -> None:
        from so101_mujoco import MujocoConfig, evaluate_oracle

        summary = evaluate_oracle(
            list(range(2000, 2005)),
            MujocoConfig(split="validation", max_steps=400),
        )
        self.assertEqual(summary.episodes, 5)
        self.assertEqual(summary.success_rate, 1.0)
        self.assertEqual(summary.retrieve_rate, 1.0)
        self.assertEqual(summary.mate_rate, 1.0)
        self.assertEqual(summary.inspect_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
