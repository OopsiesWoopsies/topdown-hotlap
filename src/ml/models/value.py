from torch import nn


class ValueNetwork(nn.Module):
  def __init__(self, obs_dim=16):
    super().__init__()

    self.network = nn.Sequential(
      nn.Linear(obs_dim, 128),
      nn.Tanh(),
      nn.Linear(128, 128),
      nn.Tanh(),
      nn.Linear(128, 1),
    )

  def forward(self, observation):
    return self.network(observation).squeeze(-1)
