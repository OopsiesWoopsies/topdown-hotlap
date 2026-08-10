import pyray as pr

from game.car.car_body import Car
from game.track.track import Track
from input.control import Control


class World:
  def __init__(self):
    self.controls = Control()
    self.car = Car(pos=pr.Vector2(0, 0), angle_deg=180, size=pr.Vector2(5.2, 1.9))
    self.track = Track()
    # timer, track, ghost, collision

  def update(self, dt):
    inputs = self.controls.get_inputs(dt)
    steer = self.controls.get_steering()
    self.car.update(dt, inputs, steer)
