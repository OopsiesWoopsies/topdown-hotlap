import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as nn_func

from ml.environment.racing_env import RacingEnv
from ml.models.policy import PolicyNetwork, select_action
from ml.models.value import ValueNetwork
from ml.training.rollout_buffer import RolloutBuffer


def compute_ppo_losses(
  policy,
  value_network,
  observations,
  raw_actions,
  old_log_probs,
  returns,
  advantages,
  clip_epsilon=0.2,
):
  advantages = (advantages - advantages.mean()) / (
    advantages.std(unbiased=False) + 1e-8
  )

  distribution = policy(observations)
  new_log_probs = distribution.log_prob(raw_actions).sum(dim=-1)
  log_ratio = new_log_probs - old_log_probs
  ratios = torch.exp(log_ratio)

  unclipped = ratios * advantages
  clipped = (
    torch.clamp(
      ratios,
      1.0 - clip_epsilon,
      1.0 + clip_epsilon,
    )
    * advantages
  )

  policy_loss = -torch.minimum(unclipped, clipped).mean()
  predicted_values = value_network(observations)
  value_loss = nn_func.mse_loss(predicted_values, returns)
  entropy = distribution.entropy().sum(dim=-1).mean()

  approx_kl = ((ratios - 1.0) - log_ratio).mean()
  clip_fraction = ((ratios - 1.0).abs() > clip_epsilon).float().mean()

  return policy_loss, value_loss, entropy, approx_kl, clip_fraction


def ppo_update(
  policy,
  value_network,
  policy_optimizer,
  value_optimizer,
  observations,
  raw_actions,
  old_log_probs,
  returns,
  advantages,
  value_coef=0.5,
  entropy_coef=0.01,
):
  policy_optimizer.zero_grad()
  value_optimizer.zero_grad()

  (
    policy_loss,
    value_loss,
    entropy,
    approx_kl,
    clip_fraction,
  ) = compute_ppo_losses(
    policy,
    value_network,
    observations,
    raw_actions,
    old_log_probs,
    returns,
    advantages,
  )

  total_loss = policy_loss + value_coef * value_loss - entropy_coef * entropy

  total_loss.backward()

  policy_optimizer.step()
  value_optimizer.step()

  return (
    policy_loss.item(),
    value_loss.item(),
    entropy.item(),
    approx_kl.item(),
    clip_fraction.item(),
  )


