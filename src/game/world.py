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

    self.check_bounds()

  def check_bounds(self):
    for tire in self.tires:
      on_track = self.track.is_point_on_track(tire.render_pos)

