import torch

from ml.models.policy import PolicyNetwork

policy = PolicyNetwork()

observation = torch.zeros(16)
distribution = policy(observation)

action = distribution.sample()

print("Action:", action)
print("Action shape:", action.shape)
print("Log probability:", distribution.log_prob(action).sum())

assert action.shape == (3,)
assert torch.isfinite(action).all()
