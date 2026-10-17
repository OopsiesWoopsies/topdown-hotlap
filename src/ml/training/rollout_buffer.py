import numpy as np


class RolloutBuffer:
  def __init__(self):
    self.observations = []
    self.actions = []
    self.log_probs = []
    self.values = []
    self.rewards = []
    self.dones = []

  def add(self, observation, action, log_prob, value, reward, done):
    self.observations.append(observation.copy())
    self.actions.append(action.detach().cpu())
    self.log_probs.append(log_prob.detach().cpu())
    self.values.append(float(value))
    self.rewards.append(float(reward))
    self.dones.append(bool(done))

  def clear(self):
    self.observations.clear()
    self.actions.clear()
    self.log_probs.clear()
    self.values.clear()
    self.rewards.clear()
    self.dones.clear()

  def compute_returns_and_advantages(self, last_value, gamma=0.99, gae_lambda=0.95):
    advantages = np.zeros(len(self.rewards), dtype=np.float32)
    gae = 0.0

    for t in reversed(range(len(self.rewards))):
      if t == len(self.rewards) - 1:
        next_value = last_value
      else:
        next_value = self.values[t + 1]

      next_non_terminal = 1.0 - float(self.dones[t])
      delta = self.rewards[t] + gamma * next_value * next_non_terminal - self.values[t]
      gae = delta + gamma * gae_lambda * next_non_terminal * gae
      advantages[t] = gae

    returns = advantages + np.asarray(self.values, dtype=np.float32)

    return returns, advantages
