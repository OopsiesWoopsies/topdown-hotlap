import math

import pyray as pr

from game.car.car_body import Car
from game.constants import PIXELS_PER_METER
from game.track.timer import Timer
from game.track.track import Track
from input.control import Control


class World:
  def __init__(self):
    self.controls = Control()
    self.car = Car(pos=pr.Vector2(0, 0), angle_deg=180, size=pr.Vector2(5.2, 1.9))
    self.track = Track()
    self.timer = Timer()

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

    for tire in self.tires:
      sector = self.track.check_sectors(tire.prev_local_pos, tire.local_pos)
      if sector != -1:
        break

    if not self.check_bounds(dt) and not self.timer.lap_timer_stopped:
      self.timer.stop_lap_timer()
      self.track.stop_lap()
    if not self.track.start_lap:
      return
    if sector == 0:
      self.timer.start_lap_timer()
    elif sector == 2 or sector == 3:
      self.timer.set_sector_time(sector - 1)
    elif sector == 1:
      self.timer.set_sector_time(sector - 1)
      self.timer.set_lap_time()

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
      for corner in tire.outer_corners:
        render_corner = pr.vector2_scale(corner, PIXELS_PER_METER)
        on_track = self.track.is_point_on_track(render_corner, index_offset)
        if on_track:
          return True
    return False
