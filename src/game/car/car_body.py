import math

import pyray as pr

from game.car.axle import Axle
from game.car.engine.engine import Engine
from game.constants import Constants
from game.track.track import Track

_GRAVITY = -9.81  # m/s^2

DEBUG_VALS = {
  "Throt": 0,
  "Brake": 0,
  "Steer": 0,
  "Accel": 0,
  "LAccel": 0,
  "Velo": 0,
  "LVelo": 0,
  "Speed": 0,
  "DragF": 0,
  "DriveT": 0,
  "BrakeT": 0,
  "EngRPM": 0,
  "Gear": 0,
  "YawTq": 0,
  "YawAccel": 0,
  "YawRate": 0,
  "Iner": 0,
}


class Car:
  def __init__(
    self,
    cons: Constants,
    pos: tuple[float, float],
    angle_deg: float,
    size: tuple[float, float],
  ):
    self.engine = Engine()
    self.cons = cons
    # Car body constants
    self.size = size
    self.pos = pos
    self.prev_pos = pos
    self.interp_pos = pos
    self.render_pos = pr.vector2_scale(pos, cons.PPM)
    self.angle_rad = math.radians(angle_deg)
    self.prev_angle_rad = self.angle_rad
    self.render_angle_rad = self.angle_rad
    self.mass = 882.0  # kg
    self.inertia = self.mass * (self.size[0] ** 2 + self.size[1] ** 2) / 12

    self.cg_from_rear = 0.45  # %
    self.cg_from_front = 1.0 - self.cg_from_rear  # %
    self.cg_height = 0.15  # m

    self.wheelbase = 3.6  # m
    self.track_width = 1.9  # m
    self.half_track_width = self.track_width / 2  # m
    self.dist_cg_front_axle = self.wheelbase * self.cg_from_front
    self.dist_cg_rear_axle = self.wheelbase * self.cg_from_rear
    self.rear_overhang = 0.85  # m
    cg_dist_from_rear_edge = self.rear_overhang + self.dist_cg_rear_axle
    self.cg = (cg_dist_from_rear_edge - (self.size[0] / 2.0), 0)  # m

    self.front_static = (
      self.mass * -_GRAVITY * self.dist_cg_rear_axle / self.wheelbase / 2
    )
    self.rear_static = (
      self.mass * -_GRAVITY * self.dist_cg_front_axle / self.wheelbase / 2
    )

    # Movement constants
    self.brake_c = 9000.0  # Nm
    self.drag_c = 0.7
    self.roll_resist = 0.015
    self.downforce_c = 3.7

    self.brake_bias_front = 0.6  # %
    self.brake_bias_rear = 1.0 - self.brake_bias_front  # %

    self.max_steer_angle = 25.0  # Deg
    self.steer_speed = 20.0
    self.steer_resist = 30.0  # m/s

    # Movement vars
    self.yaw_rate = 0.0  # Rad/s
    self.steer_angle = 0.0  # Deg
    self.speed = 0.0  # m/s

    # Suspension
    self.sus_stiffness = 10.0
    self.g_force_filtered = (0.0, 0.0)

    # LSD constants
    self.max_preload_t = 300.0
    self.diff_power_lock = 0.85
    self.diff_coast_lock = 0.35
    self.diff_preload = 0.15

    # Vectors
    self.local_accel = (0.0, 0.0)
    self.accel = (0.0, 0.0)
    self.local_velo = (0.0, 0.0)
    self.velo = (0.0, 0.0)

    # Axles
    forward_x = math.cos(self.angle_rad)
    forward_y = math.sin(self.angle_rad)
    f_ax_config = {
      "load": self.front_static,
      "long": {
        "pacejka": {"B": 14, "C": 1.65, "D": 2.6, "E": 0.3},
        "sens": {
          "B": 0.1,
          "D": 0.1,
        },
      },
      "lat": {
        "pacejka": {"B": 18, "C": 1.35, "D": 2.4, "E": 0.5},
        "sens": {
          "B": 0.1,
          "D": 0.2,
        },
      },
      "combined_slip": {
        "SHxa": 0.0,
        "bxa": 1.3,
        "cxa": 1.1,
        "SHyk": 0.0,
        "byk": 1.3,
        "cyk": 1,
        "sens": {
          "bxa": 0.1,
          "byk": 0.1,
        },
      },
    }
    r_ax_config = {
      "load": self.rear_static,
      "long": {
        "pacejka": {"B": 16, "C": 1.65, "D": 2.7, "E": 0.3},
        "sens": {
          "B": 0.12,
          "D": 0.12,
        },
      },
      "lat": {
        "pacejka": {"B": 24, "C": 1.35, "D": 2.56, "E": 0.5},
        "sens": {
          "B": 0.12,
          "D": 0.17,
        },
      },
      "combined_slip": {
        "SHxa": 0.0,
        "bxa": 1.32,
        "cxa": 1.1,
        "SHyk": 0.0,
        "byk": 2.15,
        "cyk": 1.25,
        "sens": {
          "bxa": 0.1,
          "byk": 0.2,
        },
      },
    }

    pos_x, pos_y = self.pos

    front_axle_pos = (
      pos_x + forward_x * self.dist_cg_front_axle,
      pos_y + forward_y * self.dist_cg_front_axle,
    )
    rear_axle_pos = (
      pos_x - forward_x * self.dist_cg_rear_axle,
      pos_y - forward_y * self.dist_cg_rear_axle,
    )
    self.front_axle = Axle(
      cons,
      front_axle_pos,
      self.dist_cg_front_axle,
      self.track_width,
      self.angle_rad,
      0.305,
      18.0,
      self.front_static,
      False,
      f_ax_config,
    )
    self.rear_axle = Axle(
      cons,
      rear_axle_pos,
      -self.dist_cg_rear_axle,
      self.track_width,
      self.angle_rad,
      0.405,
      21.0,
      self.rear_static,
      True,
      r_ax_config,
    )

    self.front_tires = [self.front_axle.left_tire, self.front_axle.right_tire]
    self.rear_tires = [self.rear_axle.left_tire, self.rear_axle.right_tire]
    self.all_tires = self.front_tires + self.rear_tires

    # State variables
    self.off_track = False

  def update(
    self, track: Track, dt: float, inputs: dict[str, float | bool], steer: float
  ) -> int:
    self.off_track = False
    self.prev_angle_rad = self.angle_rad
    curr_sector = self.update_physics(track, dt, inputs, steer)
    return curr_sector

  def update_physics(
    self, track: Track, dt: float, inputs: dict[str, float | bool], steer: float
  ) -> int:
    throttle = inputs["throttle"]
    brake = inputs["brake"]

    forward_x = math.cos(self.angle_rad)
    forward_y = math.sin(self.angle_rad)

    # Update velocity (car)
    velo_x, velo_y = self.velo
    local_velo_x, local_velo_y = self.local_velo
    self.speed = math.sqrt(local_velo_x * local_velo_x + local_velo_y * local_velo_y)

    # Update steering angle
    steer_reduction = self.steer_resist / max(self.speed, 1.0)
    if steer_reduction < 0.1:
      steer_reduction = 0.1
    elif steer_reduction > 1.0:
      steer_reduction = 1.0
    target_steer = self.max_steer_angle * steer * steer_reduction
    self.steer_angle = (
      self.steer_angle + (target_steer - self.steer_angle) * self.steer_speed * dt
    )
    steer_rad = math.radians(self.steer_angle)

    # Building longitudinal force
    num_steps = 8
    sub_dt = dt / num_steps

    brake_t = self.brake_c * brake
    front_brake_t = brake_t * self.brake_bias_front / 2
    rear_brake_t = brake_t * self.brake_bias_rear / 2

    rl = self.rear_axle.left_tire
    rr = self.rear_axle.right_tire
    fl = self.front_axle.left_tire
    fr = self.front_axle.right_tire

    # LSD
    if throttle > 0.05:
      locking_coeff = self.diff_power_lock
    elif brake > 0.05:
      locking_coeff = self.diff_coast_lock
    else:
      locking_coeff = self.diff_preload

    curr_sector = -1

    for _ in range(num_steps):
      # Weight transfer
      downforce = self.downforce_c * self.speed * self.speed
      front_downforce_tire = downforce * self.cg_from_rear / 2
      rear_downforce_tire = downforce * self.cg_from_front / 2

      temp = self.cg_height * self.mass
      g_force_filtered_x, g_force_filtered_y = self.g_force_filtered
      t = self.sus_stiffness * sub_dt

      local_accel_x, local_accel_y = self.local_accel

      g_force_filtered_x = g_force_filtered_x + (local_accel_x - g_force_filtered_x) * t
      g_force_filtered_y = g_force_filtered_y + (local_accel_y - g_force_filtered_y) * t

      transfer_x = temp * g_force_filtered_x / self.wheelbase / 2
      transfer_y = temp * g_force_filtered_y / self.track_width / 2

      self.g_force_filtered = (g_force_filtered_x, g_force_filtered_y)

      weight_front = self.front_static - transfer_x
      weight_rear = self.rear_static + transfer_x

      fl.load = weight_front + transfer_y + front_downforce_tire
      fr.load = weight_front - transfer_y + front_downforce_tire
      rl.load = weight_rear + transfer_y + rear_downforce_tire
      rr.load = weight_rear - transfer_y + rear_downforce_tire

      # Update slip angles through tire ground speed calculations
      fl_velo_x = local_velo_x + self.yaw_rate * self.half_track_width
      fl_velo_y = local_velo_y + self.yaw_rate * self.dist_cg_front_axle
      fr_velo_x = local_velo_x - self.yaw_rate * self.half_track_width
      fr_velo_y = local_velo_y + self.yaw_rate * self.dist_cg_front_axle
      rl_velo = (
        local_velo_x + self.yaw_rate * self.half_track_width,
        local_velo_y - self.yaw_rate * self.dist_cg_rear_axle,
      )
      rr_velo = (
        local_velo_x - self.yaw_rate * self.half_track_width,
        local_velo_y - self.yaw_rate * self.dist_cg_rear_axle,
      )

      sin_steer = math.sin(steer_rad)
      cos_steer = math.cos(steer_rad)

      fl_velo_w = (
        fl_velo_x * cos_steer + fl_velo_y * sin_steer,
        -fl_velo_x * sin_steer + fl_velo_y * cos_steer,
      )

      fr_velo_w = (
        fr_velo_x * cos_steer + fr_velo_y * sin_steer,
        -fr_velo_x * sin_steer + fr_velo_y * cos_steer,
      )

      fl.velo = fl_velo_w
      fr.velo = fr_velo_w
      rl.velo = rl_velo
      rr.velo = rr_velo

      step_total_f_x = 0.0
      step_total_f_y = 0.0
      step_yaw_t = 0.0
      avg_tire_omega = (rl.omega + rr.omega) / 2
      self.engine.update_clutch_torque(sub_dt, throttle, avg_tire_omega)
      base_drive_t = self.engine.get_drive_torque() / 2.0
      added_inertia = self.engine.get_reflected_inertia() / 2.0

      expected_omega_diff = (self.yaw_rate * self.track_width) / rr.radius

      omega_diff = rl.omega - rr.omega - expected_omega_diff
      deadzone = 0.5
      if abs(omega_diff) < deadzone:
        slip_diff = 0.0
      else:
        slip_diff = omega_diff - math.copysign(deadzone, omega_diff)
      lock_stiffness = (
        abs(base_drive_t) * locking_coeff + self.max_preload_t * self.diff_preload
      )
      max_transfer_t = abs(base_drive_t) + self.max_preload_t
      transfer_t = lock_stiffness * slip_diff
      if transfer_t < -max_transfer_t:
        transfer_t = -max_transfer_t
      elif transfer_t > max_transfer_t:
        transfer_t = max_transfer_t

      # --- REAR TIRES ---
      for tire in self.rear_tires:
        if tire == rl:
          tire.drive_t = base_drive_t - transfer_t
        else:
          tire.drive_t = base_drive_t + transfer_t
        tire.brake_t = rear_brake_t
        tire.steer_rad = 0.0

        tire.update_omega(sub_dt, self.speed, throttle, brake, added_inertia)
        tire.update_slip_angle(sub_dt)
        tire.update_slip_ratio(sub_dt)
        tire.update_lateral_force()
        tire.update_long_force()

        force_x, force_y = tire.get_local_force()
        tire_local_coord_x, tire_local_coord_y = tire.local_coord
        step_total_f_x += force_x
        step_total_f_y += force_y
        step_yaw_t += tire_local_coord_x * force_y - tire_local_coord_y * force_x

      # --- FRONT TIRES ---
      for tire in self.front_tires:
        tire.drive_t = 0.0
        tire.brake_t = front_brake_t
        tire.steer_rad = steer_rad

        tire.update_omega(sub_dt, self.speed, throttle, brake, 0.0)
        tire.update_slip_angle(sub_dt)
        tire.update_slip_ratio(sub_dt)
        tire.update_lateral_force()
        tire.update_long_force()

        force_x, force_y = tire.get_local_force()
        tire_local_coord_x, tire_local_coord_y = tire.local_coord
        step_total_f_x += force_x
        step_total_f_y += force_y
        step_yaw_t += tire_local_coord_x * force_y - tire_local_coord_y * force_x

      if self.speed > 0.01:
        roll_f = self.roll_resist * self.mass * -_GRAVITY
        drag_f = self.drag_c * self.speed * self.speed
        total_drag = roll_f + drag_f

        drag_f_x = -local_velo_x / self.speed * total_drag
        drag_f_y = -local_velo_y / self.speed * total_drag
        step_total_f_x += drag_f_x
        step_total_f_y += drag_f_y
      else:
        drag_f_x = 0.0
        drag_f_y = 0.0

      # Rotate car
      yaw_damping = 300.0  # N*m*s/rad
      step_yaw_t -= yaw_damping * self.yaw_rate
      yaw_accel = step_yaw_t / self.inertia
      self.yaw_rate += yaw_accel * sub_dt
      self.angle_rad += self.yaw_rate * sub_dt
      forward_x = math.cos(self.angle_rad)
      forward_y = math.sin(self.angle_rad)
      right = (-math.sin(self.angle_rad), math.cos(self.angle_rad))

      # Update acceleration (car)
      local_accel_x = step_total_f_x / self.mass
      local_accel_y = step_total_f_y / self.mass

      self.local_accel = (local_accel_x, local_accel_y)

      # Update acceleration (world)
      accel_x = local_accel_x * forward_x - local_accel_y * forward_y
      accel_y = local_accel_x * forward_y + local_accel_y * forward_x
      self.accel = (accel_x, accel_y)

      # Update velocity (world)
      velo_x, velo_y = self.velo
      velo_x = velo_x + accel_x * sub_dt
      velo_y = velo_y + accel_y * sub_dt
      self.velo = (velo_x, velo_y)

      local_velo_x = velo_x * forward_x + velo_y * forward_y
      local_velo_y = velo_y * forward_x - velo_x * forward_y

      self.local_velo = (local_velo_x, local_velo_y)
      self.speed = math.sqrt(local_velo_x * local_velo_x + local_velo_y * local_velo_y)

      if not throttle and self.speed < 0.5:
        self.accel = (0.0, 0.0)
        self.local_accel = (0.0, 0.0)
        self.velo = (0.0, 0.0)
        self.local_velo = (0.0, 0.0)
        self.yaw_rate = 0.0
        for tire in self.all_tires:
          tire.stop_forces()

      self.update_positions(sub_dt, (forward_x, forward_y), right, steer_rad)

      any_tire_on_track = False

      for tire in self.all_tires:
        tire.omega = tire.next_omega
        if curr_sector == -1:
          curr_sector = track.check_sectors(tire.prev_local_pos, tire.local_pos)

        on_track, track_indices = track.check_bounds(sub_dt, self.speed, tire)
        tire.surface_multi = 1.0 if on_track else 0.4
        tire.track_indices = [track_indices[0], track_indices[1]]
        if on_track:
          any_tire_on_track = True

      self.off_track = not any_tire_on_track

    # Update gear
    is_slipping = (
      self.rear_axle.left_tire.grip_usage > 0.95
      or self.rear_axle.right_tire.grip_usage > 0.95
      or abs(self.rear_axle.left_tire.slip_ratio) > 0.15
      or abs(self.rear_axle.right_tire.slip_ratio) > 0.15
      or abs(self.rear_axle.left_tire.slip_ratio) == -1
      or abs(self.rear_axle.right_tire.slip_ratio) == -1
    )
    self.engine.update_shift(is_slipping, inputs, auto_shift=False)

    DEBUG_VALS["Throt"] = f"{throttle:>4.3f}"
    DEBUG_VALS["Brake"] = f"{brake:>4.3f}"
    DEBUG_VALS["Accel"] = [f"{accel_x:>12.3f}", f"{accel_y:>12.3f}"]
    DEBUG_VALS["LAccel"] = [
      f"{self.local_accel[0]:>12.3f}",
      f"{self.local_accel[1]:>12.3f}",
    ]
    DEBUG_VALS["Velo"] = [f"{velo_x:>12.3f}", f"{velo_y:>12.3f}"]
    DEBUG_VALS["LVelo"] = [f"{local_velo_x:>12.3f}", f"{local_velo_y:>12.3f}"]
    DEBUG_VALS["Speed"] = f"{self.speed:>12.3f}"
    DEBUG_VALS["DragF"] = [f"{drag_f_x:>12.3f}", f"{drag_f_y:>12.3f}"]
    DEBUG_VALS["DriveT"] = (
      f"{self.rear_axle.left_tire.drive_t + self.rear_axle.right_tire.drive_t:>13.3f}"
    )
    DEBUG_VALS["BrakeT"] = f"{brake_t:>13.3f}"
    DEBUG_VALS["EngRPM"] = f"{self.engine.rpm:>12.3f}"
    DEBUG_VALS["Gear"] = f"{self.engine.gear - 1:>1}"
    DEBUG_VALS["Steer"] = f"{steer:>12.3f}"
    DEBUG_VALS["YawRate"] = f"{math.degrees(self.yaw_rate):>12.3f}"
    DEBUG_VALS["YawAccel"] = f"{yaw_accel:>12.3f}"
    DEBUG_VALS["Iner"] = f"{self.inertia:>12.3f}"

    return curr_sector

  def update_positions(
    self,
    dt: float,
    forward: tuple[float, float],
    right: tuple[float, float],
    steer_rad: float,
  ):
    # Update car body position
    self.prev_pos = self.pos
    pos_x, pos_y = self.pos
    velo_x, velo_y = self.velo
    pos_x = pos_x + velo_x * dt
    pos_y = pos_y + velo_y * dt

    self.pos = (pos_x, pos_y)

    # Update axle positions
    self.front_axle.update_position(self.pos, forward, right, self.angle_rad, steer_rad)
    self.rear_axle.update_position(self.pos, forward, right, self.angle_rad, 0)

  def calculate_render_state(self, alpha: float):
    interp_pos_x = self.prev_pos[0] + (self.pos[0] - self.prev_pos[0]) * alpha
    interp_pos_y = self.prev_pos[1] + (self.pos[1] - self.prev_pos[1]) * alpha
    self.render_angle_rad = (
      self.prev_angle_rad + (self.angle_rad - self.prev_angle_rad) * alpha
    )
    self.interp_pos = (interp_pos_x, interp_pos_y)
    self.render_pos = (
      interp_pos_x * self.cons.PPM,
      interp_pos_y * self.cons.PPM,
    )

  def draw_car(self, car_texture: pr.Texture2D):
    angle_deg = math.degrees(self.render_angle_rad)
    forward = (math.cos(self.render_angle_rad), math.sin(self.render_angle_rad))
    right = (-math.sin(self.render_angle_rad), math.cos(self.render_angle_rad))
    size_draw = (self.size[0] * self.cons.PPM, self.size[1] * self.cons.PPM)
    cg_x, cg_y = self.cg
    cg_draw = (
      (size_draw[0] / 2) + (cg_x * self.cons.PPM),
      (size_draw[1] / 2) + (cg_y * self.cons.PPM),
    )

    src_rec = pr.Rectangle(0.0, 0.0, car_texture.width, car_texture.height)
    dest_rec = pr.Rectangle(
      self.render_pos[0], self.render_pos[1], size_draw[0], size_draw[1]
    )
    pr.draw_texture_pro(car_texture, src_rec, dest_rec, cg_draw, angle_deg, pr.WHITE)

    self.front_axle.draw(forward, right, self.interp_pos, angle_deg, self.steer_angle)
    self.rear_axle.draw(forward, right, self.interp_pos, angle_deg, 0)

  def draw_data(self, screen_width: int, screen_height: int):
    """Show information such as the current gear, rpm, speed, and whether or not the tires are currently slipping.

    Args:
      screen_width: Width of the screen.
      screen_height: Height of the screen.
    """
    screen_width_half = screen_width / 2

    # Gear text
    gear_draw_font_size = 30
    if self.engine.gear == 1:
      curr_gear_text = "N"
    elif self.engine.gear == 0:
      curr_gear_text = "R"
    else:
      curr_gear_text = str(self.engine.gear - 1)
    text_width = pr.measure_text(curr_gear_text, gear_draw_font_size)
    gear_draw_pos_x = int(screen_width_half - text_width / 2)
    gear_draw_pos_y = screen_height - 80

    # Anti stall text
    anti_stall_draw_font_size = 20
    if self.engine.anti_stall:
      anti_stall_text = "AS: ON"
    else:
      anti_stall_text = "AS: OFF"

    text_width = pr.measure_text(anti_stall_text, anti_stall_draw_font_size)
    anti_stall_draw_pos_x = int(screen_width_half - text_width / 2)
    anti_stall_draw_pos_y = screen_height - 40

    # Speed text (kph and mph)
    speed_kph_draw_font_size = 20
    speed_kph = pr.vector2_length(self.velo) * 3.6
    speed_kph_text = f"{round(speed_kph)} kph"
    text_width = pr.measure_text(speed_kph_text, speed_kph_draw_font_size)
    speed_kph_draw_pos_x = int(screen_width_half - text_width / 2 - 100)
    speed_kph_draw_pos_y = screen_height - 70

    speed_mph_draw_font_size = 18
    speed_mph = speed_kph * 0.621371
    speed_mph_text = f"{round(speed_mph)} mph"
    text_width = pr.measure_text(speed_mph_text, speed_mph_draw_font_size)
    speed_mph_draw_pos_x = int(screen_width_half - text_width / 2 - 100)
    speed_mph_draw_pos_y = screen_height - 50

    # RPM text
    rpm_draw_font_size = 20
    rpm_text = f"{round(self.engine.rpm)} RPM"
    text_width = pr.measure_text(rpm_text, rpm_draw_font_size)
    rpm_draw_pos_x = int(screen_width_half - text_width / 2 + 100)
    rpm_draw_pos_y = screen_height - 70

    # Dashboard
    x_offset = screen_width_half * 0.07
    y_offset = screen_height * 0.01
    p1 = pr.Vector2(screen_width_half - 200 - x_offset, screen_height)  # Bottom-left
    p2 = pr.Vector2(screen_width_half + 200 + x_offset, screen_height)  # Bottom-right
    p3 = (
      screen_width_half + 150 + x_offset,
      screen_height - 100 - y_offset,
    )  # Top-right
    p4 = (
      screen_width_half - 150 - x_offset,
      screen_height - 100 - y_offset,
    )  # Top-left

    eng_rpm_ratio = self.engine.rpm / self.engine.peak_rpm
    if eng_rpm_ratio > 1.05:
      shift_light = (27, 119, 239, 200)
    elif eng_rpm_ratio > 0.6:
      shift_light = (255, 239, 1, 200)
    else:
      shift_light = (74, 250, 0, 200)
    pr.draw_rectangle_rounded(
      pr.Rectangle(p4[0], p4[1] - 10, p3[0] - p4[0], 8), 0.2, 10, shift_light
    )

    pr.draw_triangle(p1, p2, p3, (0, 0, 0, 120))  # Translucent black
    pr.draw_triangle(p1, p3, p4, (0, 0, 0, 120))  # Translucent black

    pr.draw_text(
      curr_gear_text, gear_draw_pos_x, gear_draw_pos_y, gear_draw_font_size, pr.WHITE
    )
    pr.draw_text(
      anti_stall_text,
      anti_stall_draw_pos_x,
      anti_stall_draw_pos_y,
      anti_stall_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      speed_kph_text,
      speed_kph_draw_pos_x,
      speed_kph_draw_pos_y,
      speed_kph_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      speed_mph_text,
      speed_mph_draw_pos_x,
      speed_mph_draw_pos_y,
      speed_mph_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(rpm_text, rpm_draw_pos_x, rpm_draw_pos_y, rpm_draw_font_size, pr.WHITE)

  def get_debug_vals(self) -> dict:
    def set_debug_tires():
      return {
        "Omg": 0,
        "F": 0,
        "SpA": 0,
        "SpR": 0,
        "LgF": 0,
        "LtF": 0,
        "Wt": 0,
        "WS": 0,
        "TV": 0,
        "GU": 0,
      }

    debug_fl_tire = set_debug_tires()
    debug_fr_tire = set_debug_tires()
    debug_rl_tire = set_debug_tires()
    debug_rr_tire = set_debug_tires()

    debug_tires = [debug_fl_tire, debug_fr_tire, debug_rl_tire, debug_rr_tire]
    tires = [
      self.front_axle.left_tire,
      self.front_axle.right_tire,
      self.rear_axle.left_tire,
      self.rear_axle.right_tire,
    ]

    for i in range(4):
      tire = tires[i]
      d_t = debug_tires[i]

      # force = tire.get_local_force()
      d_t["Omg"] = f"{tire.omega:>7.3f}"
      d_t["SpA"] = f"{math.degrees(tire.slip_angle):>7.3f}"
      d_t["SpR"] = f"{tire.slip_ratio:>7.3f}"
      d_t["LgF"] = f"{tire.long_f:>9.3f}"
      d_t["LtF"] = f"{tire.lateral_f:>9.3f}"
      d_t["Wt"] = f"{tire.load:>7.3f}"
      # d_t["F"] = [f"{force.x:>9.3f}", f"{force.y:>9.3f}"]
      d_t["WS"] = f"{(tire.omega * tire.radius):>7.3f}"
      d_t["TV"] = [f"{tire.velo[0]:>7.3f}", f"{tire.velo[1]:>7.3f}"]
      d_t["GU"] = f"{tire.grip_usage:>7.3f}"

    DEBUG_VALS["FLTire"] = debug_fl_tire
    DEBUG_VALS["FRTire"] = debug_fr_tire
    DEBUG_VALS["RLTire"] = debug_rl_tire
    DEBUG_VALS["RRTire"] = debug_rr_tire

    return DEBUG_VALS
