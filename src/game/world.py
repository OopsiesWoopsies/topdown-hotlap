import pyray as pr

from game.car.car_body import Car
from game.track.timer import Timer
from game.track.track import Track
from input.control import Control


class World:
  def __init__(self):
    self.controls = Control()
    self.car = Car(pos=(0.0, 0.0), angle_deg=180, size=(5.2, 1.9))
    self.track = Track()
    self.timer = Timer()

  def update(self, dt):
    inputs = self.controls.get_inputs(dt)
    steer = self.controls.get_steering()
    sector = self.car.update(self.track, dt, inputs, steer)

    if self.car.off_track and not self.timer.lap_timer_stopped:
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
