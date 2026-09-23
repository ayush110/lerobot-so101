import sys
import unittest
from pathlib import Path

PACKAGE_SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

try:
    import gymnasium  # noqa: F401
    import mujoco  # noqa: F401
    import numpy as np
except ImportError:
    gymnasium = None
    mujoco = None
    np = None


@unittest.skipIf(mujoco is None or gymnasium is None, "MuJoCo dependencies are not installed")
class EnvironmentTests(unittest.TestCase):
    def test_model_reset_and_step_contract(self) -> None:
        from so101_mujoco import JOINT_NAMES, So101AssemblyEnv

        env = So101AssemblyEnv()
        try:
            self.assertEqual(env.model.nu, 6)
            self.assertEqual(tuple(env.model.joint(i).name for i in range(6)), JOINT_NAMES)
            observation, info = env.reset(seed=2000)
            self.assertEqual(info["backend"], "mujoco")
            self.assertEqual(observation["state"].shape, (19,))
            result = env.step(np.zeros(6, dtype=np.float32))
            self.assertEqual(len(result), 5)
            self.assertTrue(np.isfinite(result[0]["state"]).all())
        finally:
            env.close()

    def test_vector_entrypoint(self) -> None:
        from so101_mujoco import make_env

        env = make_env(n_envs=2, cfg={"split": "validation", "max_steps": 2})
        try:
            observation, _ = env.reset(seed=[2000, 2001])
            self.assertEqual(observation["state"].shape, (2, 19))
        finally:
            env.close()

    def test_rejects_malformed_action(self) -> None:
        from so101_mujoco import So101AssemblyEnv

        env = So101AssemblyEnv()
        try:
            env.reset(seed=2000)
            with self.assertRaises(ValueError):
                env.step(np.zeros(5, dtype=np.float32))
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