def train(
  total_timesteps=100_000,
  rollout_size=1024,
  update_epochs=4,
  new=False,
):
  env = RacingEnv()

  policy = PolicyNetwork()
  value_network = ValueNetwork()

  policy_optimizer = torch.optim.Adam(policy.parameters(), lr=3e-4)
  value_optimizer = torch.optim.Adam(value_network.parameters(), lr=1e-3)

  checkpoint_path = (
    Path(__file__).resolve().parents[1] / "models" / "racing_ppo_checkpoint.pt"
  )
  checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
  total_steps = 0

  if not new:
    if not checkpoint_path.exists():
      raise FileNotFoundError(
        f"Cannot resume: checkpoint not found at {checkpoint_path}"
      )

    checkpoint = torch.load(
      checkpoint_path,
      map_location="cpu",
      weights_only=True,
    )

    policy.load_state_dict(checkpoint["policy_state_dict"])
    value_network.load_state_dict(checkpoint["value_state_dict"])
    policy_optimizer.load_state_dict(checkpoint["policy_optimizer_state_dict"])
    value_optimizer.load_state_dict(checkpoint["value_optimizer_state_dict"])

    total_steps = checkpoint["total_steps"]
    print(f"Resuming from checkpoint at step {total_steps}")
  else:
    print("Starting training from scratch")

  observation, info = env.reset()
  steps_this_run = 0
  episode_reward = 0.0
  episode_length = 0
  episode_rewards = []

  while steps_this_run < total_timesteps:
    buffer = RolloutBuffer()
    steps_this_rollout = min(rollout_size, total_timesteps - steps_this_run)

    # Collect experiences using the current policy.
    for _ in range(steps_this_rollout):
      action, raw_action, log_prob = select_action(policy, observation)

      with torch.no_grad():
        value = value_network(torch.as_tensor(observation, dtype=torch.float32)).item()

      next_observation, reward, terminated, truncated, info = env.step(action)

      done = terminated or truncated

      buffer.add(
        observation,
        raw_action,
        log_prob,
        value,
        reward,
        done,
      )

      total_steps += 1
      steps_this_run += 1
      episode_reward += reward
      episode_length += 1

      if done:
        episode_rewards.append(episode_reward)

        print(
          f"Episode ended | Steps: {total_steps} | Length: {episode_length} "
          f"| Reward: {episode_reward:.2f} "
          f"| Laps: {info['completed_laps']} "
          f"| Track progress: {info['track_progress_pct']:.1f}% "
          f"| Net progress: {info['net_progress_m']:.1f} m"
        )

        observation, info = env.reset()
        episode_reward = 0.0
        episode_length = 0
      else:
        observation = next_observation

    # Estimate the value after the final collected transition.
    with torch.no_grad():
      if buffer.dones[-1]:
        last_value = 0.0
      else:
        last_value = value_network(
          torch.as_tensor(observation, dtype=torch.float32)
        ).item()

    returns, advantages = buffer.compute_returns_and_advantages(last_value)

    # Convert the collected data into PyTorch batches.
    observations = torch.as_tensor(np.asarray(buffer.observations), dtype=torch.float32)
    raw_actions = torch.stack(buffer.actions).float()
    old_log_probs = torch.stack(buffer.log_probs).float()
    returns_tensor = torch.as_tensor(returns, dtype=torch.float32)
    advantages_tensor = torch.as_tensor(advantages, dtype=torch.float32)

    # Reuse the same rollout for several PPO optimization epochs.
    for _ in range(update_epochs):
      (
        policy_loss,
        value_loss,
        entropy,
        approx_kl,
        clip_fraction,
      ) = ppo_update(
        policy,
        value_network,
        policy_optimizer,
        value_optimizer,
        observations,
        raw_actions,
        old_log_probs,
        returns_tensor,
        advantages_tensor,
      )

    if not np.isfinite([policy_loss, value_loss, entropy]).all():
      raise RuntimeError("Non-finite PPO training metric detected")

    torch.save(
      {
        "policy_state_dict": policy.state_dict(),
        "value_state_dict": value_network.state_dict(),
        "policy_optimizer_state_dict": policy_optimizer.state_dict(),
        "value_optimizer_state_dict": value_optimizer.state_dict(),
        "total_steps": total_steps,
      },
      checkpoint_path,
    )

    print(f"Checkpoint saved: {checkpoint_path}")

    recent_rewards = episode_rewards[-10:]
    mean_reward = float(np.mean(recent_rewards)) if recent_rewards else float("nan")

    print(
      f"Steps: {total_steps} | "
      f"Mean episode reward (last 10): {mean_reward:.2f} | "
      f"Policy loss: {policy_loss:.4f} | "
      f"Value loss: {value_loss:.4f} | "
      f"Entropy: {entropy:.4f} | "
      f"Approx KL: {approx_kl:.5f} | "
      f"Clip fraction: {clip_fraction:.3f}"
    )

  env.close()
  return policy, value_network


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--total-timesteps",
    type=int,
    default=100_000,
  )
  parser.add_argument(
    "--rollout-size",
    type=int,
    default=1024,
  )
  parser.add_argument(
    "--update-epochs",
    type=int,
    default=4,
  )
  parser.add_argument(
    "--new",
    action="store_true",
    help="Reset everything and start from scratch",
  )

  args = parser.parse_args()

  train(
    total_timesteps=args.total_timesteps,
    rollout_size=args.rollout_size,
    update_epochs=args.update_epochs,
    new=args.new,
  )
