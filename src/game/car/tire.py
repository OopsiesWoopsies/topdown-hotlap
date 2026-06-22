from collections.abc import Callable

import pyray as pr

from game.constants import PIXELS_PER_METER


class Tire:
  def __init__(self, pos: pr.Vector2, width: float, mass: float, weight: float):
    self.pos = pos
    self.grip = 2.0
    self.radius = 0.35  # m
    self.width = width
    self.mass = mass  # kg
    self.weight = weight  # N
    self.traction_stiffness = 3000

    self.omega = 0.0  # rad/s
    self.inertia = self.mass * self.radius**2 / 2  # kg * m^2
    self.slip_ratio = 0.0
    self.traction_f = 0.0

  def update_slip_ratio(self, long_velo: float):
    self.slip_ratio = (self.omega * self.radius - long_velo) / max(abs(long_velo), 1.0)

  def update_motorized_omega(
    self,
    dt: float,
    drive_torque: float,
    brake_torque: float,
    long_velo: float,
    throttle: bool,
  ):
    if not throttle and abs(long_velo) < 0.5:
      self.omega = 0.0
      return

    traction_t = self.traction_f * self.radius
    net_torque = drive_torque - traction_t - brake_torque
    new_omega = self.omega + net_torque / self.inertia * dt

    # Prevent brakes from instantly reversing wheel direction
    if self.omega > 0 and new_omega < 0:
      new_omega = 0.0

    elif self.omega < 0 and new_omega > 0:
      new_omega = 0.0

    self.omega = new_omega

  def update_reg_omega(self, long_velo: float, throttle: bool):
    if not throttle and abs(long_velo) < 0.5:
      self.omega = 0.0
    else:
      self.omega = long_velo / self.radius

  def update_traction_force(self, mu: float):
    traction_f = self.traction_stiffness * self.slip_ratio
    raw = mu * self.weight
    self.traction_f = pr.clamp(traction_f, -raw, raw)

  def get_traction_torque(self) -> float:
    return self.traction_f * self.radius

  def get_traction_force(self) -> float:
    return self.traction_f

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
