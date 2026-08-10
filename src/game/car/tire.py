import math
from collections.abc import Callable

import pyray as pr

from game.constants import PIXELS_PER_METER

RIGHT_ANGLE = math.pi / 2


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
    config: dict[str, any],
  ):
    # Constants
    self.powered = powered
    self.local_pos = local_pos
    self.prev_local_pos = local_pos
    self.local_coord = local_coord
    self.radius = 0.35  # m
    self.width = width  # m
    self.mass = mass  # kg
    self.config = config

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
    self.max_lat_D = self.config["lat"]["pacejka"]["D"]
    self.max_long_D = self.config["long"]["pacejka"]["D"]
    self.grip_usage = 0.0

  def update_slip_ratio(self):
    wheel_speed = self.omega * self.radius
    vehicle_speed = self.velo.x

    denom = max(
      abs(vehicle_speed),
      abs(wheel_speed),
      1.0,
    )

    self.slip_ratio = (wheel_speed - vehicle_speed) / denom

  def update_slip_angle(self):
    speed = pr.vector2_length(self.velo)
    if abs(self.velo.x) < 0.1:
      x_anchor = 0.1 if self.velo.x >= 0 else -0.1

      self.slip_angle = math.atan2(self.velo.y, x_anchor) * (speed / 0.1)
    else:
      self.slip_angle = math.atan2(self.velo.y, self.velo.x)

    if self.slip_angle > RIGHT_ANGLE:
      self.slip_angle -= math.pi
      self.slip_angle *= -1
    elif self.slip_angle < -RIGHT_ANGLE:
      self.slip_angle += math.pi
      self.slip_angle *= -1

  def update_lateral_force(self):
    lat_config = self.config["lat"]
    pacejka_config = lat_config["pacejka"]
    B = pacejka_config["B"]
    C = pacejka_config["C"]
    D = pacejka_config["D"]
    E = pacejka_config["E"]
    f_nom = lat_config["load"]
    sens_lat = lat_config["sens"]

    load_ratio = self.load / max(f_nom, 1.0)
    D_lat_scaled = D * (1.0 / (1.0 + sens_lat * (load_ratio - 1.0)))
    self.max_lat_D = max(D_lat_scaled, 0.5 * D)

    self.lateral_f = (
      -pacejka_model(B, C, self.max_lat_D, E, self.slip_angle) * self.load
    )

  def update_long_force(self):
    long_config = self.config["long"]
    pacejka_config = long_config["pacejka"]
    B = pacejka_config["B"]
    C = pacejka_config["C"]
    D = pacejka_config["D"]
    E = pacejka_config["E"]
    f_nom = long_config["load"]
    sens_long = long_config["sens"]

    load_ratio = self.load / max(f_nom, 1.0)
    D_long_scaled = D * (1.0 - sens_long * (load_ratio - 1.0))
    self.max_long_D = max(D_long_scaled, 0.5 * D)

    self.long_f = pacejka_model(B, C, self.max_long_D, E, self.slip_ratio) * self.load

  def update_omega(
    self, dt: float, car_speed: float, throttle: bool, brake: bool, added_inertia: float
  ):
    active_t = self.drive_t - self.long_f * self.radius
    total_inertia = self.inertia + added_inertia

    if abs(self.omega) < 0.1 and abs(active_t) <= self.brake_t:
      self.next_omega = 0.0
      return

    if abs(self.omega) > 0.1:
      brake_sign = math.copysign(1.0, self.omega)
    else:
      brake_sign = math.copysign(1.0, active_t)

    brake_torque = self.brake_t * brake_sign
    net_torque = active_t - brake_torque

    alpha = net_torque / total_inertia
    next_omega = self.omega + alpha * dt

    if self.omega * next_omega < 0.0:
      next_omega = 0.0

    if not throttle and not brake and car_speed < 0.1:
      next_omega = 0.0

    self.next_omega = next_omega

  def get_local_force(self) -> pr.Vector2:
    fx = self.long_f
    fy = self.lateral_f

    combined_slip_config = self.config["combined_slip"]

    SHxa = combined_slip_config["SHxa"]
    bxa = combined_slip_config["bxa"]
    cxa = combined_slip_config["cxa"]

    SHyk = combined_slip_config["SHyk"]
    byk = combined_slip_config["byk"]
    cyk = combined_slip_config["cyk"]

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

    self.grip_usage = (self.lateral_f / (self.max_lat_D * self.load)) ** 2 + (
      self.long_f / (self.max_long_D * self.load)
    ) ** 2

    return pr.Vector2(
      fx * math.cos(self.steer_rad) - fy * math.sin(self.steer_rad),
      fx * math.sin(self.steer_rad) + fy * math.cos(self.steer_rad),
    )

  def update_position(
    self,
    vector2_op: Callable[[pr.Vector2, pr.Vector2], pr.Vector2],
    axle_local_pos: pr.Vector2,
    right: float,
    track_width: float,
  ):
    self.local_pos = vector2_op(
      axle_local_pos,
      pr.vector2_scale(right, track_width / 2 + self.width / 2),
    )

  def draw(
    self,
    vector2_op: Callable[[pr.Vector2, pr.Vector2], pr.Vector2],
    axle_render_pos: pr.Vector2,
    right: float,
    angle_deg: float,
    steer_deg: float,
    track_width: float,
  ):
    render_pos = vector2_op(
      axle_render_pos, pr.vector2_scale(right, track_width / 2 + self.width / 2)
    )

    local_pos_draw = pr.vector2_scale(render_pos, PIXELS_PER_METER)
    diameter_draw = self.radius * 2 * PIXELS_PER_METER
    width_draw = self.width * PIXELS_PER_METER

    rec = pr.Rectangle(local_pos_draw.x, local_pos_draw.y, diameter_draw, width_draw)
    origin = pr.Vector2(diameter_draw / 2, width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg + steer_deg, pr.BLUE)
