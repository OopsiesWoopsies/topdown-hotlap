import numpy as np
import torch
from torch import nn
from torch.distributions import Normal


class PolicyNetwork(nn.Module):
  def __init__(self, obs_dim=16, action_dim=3):
    super().__init__()

    self.network = nn.Sequential(
      nn.Linear(obs_dim, 128),
      nn.Tanh(),
      nn.Linear(128, 128),
      nn.Tanh(),
    )

    self.mean_layer = nn.Linear(128, action_dim)
    self.log_std = nn.Parameter(torch.zeros(action_dim))

  def forward(self, observation):
    features = self.network(observation)

    mean = self.mean_layer(features)

    std = torch.exp(self.log_std)

    return Normal(mean, std)


@torch.no_grad()
def select_action(policy, observation):
  observation = torch.as_tensor(observation, dtype=torch.float32)
  distribution = policy(observation)
  raw_action = distribution.sample()

  action = torch.tanh(raw_action)
  log_prob = distribution.log_prob(raw_action).sum()

  return (
    action.cpu().numpy().astype(np.float32),
    raw_action,
    log_prob,
  )
