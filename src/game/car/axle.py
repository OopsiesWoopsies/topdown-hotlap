import math

import pyray as pr

from game.car.tire import Tire
from game.constants import PIXELS_PER_METER


class Axle:
  def __init__(
    self,
    local_pos: pr.Vector2,
    distance_to_center: float,
    distance_to_cg: float,
    track_width: float,
    angle_rad: float,
    tire_width: float,
    tire_mass: float,
    tire_load: float,
    powered: bool,
    lat_pacejka_consts: dict[str, float],
    long_pacejka_consts: dict[str, float],
  ):
    self.local_pos = local_pos
    self.distance_to_center = distance_to_center
    self.track_width = track_width
    self.axle_width = 0.05

    right = pr.Vector2(-math.sin(angle_rad), math.cos(angle_rad))

    left_tire_pos = pr.vector2_subtract(
      self.local_pos, pr.vector2_scale(right, self.track_width / 2)
    )
    right_tire_pos = pr.vector2_add(
      self.local_pos, pr.vector2_scale(right, self.track_width / 2)
    )
    self.left_tire = Tire(
      left_tire_pos,
      tire_width,
      tire_mass,
      tire_load,
      pr.Vector2(distance_to_cg, track_width / 2),
      powered,
      lat_pacejka_consts,
      long_pacejka_consts,
    )
    self.right_tire = Tire(
      right_tire_pos,
      tire_width,
      tire_mass,
      tire_load,
      pr.Vector2(distance_to_cg, -track_width / 2),
      powered,
      lat_pacejka_consts,
      long_pacejka_consts,
    )

  def get_load(self) -> float:
    return self.left_tire.load + self.right_tire.load

  def update_position(self, car_pos: pr.Vector2, forward: float, right: float):
    self.local_pos = pr.vector2_add(
      car_pos, pr.vector2_scale(forward, self.distance_to_center)
    )

    self.left_tire.update_position(
      pr.vector2_subtract, self.local_pos, right, self.track_width
    )
    self.right_tire.update_position(
      pr.vector2_add, self.local_pos, right, self.track_width
    )

  def draw(self, angle_deg: float, steer_deg: float):
    pos_draw = pr.vector2_scale(self.local_pos, PIXELS_PER_METER)
    axle_width_draw = self.axle_width * PIXELS_PER_METER
    track_width_draw = self.track_width * PIXELS_PER_METER

    rec = pr.Rectangle(pos_draw.x, pos_draw.y, axle_width_draw, track_width_draw)
    origin = pr.Vector2(axle_width_draw / 2, track_width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg, pr.BLACK)

    self.left_tire.draw(angle_deg, steer_deg)
    self.right_tire.draw(angle_deg, steer_deg)
