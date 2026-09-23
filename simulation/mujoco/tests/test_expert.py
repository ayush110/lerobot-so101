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
class ExpertTests(unittest.TestCase):
    def test_expert_completes_randomized_validation_scenes(self) -> None:
        from so101_mujoco import MujocoAssemblyExpert, MujocoConfig, So101AssemblyEnv

        env = So101AssemblyEnv(MujocoConfig(split="validation", max_steps=400))
        try:
            for seed in range(2000, 2005):
                env.reset(seed=seed)
                expert = MujocoAssemblyExpert(env)
                terminated = truncated = False
                info = {}
                while not (terminated or truncated):
                    _, _, terminated, truncated, info = env.step(expert.act())
                self.assertTrue(terminated, f"expert failed seed {seed}: {info}")
                self.assertTrue(info["mated"])
                self.assertFalse(info["grasped"])
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
