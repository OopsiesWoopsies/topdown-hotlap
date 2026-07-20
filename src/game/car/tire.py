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
    D: The peak factor. The maximum 'grip' the tire can provide.
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
    load: float,
    local_coord: pr.Vector2,
    powered: bool,
    lat_config: dict[str, float],
    long_config: dict[str, float],
  ):
    # Constants
    self.powered = powered
    self.local_pos = local_pos
    self.local_coord = local_coord
    self.radius = 0.35  # m
    self.width = width
    self.mass = mass  # kg
    self.lat_config = lat_config
    self.long_config = long_config

    # Variables
    self.load = load  # N
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
    self.max_lat_D = self.lat_config["pacejka"]["D"]
    self.max_long_D = self.long_config["pacejka"]["D"]

  def update_slip_ratio(self, dt: float):
    wheel_speed = self.omega * self.radius
    denom = max(abs(self.velo.x), 0.001)
    target_slip = (wheel_speed - self.velo.x) / denom
    dx = denom * dt
    blend = dx / (0.3 + dx)

    self.slip_ratio += (target_slip - self.slip_ratio) * blend
    if target_slip == 0.0:
      self.slip_ratio = 0.0

  def update_slip_angle(self):
    speed = pr.vector2_length(self.velo)
    if abs(self.velo.x) < 0.1:
      x_anchor = 0.1 if self.velo.x >= 0 else -0.1

      self.slip_angle = math.atan2(self.velo.y, x_anchor) * (speed / 0.1)
    else:
      self.slip_angle = math.atan2(self.velo.y, self.velo.x)

    right_ang = math.pi / 2

    if self.slip_angle > right_ang:
      self.slip_angle -= math.pi
      self.slip_angle *= -1
    elif self.slip_angle < -right_ang:
      self.slip_angle += math.pi
      self.slip_angle *= -1

  def update_lateral_force(self):
    B = self.lat_config["pacejka"]["B"]
    C = self.lat_config["pacejka"]["C"]
    D = self.lat_config["pacejka"]["D"]
    E = self.lat_config["pacejka"]["E"]
    f_nom = self.lat_config["load"]
    sens_lat = self.lat_config["sens"]

    load_ratio = self.load / max(f_nom, 1.0)
    D_lat_scaled = D * (1.0 / (1.0 + sens_lat * (load_ratio - 1.0)))
    self.max_lat_D = max(D_lat_scaled, 0.5 * D)

    self.lateral_f = (
      -pacejka_model(B, C, self.max_lat_D, E, self.slip_angle) * self.load
    )

  def update_long_force(self):
    B = self.long_config["pacejka"]["B"]
    C = self.long_config["pacejka"]["C"]
    D = self.long_config["pacejka"]["D"]
    E = self.long_config["pacejka"]["E"]
    f_nom = self.long_config["load"]
    sens_long = self.long_config["sens"]

    load_ratio = self.load / max(f_nom, 1.0)
    D_long_scaled = D * (1.0 - sens_long * (load_ratio - 1.0))
    self.max_long_D = max(D_long_scaled, 0.5 * D)

    self.long_f = pacejka_model(B, C, self.max_long_D, E, self.slip_ratio) * self.load

  def update_omega(self, dt: float, car_speed: float, throttle: bool, brake: bool):
    active_t = self.drive_t - self.long_f * self.radius
    max_brake_t = self.brake_t

    if abs(self.omega) > 0.01:
      applied_brake = math.copysign(max_brake_t, self.omega)
      net_torque = active_t - applied_brake
      alpha = net_torque / self.inertia
      next_omega = self.omega + alpha * dt

      if (
        math.copysign(1, self.omega) != math.copysign(1, next_omega) and next_omega != 0
      ):
        next_omega = 0.0
    else:
      if abs(active_t) <= max_brake_t:
        next_omega = 0.0
      else:
        remaining_t = active_t - math.copysign(max_brake_t, active_t)
        alpha = remaining_t / self.inertia
        next_omega = self.omega + alpha * dt

    if not throttle and not brake and car_speed < 0.1:
      next_omega = 0.0

    self.next_omega = next_omega

  def get_local_force(self) -> pr.Vector2:
    fx = self.long_f
    fy = self.lateral_f

    SHxa = 0.0
    bxa = 1.2
    cxa = 1.0

    SHyk = 0.0
    byk = 1.1
    cyk = 1.0

    gx = math.cos(cxa * math.atan(bxa * (abs(self.slip_angle) + SHxa))) / math.cos(
      cxa * math.atan(bxa * SHxa)
    )
    gy = math.cos(cyk * math.atan(byk * (abs(self.slip_ratio) + SHyk))) / math.cos(
      cyk * math.atan(byk * SHyk)
    )

    fx *= gx
    fy *= gy

    self.long_f = fx
    self.lateral_f = fy

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
