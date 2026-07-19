import math

import pyray as pr

from game.car.axle import Axle
from game.car.engine import Engine
from game.constants import PIXELS_PER_METER

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
  "LongF": 0,
  "TractionF": 0,
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
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.engine = Engine()
    # Car body constants
    self.size = size
    self.pos = pos
    self.render_pos = pr.vector2_scale(pos, PIXELS_PER_METER)
    self.angle_rad = math.radians(angle_deg)
    self.mass = 750  # kg
    self.inertia = self.mass * (self.size.x**2 + self.size.y**2) / 12

    self.cg_to_front = 0.45  # %
    self.cg_to_rear = 1 - self.cg_to_front  # %
    self.cg_height = 0.3  # m
    self.cg = pr.Vector2(0, (self.size.x * self.cg_to_front - self.size.x / 2))  # m

    self.brake_bias_front = 0.6  # %
    self.brake_bias_rear = 1 - self.brake_bias_front  # %

    self.max_steer_angle = 25  # Deg
    self.steer_angle = 0.0  # Deg
    self.steer_step = 0.7  # Deg

    self.front_dist_from_center = self.size.x * 0.26  # m
    self.rear_dist_from_center = -self.size.x * 0.43  # m
    self.wheelbase = abs(self.front_dist_from_center) + abs(self.rear_dist_from_center)
    self.track_width = 1.9  # m

    self.dist_cg_front_axle = abs(self.cg.y - self.front_dist_from_center)
    self.dist_cg_rear_axle = abs(self.rear_dist_from_center - self.cg.y)

    self.front_static = (
      self.mass * -_GRAVITY * self.dist_cg_front_axle / self.wheelbase / 2
    )
    self.rear_static = (
      self.mass * -_GRAVITY * self.dist_cg_rear_axle / self.wheelbase / 2
    )

    # Movement constants
    self.brake_c = 10000  # N
    self.drag_c = 0.7
    self.roll_resist = 0.015
    self.downforce_c = 3.5

    # Movement vars
    self.yaw_rate = 0.0  # Rad/s

    # Vectors
    self.local_accel = pr.Vector2(0, 0)
    self.accel = pr.Vector2(0, 0)
    self.local_velo = pr.Vector2(0, 0)
    self.velo = pr.Vector2(0, 0)

    # Axles
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))
    f_ax_lat_config = {
      "pacejka": {"B": 10, "C": 1.9, "D": 1.6, "E": 0.9},
      "load": self.front_static,
      "sens": 0.09,
    }
    f_ax_long_config = {
      "pacejka": {"B": 12, "C": 1.6, "D": 1.6, "E": -0.5},
      "load": self.front_static,
      "sens": 0.09,
    }
    r_ax_lat_config = {
      "pacejka": {"B": 10, "C": 1.9, "D": 1.55, "E": 0.8},
      "load": self.rear_static,
      "sens": 0.09,
    }
    r_ax_long_config = {
      "pacejka": {"B": 12, "C": 1.5, "D": 1.5, "E": -0.5},
      "load": self.rear_static,
      "sens": 0.09,
    }

    front_axle_pos = pr.Vector2(
      self.pos.x + forward.x * self.front_dist_from_center,
      self.pos.y + forward.y * self.front_dist_from_center,
    )
    rear_axle_pos = pr.Vector2(
      self.pos.x + forward.x * self.rear_dist_from_center,
      self.pos.y + forward.y * self.rear_dist_from_center,
    )
    self.front_axle = Axle(
      front_axle_pos,
      self.front_dist_from_center,
      self.dist_cg_front_axle,
      self.track_width,
      self.angle_rad,
      0.275,
      18.0,
      self.front_static,
      False,
      f_ax_lat_config,
      f_ax_long_config,
    )
    self.rear_axle = Axle(
      rear_axle_pos,
      self.rear_dist_from_center,
      -self.dist_cg_rear_axle,
      self.track_width,
      self.angle_rad,
      0.375,
      21.0,
      self.rear_static,
      True,
      r_ax_lat_config,
      r_ax_long_config,
    )

  def update(self, dt: float, throttle: bool, brake: bool, steer: float):
    self.update_physics(dt, throttle, brake, steer)
    self.update_positions(dt)

  def update_physics(self, dt: float, throttle: bool, brake: bool, steer: float):
    front_tires = [self.front_axle.left_tire, self.front_axle.right_tire]
    rear_tires = [self.rear_axle.left_tire, self.rear_axle.right_tire]
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))

    # Update velocity (car)
    self.local_velo.x = self.velo.x * forward.x + self.velo.y * forward.y
    self.local_velo.y = self.velo.y * forward.x - self.velo.x * forward.y
    speed = pr.vector2_length(self.local_velo)

    # Update steering angle
    self.steer_angle = self.max_steer_angle * steer
    steer_rad = math.radians(self.steer_angle)

    # Update slip angles through tire ground speed calculations
    half_track = self.track_width / 2
    fl_velo = pr.Vector2(
      self.local_velo.x - self.yaw_rate * half_track,
      self.local_velo.y + self.yaw_rate * self.dist_cg_front_axle,
    )
    fr_velo = pr.Vector2(
      self.local_velo.x + self.yaw_rate * half_track,
      self.local_velo.y + self.yaw_rate * self.dist_cg_front_axle,
    )
    rl_velo = pr.Vector2(
      self.local_velo.x - self.yaw_rate * half_track,
      self.local_velo.y - self.yaw_rate * self.dist_cg_rear_axle,
    )
    rr_velo = pr.Vector2(
      self.local_velo.x + self.yaw_rate * half_track,
      self.local_velo.y - self.yaw_rate * self.dist_cg_rear_axle,
    )

    fl_velo_w = pr.Vector2(
      fl_velo.x * math.cos(steer_rad) + fl_velo.y * math.sin(steer_rad),
      -fl_velo.x * math.sin(steer_rad) + fl_velo.y * math.cos(steer_rad),
    )
    fr_velo_w = pr.Vector2(
      fr_velo.x * math.cos(steer_rad) + fr_velo.y * math.sin(steer_rad),
      -fr_velo.x * math.sin(steer_rad) + fr_velo.y * math.cos(steer_rad),
    )
    self.front_axle.left_tire.velo = fl_velo_w
    self.front_axle.right_tire.velo = fr_velo_w
    self.rear_axle.left_tire.velo = rl_velo
    self.rear_axle.right_tire.velo = rr_velo

    # Weight transfer
    downforce = self.downforce_c * speed * speed
    front_downforce_tire = downforce * self.cg_to_front / 2
    rear_downforce_tire = downforce * self.cg_to_rear / 2

    temp = self.cg_height * self.mass
    transfer_x = temp * self.local_accel.x / self.wheelbase / 2
    transfer_y = temp * self.local_accel.y / self.track_width / 2

    weight_front = self.front_static - transfer_x
    weight_rear = self.rear_static + transfer_x

    self.front_axle.left_tire.load = weight_front + transfer_y + front_downforce_tire
    self.front_axle.right_tire.load = weight_front - transfer_y + front_downforce_tire
    self.rear_axle.left_tire.load = weight_rear + transfer_y + rear_downforce_tire
    self.rear_axle.right_tire.load = weight_rear - transfer_y + rear_downforce_tire

    # Building longitudinal force
    avg_tire_omega = (
      self.rear_axle.left_tire.omega + self.rear_axle.right_tire.omega
    ) / 2
    drive_t = self.engine.get_drive_torque(
      dt,
      throttle,
      avg_tire_omega,
    )
    brake_t = self.brake_c * brake

    drive_t /= 2
    brake_t /= 4

    total_force = pr.Vector2(0, 0)
    yaw_torque = 0.0

    # Compute traction forces & ratios, brake ratios, and accumulate yaw torque and forces for each tire
    for tire in rear_tires:
      tire.drive_t = drive_t
      tire.brake_t = brake_t

      tire.update_slip_angle()
      tire.update_slip_ratio(dt)
      tire.update_lateral_force()
      tire.update_long_force()
      tire.steer_rad = 0

      force = tire.get_local_force()
      total_force = pr.vector2_add(force, total_force)
      yaw_torque += tire.local_coord.x * force.y - tire.local_coord.y * force.x
      tire.update_omega(dt, speed, throttle, brake)

    for tire in front_tires:
      tire.drive_t = 0.0
      tire.brake_t = brake_t

      tire.update_slip_angle()
      tire.update_slip_ratio(dt)
      tire.update_lateral_force()
      tire.update_long_force()
      tire.steer_rad = steer_rad

      force = tire.get_local_force()
      total_force = pr.vector2_add(force, total_force)
      yaw_torque += tire.local_coord.x * force.y - tire.local_coord.y * force.x
      tire.update_omega(dt, speed, throttle, brake)

    for tire in front_tires + rear_tires:
      tire.omega = tire.next_omega

    # Update gear
    self.engine.update_shift(self.engine.get_rpm())

    # Compute long force
    if speed > 0.01:
      roll_f = self.roll_resist * self.mass * -_GRAVITY
      drag_f = self.drag_c * speed * speed

      total_drag = roll_f + drag_f

      drag_f_x = -self.local_velo.x / speed * total_drag
      drag_f_y = -self.local_velo.y / speed * total_drag
    else:
      drag_f_x = 0.0
      drag_f_y = 0.0

    long_f_x = total_force.x + drag_f_x
    long_f_y = total_force.y + drag_f_y

    # Rotate car
    yaw_damping = 300.0  # N*m*s/rad
    yaw_torque -= yaw_damping * self.yaw_rate
    yaw_accel = yaw_torque / self.inertia
    self.yaw_rate += yaw_accel * dt
    self.angle_rad += self.yaw_rate * dt
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))

    # Update acceleration (car)
    self.local_accel.x = long_f_x / self.mass
    self.local_accel.y = long_f_y / self.mass

    # Update acceleration (world)
    self.accel.x = self.local_accel.x * forward.x - self.local_accel.y * forward.y
    self.accel.y = self.local_accel.x * forward.y + self.local_accel.y * forward.x

    # Update velocity (world)
    self.velo = pr.vector2_add(self.velo, pr.vector2_scale(self.accel, dt))

    if not throttle and speed < 1:
      self.accel = pr.Vector2(0, 0)
      self.local_accel = pr.Vector2(0, 0)
      self.velo = pr.Vector2(0, 0)
      self.local_velo = pr.Vector2(0, 0)
      self.yaw_rate = 0

    global DEBUG_VALS
    DEBUG_VALS["Throt"] = f"{throttle:1}"
    DEBUG_VALS["Brake"] = f"{brake:>1}"
    DEBUG_VALS["Accel"] = [f"{self.accel.x:>12.3f}", f"{self.accel.y:>12.3f}"]
    DEBUG_VALS["LAccel"] = [
      f"{self.local_accel.x:>12.3f}",
      f"{self.local_accel.y:>12.3f}",
    ]
    DEBUG_VALS["Velo"] = [f"{self.velo.x:>12.3f}", f"{self.velo.y:>12.3f}"]
    DEBUG_VALS["LVelo"] = [f"{self.local_velo.x:>12.3f}", f"{self.local_velo.y:>12.3f}"]
    DEBUG_VALS["Speed"] = f"{speed:>12.3f}"
    DEBUG_VALS["LongF"] = [f"{long_f_x:>12.3f}", f"{long_f_y:>12.3f}"]
    DEBUG_VALS["TractionF"] = [f"{total_force.x:>12.3f}", f"{total_force.y:>12.3f}"]
    DEBUG_VALS["DragF"] = [f"{drag_f_x:>12.3f}", f"{drag_f_y:>12.3f}"]
    DEBUG_VALS["DriveT"] = f"{drive_t:>13.3f}"
    DEBUG_VALS["BrakeT"] = f"{brake_t:>13.3f}"
    DEBUG_VALS["EngRPM"] = f"{self.engine.rpm:>12.3f}"
    DEBUG_VALS["Gear"] = f"{self.engine.gear + 1:>1}"
    DEBUG_VALS["Steer"] = f"{steer:>12.3f}"
    DEBUG_VALS["YawRate"] = f"{math.degrees(self.yaw_rate):>12.3f}"
    DEBUG_VALS["YawTq"] = f"{yaw_torque:>12.3f}"
    DEBUG_VALS["YawAccel"] = f"{yaw_accel:>12.3f}"
    DEBUG_VALS["Iner"] = f"{self.inertia:>12.3f}"

  def update_positions(self, dt):
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))
    right = pr.Vector2(-math.sin(self.angle_rad), math.cos(self.angle_rad))

    # Update car body position
    self.pos = pr.vector2_add(self.pos, pr.vector2_scale(self.velo, dt))

    # Update axle positions
    self.front_axle.update_position(self.pos, forward, right)
    self.rear_axle.update_position(self.pos, forward, right)

  def draw(self, alpha: float):
    angle_deg = math.degrees(self.angle_rad)
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))
    right = pr.Vector2(-math.sin(self.angle_rad), math.cos(self.angle_rad))

    cg_world_x = self.pos.x + right.x * self.cg.x + forward.x * self.cg.y
    cg_world_y = self.pos.y + right.y * self.cg.x + forward.y * self.cg.y

    pos_draw = pr.vector2_scale(self.pos, PIXELS_PER_METER)
    size_draw = pr.vector2_scale(self.size, PIXELS_PER_METER)

    self.render_pos = pos_draw

    rec = pr.Rectangle(pos_draw.x, pos_draw.y, size_draw.x, size_draw.y)
    car_origin = pr.Vector2(size_draw.x / 2, size_draw.y / 2)
    pr.draw_rectangle_pro(rec, car_origin, angle_deg, pr.RED)

    pr.draw_circle(
      int(cg_world_x * PIXELS_PER_METER),
      int(cg_world_y * PIXELS_PER_METER),
      5.0,
      pr.BLACK,
    )

    self.front_axle.draw(angle_deg, self.steer_angle)
    self.rear_axle.draw(angle_deg, 0)

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
      grip_usage = (
        tire.lateral_f / (tire.max_lat_D * tire.load)
      ) ** 2 + (tire.long_f / (tire.max_long_D * tire.load)) ** 2

      # force = tire.get_local_force()
      d_t["Omg"] = f"{tire.omega:>7.3f}"
      d_t["SpA"] = f"{math.degrees(tire.slip_angle):>7.3f}"
      d_t["SpR"] = f"{tire.slip_ratio:>7.3f}"
      d_t["LgF"] = f"{tire.long_f:>9.3f}"
      d_t["LtF"] = f"{tire.lateral_f:>9.3f}"
      d_t["Wt"] = f"{tire.load:>7.3f}"
      # d_t["F"] = [f"{force.x:>9.3f}", f"{force.y:>9.3f}"]
      d_t["WS"] = f"{(tire.omega * tire.radius):>7.3f}"
      d_t["TV"] = [f"{tire.velo.x:>7.3f}", f"{tire.velo.y:>7.3f}"]
      d_t["GU"] = f"{grip_usage:>7.3f}"

    DEBUG_VALS["FLTire"] = debug_fl_tire
    DEBUG_VALS["FRTire"] = debug_fr_tire
    DEBUG_VALS["RLTire"] = debug_rl_tire
    DEBUG_VALS["RRTire"] = debug_rr_tire

    return DEBUG_VALS
