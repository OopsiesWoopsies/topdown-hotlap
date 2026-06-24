import math
from collections.abc import Callable

import pyray as pr

from game.constants import PIXELS_PER_METER


class Tire:
  def __init__(self, pos: pr.Vector2, width: float, mass: float, weight: float):
    self.pos = pos
    self.radius = 0.35  # m
    self.width = width
    self.mass = mass  # kg
    self.weight = weight  # N
    self.mu = 1.9

    self.omega = 0.0  # Rad/s
    self.traction_ratio = 0.0
    self.brake_ratio = 0.0
    self.traction_f = 0.0

  def update_traction_ratio(self, torque: float):
    desired_f = torque / self.radius
    max_force = self.mu * self.weight
    traction_ratio = desired_f / max_force
    self.traction_ratio = pr.clamp(traction_ratio, -2.0, 2.0)

  def update_brake_ratio(self, torque: float):
    desired_f = torque / self.radius
    max_force = self.mu * self.weight
    brake_ratio = desired_f / max_force
    self.brake_ratio = pr.clamp(brake_ratio, -2.0, 2.0)

  def update_traction_force(self):
    self.traction_f = self.mu * self.weight * math.tanh(1.8 * self.traction_ratio)

  def get_traction_force(self) -> float:
    return self.traction_f

  def get_brake_force(self) -> float:
    return self.mu * self.weight * math.tanh(1.0 * self.brake_ratio)

  def update_position(
    self,
    vector2_operation: Callable[[pr.Vector2, pr.Vector2], pr.Vector2],
    axle_pos: pr.Vector2,
    right: float,
    track_width: float,
  ):
    self.pos = vector2_operation(
      axle_pos,
      pr.vector2_scale(right, track_width / 2 + self.width / 2),
    )

  def draw(self, angle_deg: float):
    pos_draw = pr.vector2_scale(self.pos, PIXELS_PER_METER)
    diameter_draw = self.radius * 2 * PIXELS_PER_METER
    width_draw = self.width * PIXELS_PER_METER

    rec = pr.Rectangle(pos_draw.x, pos_draw.y, diameter_draw, width_draw)
    origin = pr.Vector2(diameter_draw / 2, width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg, pr.BLUE)
