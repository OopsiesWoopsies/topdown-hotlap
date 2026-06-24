import math

import pyray as pr

from game.car.axle import Axle
from game.car.engine import Engine
from game.constants import PIXELS_PER_METER

_GRAVITY = -9.81  # m/s^2

DEBUG_VALS = {
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
  "AvgOmg": 0,
  "EngRPM": 0,
  "Gear": 0,
}


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.engine = Engine()
    # Car body constants
    self.size = size
    self.pos = pos
    self.render_pos = pr.vector2_scale(pos, PIXELS_PER_METER)
    self.mass = 750  # kg
    self.cg_to_front = 0.45  # %
    self.cg_to_rear = 0.55  # %
    self.cg_height = 0.3  # m
    self.cg = pr.Vector2(0, (self.size.x * 0.45 - self.size.x / 2))  # m
    self.angle_rad = math.radians(angle_deg)
    self.weight_transfer = 1.0
    self.track_width = 1.9  # m

    self.front_dist_from_center = self.size.x * 0.26  # m
    self.rear_dist_from_center = -self.size.x * 0.43  # m
    self.wheelbase = abs(self.front_dist_from_center) + abs(self.rear_dist_from_center)

    dist_cg_front_axle = abs(self.cg.y - self.front_dist_from_center)
    dist_cg_rear_axle = abs(self.rear_dist_from_center - self.cg.y)

    self.front_static = self.mass * -_GRAVITY * dist_cg_front_axle / self.wheelbase / 2
    self.rear_static = self.mass * -_GRAVITY * dist_cg_rear_axle / self.wheelbase / 2

    # Axles
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))

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
      self.track_width,
      self.angle_rad,
      0.275,
      18.0,
      self.front_static,
    )
    self.rear_axle = Axle(
      rear_axle_pos,
      self.rear_dist_from_center,
      self.track_width,
      self.angle_rad,
      0.375,
      21.0,
      self.rear_static,
    )

    # Vectors
    self.local_accel = pr.Vector2(0, 0)
    self.accel = pr.Vector2(0, 0)
    self.local_velo = pr.Vector2(0, 0)
    self.velo = pr.Vector2(0, 0)

    # Movement constants
    self.brake_c = 4000 * 1  # N
    self.drag_c = 0.7
    self.roll_resist = 0.015
    self.downforce_c = 3.5

  def update(self, dt: float, throttle: bool, brake: bool, steer: float):
    self.update_physics(dt, throttle, brake)
    self.update_positions(dt)

  def update_physics(self, dt: bool, throttle: bool, brake: bool):
    forward = pr.Vector2(math.cos(self.angle_rad), math.sin(self.angle_rad))

    # Update velocity (car)
    self.local_velo.x = self.velo.x * forward.x + self.velo.y * forward.y
    self.local_velo.y = self.velo.y * forward.x - self.velo.x * forward.y
    speed = pr.vector2_length(self.local_velo)

    # Weight transfer
    downforce = self.downforce_c * speed * speed
    front_downforce_tire = downforce * self.cg_to_front / 2
    rear_downforce_tire = downforce * self.cg_to_rear / 2

    temp = self.weight_transfer * self.cg_height * self.mass
    transfer_x = temp * self.local_accel.x / self.wheelbase / 2
    transfer_y = temp * self.local_accel.y / self.track_width / 2

    weight_front = self.front_static - transfer_x
    weight_rear = self.rear_static + transfer_x

    self.front_axle.left_tire.weight = weight_front - transfer_y + front_downforce_tire
    self.front_axle.right_tire.weight = weight_front + transfer_y + front_downforce_tire
    self.rear_axle.left_tire.weight = weight_rear - transfer_y + rear_downforce_tire
    self.rear_axle.right_tire.weight = weight_rear + transfer_y + rear_downforce_tire

    # Building longitudinal force
    drive_t = self.engine.get_drive_torque(
      dt, throttle, self.local_velo.x, self.rear_axle.left_tire.radius
    )
    brake_t = self.brake_c * brake * math.copysign(1, self.local_velo.x)

    drive_t /= 2
    brake_t /= 2

    # Compute slip ratios for each tire and traction forces and tire omegas for motorized tires
    for tire in [self.rear_axle.left_tire, self.rear_axle.right_tire]:
      tire.update_traction_ratio(drive_t)
      tire.update_traction_force()
      tire.update_brake_ratio(brake_t)

    # Update gear
    self.engine.update_shift(self.engine.get_rpm())

    brake_f = (
      self.rear_axle.left_tire.get_brake_force()
      + self.rear_axle.right_tire.get_brake_force()
    )

    # Compute long force
    drive_f = (
      self.rear_axle.left_tire.get_traction_force()
      + self.rear_axle.right_tire.get_traction_force()
    )

    traction_f_x = drive_f - brake_f
    traction_f_y = 0

    drag_f_x = (
      -self.roll_resist * self.local_velo.x - self.drag_c * self.local_velo.x * speed
    )
    drag_f_y = (
      -self.roll_resist * self.local_velo.y - self.drag_c * self.local_velo.y * speed
    )

    long_f_x = traction_f_x + drag_f_x
    long_f_y = traction_f_y + drag_f_y

    # Update acceleration (car)
    self.local_accel.x = long_f_x / self.mass
    self.local_accel.y = long_f_y / self.mass

    # Update acceleration (world)
    self.accel.x = self.local_accel.x * forward.x - self.local_accel.y * forward.y
    self.accel.y = self.local_accel.x * forward.y + self.local_accel.y * forward.x

    # Update velocity (world)
    self.velo = pr.vector2_add(self.velo, pr.vector2_scale(self.accel, dt))

    if not throttle and speed < 0.5:
      self.accel = pr.Vector2(0, 0)
      self.local_accel = pr.Vector2(0, 0)
      self.velo = pr.Vector2(0, 0)
      self.local_velo = pr.Vector2(0, 0)

    global DEBUG_VALS
    DEBUG_VALS = {
      "Throt": f"{throttle}",
      "Brake": f"{brake}",
      "Accel": [f"{self.accel.x:>12.5f}", f"{self.accel.y:>12.5f}"],
      "LAccel": [f"{self.local_accel.x:>12.5f}", f"{self.local_accel.y:>12.5f}"],
      "Velo": [f"{self.velo.x:>12.5f}", f"{self.velo.y:>12.5f}"],
      "LVelo": [f"{self.local_velo.x:>12.5f}", f"{self.local_velo.y:>12.5f}"],
      "Speed": f"{speed:>12.5f}",
      "LongF": [f"{long_f_x:>12.5f}", f"{long_f_y:>12.5f}"],
      "TractionF": [f"{traction_f_x:>12.5f}", f"{traction_f_y:>12.5f}"],
      "DragF": [f"{drag_f_x:>12.5f}", f"{drag_f_y:>12.5f}"],
      "DriveT": f"{drive_t:>13.5f}",
      "BrakeT": f"{brake_t:>13.5f}",
      "EngRPM": f"{self.engine.rpm:>12.5f}",
      "Gear": f"{self.engine.gear + 1:>12.5f}",
    }

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

    self.front_axle.draw(angle_deg)
    self.rear_axle.draw(angle_deg)

  def get_debug_vals(self) -> dict:
    debug_fl_tire = {
      "BrakeR": f"{self.front_axle.left_tire.brake_ratio:>12.5f}",
      "TractionR": f"{self.front_axle.left_tire.traction_ratio:>12.5f}",
      "TracF": f"{self.front_axle.left_tire.traction_f:>12.5f}",
      "Weight": f"{self.front_axle.left_tire.weight:>12.5f}",
    }
    debug_fr_tire = {
      "BrakeR": f"{self.front_axle.right_tire.brake_ratio:>12.5f}",
      "TractionR": f"{self.front_axle.right_tire.traction_ratio:>12.5f}",
      "TracF": f"{self.front_axle.right_tire.traction_f:>12.5f}",
      "Weight": f"{self.front_axle.right_tire.weight:>12.5f}",
    }
    debug_rl_tire = {
      "BrakeR": f"{self.rear_axle.left_tire.brake_ratio:>12.5f}",
      "TractionR": f"{self.rear_axle.left_tire.traction_ratio:>12.5f}",
      "TracF": f"{self.rear_axle.left_tire.traction_f:>12.5f}",
      "Weight": f"{self.rear_axle.left_tire.weight:>12.5f}",
    }
    debug_rr_tire = {
      "BrakeR": f"{self.rear_axle.right_tire.brake_ratio:>12.5f}",
      "TractionR": f"{self.rear_axle.right_tire.traction_ratio:>12.5f}",
      "TracF": f"{self.rear_axle.right_tire.traction_f:>12.5f}",
      "Weight": f"{self.rear_axle.right_tire.weight:>12.5f}",
    }

    DEBUG_VALS["FLTire"] = debug_fl_tire
    DEBUG_VALS["FRTire"] = debug_fr_tire
    DEBUG_VALS["RLTire"] = debug_rl_tire
    DEBUG_VALS["RRTire"] = debug_rr_tire

    return DEBUG_VALS
