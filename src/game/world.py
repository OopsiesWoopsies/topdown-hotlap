import pyray as pr

from game.car import Car
from input.keyboard import Keyboard


class World:
  def __init__(self):
    self.keyboard = Keyboard()
    self.car = Car(
      pos=pr.Vector2(10, 10), angle_deg=180, size=pr.Vector2(30, 60)
    )
    # timer, track, ghost, collision

  def update(self, dt):
    inputs = self.keyboard.get_inputs()
    steer = self.keyboard.get_steering()
    throttle = inputs.get("throttle")
    brake = inputs.get("brake")
    self.car.update(throttle, brake, steer, dt)
