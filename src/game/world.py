import pyray as pr

from game.car.car_body import Car
from input.control import Control


class World:
  def __init__(self):
    self.keyboard = Control()
    self.car = Car(pos=pr.Vector2(0, 0), angle_deg=180, size=pr.Vector2(5.2, 1.9))
    # timer, track, ghost, collision

  def update(self, dt):
    inputs = self.keyboard.get_inputs()
    steer = self.keyboard.get_steering()
    throttle = inputs.get("throttle")
    brake = inputs.get("brake")
    self.car.update(dt, throttle, brake, steer)
