import sys
import unittest
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

PACKAGE_SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))


@unittest.skipIf(np is None, "NumPy optional dependency is not installed")
class SceneTests(unittest.TestCase):
    def test_splits_do_not_overlap(self) -> None:
        from so101_mujoco.scene import SPLIT_RANGES

        seeds = [set(range(low, high + 1)) for low, high in SPLIT_RANGES.values()]
        self.assertTrue(seeds[0].isdisjoint(seeds[1]))
        self.assertTrue(seeds[0].isdisjoint(seeds[2]))
        self.assertTrue(seeds[1].isdisjoint(seeds[2]))

    def test_scene_is_deterministic(self) -> None:
        from so101_mujoco.scene import sample_scene

        first = sample_scene(2000)
        second = sample_scene(2000)
        np.testing.assert_array_equal(first.part_a, second.part_a)
        np.testing.assert_array_equal(first.part_b, second.part_b)
        self.assertEqual(first.friction, second.friction)


if __name__ == "__main__":
    unittest.main()
