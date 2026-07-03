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
  ):
    self.local_pos = local_pos
    self.local_coord = local_coord
    self.radius = 0.35  # m
    self.width = width
    self.mass = mass  # kg
    self.weight = weight  # N
    self.mu = 1.9

    self.omega = 0.0  # Rad/s
    self.traction_ratio = 0.0
    self.brake_ratio = 0.0
    self.slip_angle = 0.0  # Rad
    self.traction_f = 0.0  # N
    self.brake_f = 0.0  # N
    self.lateral_f = 0.0  # N
    self.steer_rad = 0.0  # Rad

  def update_slip_angle(self, tire_velo: pr.Vector2):
    self.slip_angle = math.atan2(tire_velo.y, tire_velo.x)

  def update_lateral_force(self, max_force: float):
    self.lateral_f = -pacejka_model(10.3, 1.9, max_force, -0.7, self.slip_angle)

  def update_traction_ratio(self, torque: float, max_force: float):
    desired_f = torque / self.radius
    traction_ratio = desired_f / max_force
    self.traction_ratio = pr.clamp(traction_ratio, -2.0, 2.0)

  def update_brake_ratio(self, torque: float, max_force: float):
    desired_f = torque / self.radius
    brake_ratio = desired_f / max_force
    self.brake_ratio = pr.clamp(brake_ratio, -2.0, 2.0)

  def update_traction_force(self, max_force: float):
    self.traction_f = max_force * math.tanh(1.8 * self.traction_ratio)

  def update_brake_force(self, max_force: float):
    self.brake_f = max_force * math.tanh(1.0 * self.brake_ratio)

  def update_steer_rad(self, steer_rad: float):
    self.steer_rad = steer_rad

  def get_local_force(self, max_force: float) -> pr.Vector2:
    fx = self.traction_f - self.brake_f
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
