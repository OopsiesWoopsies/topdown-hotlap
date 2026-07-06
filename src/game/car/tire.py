import math
from collections.abc import Callable

import pyray as pr

from game.constants import PIXELS_PER_METER


def pacejka_model(
  B: float,
  C: float,
  D: float,
  E: float,
  angle_rad: float,
) -> float:
  """Uses the 5.2 magic formula for realistic tire physics.

  Args:
    B: The stiffness factor. Determines the slope of the curve at the origin.
    C: The shape factor. Defines the limits of the sine function (dictates the peak value).
    D: The peak factor. The maximum force (or whatever unit) the tire can generate.
    E: The curvature factor. Controls the curvature and location of the peak force relative to slip.
    angle: The slip angle in radians.

  Returns:
    float: A force (or whatever unit) the tires produces relative to the slip angle.
  """
  return D * math.sin(
    C * math.atan(B * angle_rad - E * (B * angle_rad - math.atan(B * angle_rad)))
  )


class Tire:
  def __init__(
    self,
    local_pos: pr.Vector2,
    width: float,
    mass: float,
    weight: float,
    local_coord: pr.Vector2,
    powered: bool,
  ):
    # Constants
    self.powered = powered
    self.local_pos = local_pos
    self.local_coord = local_coord
    self.radius = 0.35  # m
    self.width = width
    self.mass = mass  # kg
    self.weight = weight  # N
    self.mu = 1.9

    # Variables
    self.omega = 0.0  # Rad/s
    self.next_omega = 0.0  # Rad/s
    self.velo = pr.Vector2(0, 0)  # m/s
    self.inertia = mass * self.radius**2 / 2  # kg * m^2
    self.drive_t = 0.0  # Nm
    self.brake_t = 0.0  # Nm
    self.slip_ratio = 0.0
    self.slip_angle = 0.0  # Rad
    self.long_f = 0.0  # N
    self.lateral_f = 0.0  # N
    self.steer_rad = 0.0  # Rad

  def update_slip_ratio(self, dt: float):
    wheel_speed = self.omega * self.radius
    denom = max(abs(self.velo.x), 1.0)
    target_slip = (wheel_speed - self.velo.x) / denom
    dx = denom * dt
    blend = dx / (0.3 + dx)

    self.slip_ratio += (target_slip - self.slip_ratio) * blend

  def update_slip_angle(self):
    self.slip_angle = math.atan2(self.velo.y, self.velo.x)

  def update_lateral_force(self, max_force: float):
    self.lateral_f = -pacejka_model(10.3, 1.9, max_force, -0.7, self.slip_angle)

  def update_long_force(self, max_force: float):
    self.long_f = pacejka_model(8, 1.6, max_force, -0.5, self.slip_ratio)

  def update_omega(self, dt: float, car_speed: float, throttle: bool, brake: bool):
    net_torque = self.drive_t - self.brake_t - self.long_f * self.radius
    alpha = net_torque / self.inertia

    omega = self.omega
    if not throttle and car_speed < 0.1:
      next_omega = 0.0
    else:
      next_omega = omega + alpha * dt
    if brake and next_omega < 0:
      next_omega = 0

    self.next_omega = next_omega

  def get_local_force(self, max_force: float) -> pr.Vector2:
    fx = self.long_f
    fy = self.lateral_f

    req_force = math.sqrt(fx**2 + fy**2)
    if req_force > max_force:
      scale = max_force / req_force
      fx *= scale
      fy *= scale

    return pr.Vector2(
      fx * math.cos(self.steer_rad) - fy * math.sin(self.steer_rad),
      fx * math.sin(self.steer_rad) + fy * math.cos(self.steer_rad),
    )

  def update_position(
    self,
    vector2_operation: Callable[[pr.Vector2, pr.Vector2], pr.Vector2],
    axle_local_pos: pr.Vector2,
    right: float,
    track_width: float,
  ):
    self.local_pos = vector2_operation(
      axle_local_pos,
      pr.vector2_scale(right, track_width / 2 + self.width / 2),
    )

  def draw(self, angle_deg: float, steer_deg: float):
    local_pos_draw = pr.vector2_scale(self.local_pos, PIXELS_PER_METER)
    diameter_draw = self.radius * 2 * PIXELS_PER_METER
    width_draw = self.width * PIXELS_PER_METER

    rec = pr.Rectangle(local_pos_draw.x, local_pos_draw.y, diameter_draw, width_draw)
    origin = pr.Vector2(diameter_draw / 2, width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg + steer_deg, pr.BLUE)
