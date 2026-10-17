import numpy as np
import torch

from ml.environment.racing_env import RacingEnv
from ml.models.policy import PolicyNetwork, select_action
from ml.models.value import ValueNetwork
from ml.training.rollout_buffer import RolloutBuffer
from ml.training.train import ppo_update

env = RacingEnv()
policy = PolicyNetwork()
buffer = RolloutBuffer()
value_network = ValueNetwork()

observation, info = env.reset()

for _ in range(10):
  action, raw_action, log_prob = select_action(policy, observation)

  assert action.shape == (3,)
  assert np.all(action >= -1.0) and np.all(action <= 1.0)

  with torch.no_grad():
    value = value_network(torch.as_tensor(observation, dtype=torch.float32)).item()

  next_observation, reward, terminated, truncated, info = env.step(action)

  buffer.add(
    observation,
    raw_action,
    log_prob,
    value,
    reward,
    terminated or truncated,
  )

  observation = next_observation

  if terminated or truncated:
    observation, info = env.reset()

# Test returns and advantages
with torch.no_grad():
  last_value = value_network(torch.as_tensor(observation, dtype=torch.float32)).item()

returns, advantages = buffer.compute_returns_and_advantages(last_value)

print("Returns shape:", returns.shape)
print("Advantages shape:", advantages.shape)
print("Returns finite:", np.isfinite(returns).all())
print("Advantages finite:", np.isfinite(advantages).all())

assert returns.shape == (10,)
assert advantages.shape == (10,)
assert np.isfinite(returns).all()
assert np.isfinite(advantages).all()

# Test policy and value loss + entropy
observations = torch.as_tensor(np.asarray(buffer.observations), dtype=torch.float32)
raw_actions = torch.stack(buffer.actions).float()
old_log_probs = torch.stack(buffer.log_probs).float()

returns_tensor = torch.as_tensor(returns, dtype=torch.float32)
advantages_tensor = torch.as_tensor(advantages, dtype=torch.float32)

policy_optimizer = torch.optim.Adam(policy.parameters(), lr=3e-4)
value_optimizer = torch.optim.Adam(value_network.parameters(), lr=1e-3)

policy_loss, value_loss, entropy = ppo_update(
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

print("Updated policy loss:", policy_loss)
print("Updated value loss:", value_loss)
print("Updated entropy:", entropy)
print("PPO update completed.")

# Print looped tests
print("Stored experiences:", len(buffer.observations))
print("Observation shape:", buffer.observations[0].shape)
print("Raw action shape:", buffer.actions[0].shape)
print("First reward:", buffer.rewards[0])

print("Stored values:", len(buffer.values))
print("First value:", buffer.values[0])

assert len(buffer.values) == 10
assert all(np.isfinite(v) for v in buffer.values)

env.close()
