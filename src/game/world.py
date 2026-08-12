import math

import pyray as pr

from game.car.car_body import Car
from game.track.track import Track
from input.control import Control


class World:
  def __init__(self):
    self.controls = Control()
    self.car = Car(pos=pr.Vector2(0, 0), angle_deg=180, size=pr.Vector2(5.2, 1.9))
    self.track = Track()

    self.tires = [
      self.car.rear_axle.left_tire,
      self.car.rear_axle.right_tire,
      self.car.front_axle.left_tire,
      self.car.front_axle.right_tire,
    ]
    # timer, track, ghost, collision

  def update(self, dt):
    inputs = self.controls.get_inputs(dt)
    steer = self.controls.get_steering()
    self.car.update(dt, inputs, steer)

    self.check_bounds(dt)

  def check_bounds(self, dt: float) -> bool:
    """Checks if tires are within track boundaries (white lines).

    Args:
      dt: Delta time. Used to calculate the index offset.

    Returns:
      bool: All four wheels are off track returns false
    """
    margin = 2
    index_offset = math.ceil(self.car.speed / self.track.mpp * dt) + margin

    for tire in self.tires:
      on_track = self.track.is_point_on_track(tire.render_pos, index_offset)
      if on_track:
        return True

    return False
