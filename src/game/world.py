from game.car.car_body import Car
from game.constants import Constants
from game.track.physics_track import PhysicsTrack
from game.track.timer import Timer
from input.control import Control


class World:
  def __init__(self, cons: Constants, ctrls: Control):
    self.controls = ctrls
    self.car = Car(cons, pos=(0.0, 0.0), angle_deg=180, size=(5.6, 2.0))
    self.track = PhysicsTrack()
    self.timer = Timer()

    self.inputs = ctrls.get_inputs(0)

  def update(self, dt):
    self.inputs = self.controls.get_inputs(dt)
    steer = self.controls.get_steering()
    sector = self.car.update(self.track, dt, self.inputs, steer)

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
