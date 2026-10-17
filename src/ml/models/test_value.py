import torch

from ml.models.value import ValueNetwork

value_network = ValueNetwork()

# Test one observation.
observation = torch.zeros(16)
value = value_network(observation)

print("Value:", value.item())
print("Value shape:", value.shape)

assert value.shape == torch.Size([])
assert torch.isfinite(value)

# Test a batch of observations.
observations = torch.zeros(8, 16)
values = value_network(observations)

print("Batch value shape:", values.shape)

assert values.shape == (8,)
assert torch.isfinite(values).all()
