import math

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
    local_pos: tuple[float, float],
    width: float,
    radius: float,
    mass: float,
    load: float,
    local_coord: tuple[float, float],
    outer_corners: list[tuple[float, float]],
    powered: bool,
    config: dict[str, any],
  ):
    # Constants
    self.powered = powered
    self.local_pos = local_pos
    self.prev_local_pos = local_pos
    self.render_pos = local_pos
    self.local_coord = local_coord

    self.radius = radius  # m
    self.width = width  # m
    self.half_width = width / 2  # m
    self.mass = mass  # kg

    self.config = config
    self.f_nom = config["load"]
    self.max_lat_D = self.config["lat"]["pacejka"]["D"]
    self.max_long_D = self.config["long"]["pacejka"]["D"]

    self.sa_relaxation = 0.15
    self.sr_relaxation = 0.1

    # Variables
    self.load = load  # N
    self.omega = 0.0  # Rad/s
    self.next_omega = 0.0  # Rad/s
    self.velo = (0.0, 0.0)  # m/s
    self.inertia = mass * self.radius**2 / 2  # kg * m^2

    self.drive_t = 0.0  # Nm
    self.brake_t = 0.0  # Nm

    self.slip_ratio = 0.0
    self.slip_angle = 0.0  # Rad
    self.long_f = 0.0  # N
    self.lateral_f = 0.0  # N
    self.steer_rad = 0.0  # Rad
    self.grip_usage = 0.0
    self.surface_multi = 1.0

    self.outer_corners = outer_corners
    self.track_indices = [0, 0]

  def update_outer_corners(
    self,
    sign: int,
    angle_rad: float,
    steer_rad: float,
  ):
    forward = (math.cos(angle_rad + steer_rad), math.sin(angle_rad + steer_rad))
    right = (-math.sin(angle_rad + steer_rad), math.cos(angle_rad + steer_rad))
    forward_offset = (forward[0] * self.radius, forward[1] * self.radius)
    right_offset = (right[0] * self.width / 2, right[1] * self.width / 2)
    self.outer_corners = [
      (
        self.local_pos[0] + forward_offset[0] + right_offset[0] * sign,
        self.local_pos[1] + forward_offset[1] + right_offset[1] * sign,
      ),
      (
        self.local_pos[0] - forward_offset[0] + right_offset[0] * sign,
        self.local_pos[1] - forward_offset[1] + right_offset[1] * sign,
      ),
    ]

  def update_slip_ratio(self, dt: float):
    wheel_speed = self.omega * self.radius
    vehicle_speed = self.velo[0]

    denom = max(
      abs(vehicle_speed),
      abs(wheel_speed),
      1.0,
    )

    target_sr = (wheel_speed - vehicle_speed) / denom
    roll_speed = max(abs(vehicle_speed), 0.5)
    alpha_factor = math.exp(-(roll_speed * dt) / self.sr_relaxation)

    self.slip_ratio = target_sr + (self.slip_ratio - target_sr) * alpha_factor

  def update_slip_angle(self, dt: float):
    velo_x, velo_y = self.velo
    speed = (velo_x**2 + velo_y**2) ** 0.5
    if abs(velo_x) < 0.1:
      x_anchor = 0.1 if velo_x >= 0 else -0.1

      target_sa = math.atan2(velo_y, x_anchor) * (speed / 0.1)
    else:
      target_sa = math.atan2(velo_y, velo_x)

    if target_sa > RIGHT_ANGLE:
      target_sa -= math.pi
      target_sa *= -1
    elif target_sa < -RIGHT_ANGLE:
      target_sa += math.pi
      target_sa *= -1

    roll_speed = max(abs(velo_x), 0.5)
    alpha_factor = math.exp(-(roll_speed * dt) / self.sa_relaxation)

    self.slip_angle = target_sa + (self.slip_angle - target_sa) * alpha_factor

  def update_lateral_force(self):
    lat_config = self.config["lat"]
    pacejka_config = lat_config["pacejka"]
    B = pacejka_config["B"]
    C = pacejka_config["C"]
    D = pacejka_config["D"]
    E = pacejka_config["E"]
    sens = lat_config["sens"]
    sens_D = sens["D"]
    sens_B = sens["B"]

    load_ratio = self.load / self.f_nom
    D_lat_scaled = (
      D * (1.0 / (1.0 + sens_D * (load_ratio - 1.0)))
    ) * self.surface_multi
    self.max_lat_D = max(D_lat_scaled, 0.65 * D)

    B_lat_scaled = (
      max(B * (1.0 / (1.0 + sens_B * (load_ratio - 1.0))), 0.5 * B)
    ) * self.surface_multi**0.5

    self.lateral_f = (
      -pacejka_model(B_lat_scaled, C, self.max_lat_D, E, self.slip_angle) * self.load
    )

  def update_long_force(self):
    long_config = self.config["long"]
    pacejka_config = long_config["pacejka"]
    B = pacejka_config["B"]
    C = pacejka_config["C"]
    D = pacejka_config["D"]
    E = pacejka_config["E"]
    sens = long_config["sens"]
    sens_D = sens["D"]
    sens_B = sens["B"]

    load_ratio = self.load / self.f_nom
    D_long_scaled = D * (1.0 / (1.0 + sens_D * (load_ratio - 1.0)))
    self.max_long_D = max(D_long_scaled, 0.65 * D)

    B_long_scaled = max(B * (1.0 / (1.0 + sens_B * (load_ratio - 1.0))), 0.5 * B)

    self.long_f = (
      pacejka_model(B_long_scaled, C, self.max_long_D, E, self.slip_ratio) * self.load
    )

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

  def get_local_force(self) -> tuple[float, float]:
    if self.load <= 0.0:
      return (0.0, 0.0)

    fx = self.long_f
    fy = self.lateral_f

    combined_slip_config = self.config["combined_slip"]
    combined_slip_sens = combined_slip_config["sens"]
    load_ratio = self.load / self.f_nom

    SHxa = combined_slip_config["SHxa"]
    bxa = combined_slip_config["bxa"]
    cxa = combined_slip_config["cxa"]

    SHyk = combined_slip_config["SHyk"]
    byk = combined_slip_config["byk"]
    cyk = combined_slip_config["cyk"]

    sens_bxa = combined_slip_sens["bxa"]
    sens_byk = combined_slip_sens["byk"]

    bxa = bxa * (1.0 + sens_bxa * (load_ratio - 1.0))
    byk = byk * (1.0 + sens_byk * (load_ratio - 1.0))

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

    # Clamp at 100% grip usage
    if self.grip_usage > 1.0:
      ellipse_scale = 1.0 / math.sqrt(self.grip_usage)
      self.long_f *= ellipse_scale
      self.lateral_f *= ellipse_scale

      fx = self.long_f
      fy = self.lateral_f
      self.grip_usage = 1.0

    return fx * math.cos(self.steer_rad) - fy * math.sin(self.steer_rad), fx * math.sin(
      self.steer_rad
    ) + fy * math.cos(self.steer_rad)

  def update_position(
    self,
    sign: int,
    axle_local_pos: tuple[float, float],
    right: tuple[float, float],
    half_track_width: float,
  ):
    self.prev_local_pos = self.local_pos
    self.local_pos = (
      axle_local_pos[0] + right[0] * (half_track_width + self.half_width) * sign,
      axle_local_pos[1] + right[1] * (half_track_width + self.half_width) * sign,
    )

  def draw(
    self,
    sign: int,
    axle_render_pos: tuple[float, float],
    right: tuple[float, float],
    angle_deg: float,
    steer_deg: float,
    half_track_width: float,
  ):
    self.render_pos = (
      (axle_render_pos[0] + right[0] * (half_track_width + self.half_width) * sign)
      * PIXELS_PER_METER,
      (axle_render_pos[1] + right[1] * (half_track_width + self.half_width) * sign)
      * PIXELS_PER_METER,
    )

    diameter_draw = self.radius * 2 * PIXELS_PER_METER
    width_draw = self.width * PIXELS_PER_METER

    rec = pr.Rectangle(
      self.render_pos[0], self.render_pos[1], diameter_draw, width_draw
    )
    origin = (diameter_draw / 2, width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg + steer_deg, pr.BLUE)
    pr.draw_circle_v(
      pr.vector2_scale(self.outer_corners[0], PIXELS_PER_METER), 2, pr.PURPLE
    )
    pr.draw_circle_v(
      pr.vector2_scale(self.outer_corners[1], PIXELS_PER_METER), 2, pr.PURPLE
    )
