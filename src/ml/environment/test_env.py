import numpy as np
from gymnasium.utils.env_checker import check_env

from ml.environment.racing_env import RacingEnv

env = RacingEnv()

# Check Gymnasium's environment API and observation/action spaces.
check_env(env, skip_render_check=True)
print("Gymnasium environment checks passed.")

obs, info = env.reset()

for i in range(40):
  action = np.array([0.0, 1.0, 0.0], dtype=np.float32)
  obs, reward, terminated, truncated, info = env.step(action)

  if i % 5 == 0:
    print(
      f"t={(i + 1) * env.action_interval:.2f}s, "
      f"speed={env.car.speed:.6f}, "
      f"throttle={env.throttle_amt:.2f}, "
      f"reward={reward:.4f}"
    )

  if terminated or truncated:
    print("Episode ended.")
    break

env.close()
