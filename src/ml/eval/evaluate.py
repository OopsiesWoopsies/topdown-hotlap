from pathlib import Path

import torch

from ml.environment.racing_env import RacingEnv
from ml.models.policy import PolicyNetwork


def evaluate():
  checkpoint_path = (
    Path(__file__).resolve().parents[1] / "models" / "racing_ppo_checkpoint.pt"
  )

  if not checkpoint_path.exists():
    raise FileNotFoundError(f"No checkpoint found at {checkpoint_path}")

  env = RacingEnv()
  policy = PolicyNetwork()

  checkpoint = torch.load(
    checkpoint_path,
    map_location="cpu",
    weights_only=True,
  )
  policy.load_state_dict(checkpoint["policy_state_dict"])
  policy.eval()

  observation, info = env.reset(seed=0)
  total_reward = 0.0
  steps = 0

  with torch.no_grad():
    while True:
      obs_tensor = torch.as_tensor(observation, dtype=torch.float32)

      # Use the policy's mean action instead of sampling.
      distribution = policy(obs_tensor)
      action = torch.tanh(distribution.mean).cpu().numpy()

      observation, reward, terminated, truncated, info = env.step(action)

      total_reward += reward
      steps += 1

      if terminated or truncated:
        break

  print(f"Evaluation steps: {steps}")
  print(f"Total reward: {total_reward:.2f}")
  print(f"Off track: {info['off_track']}")
  print(f"Final pos: {env.car.pos}")

  if "track_progress_pct" in info:
    print(f"Completed laps: {info['completed_laps']}")
    print(f"Track progress: {info['track_progress_pct']:.1f}%")
    print(f"Net progress: {info['net_progress_m']:.1f} m")

  env.close()


if __name__ == "__main__":
  evaluate()
