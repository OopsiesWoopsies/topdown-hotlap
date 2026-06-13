import math

import pyray as pr


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.pos = pos
    self.size = size
    self.mass = 1200.0
    self.angle_deg = angle_deg

    self.vel = pr.Vector2(0, 0)
    self.angular_velocity = 0.0
    self.max_lateral_accel = 10.0

    self.wheelbase = 60.0
    self.front_axle = self.wheelbase * 0.5
    self.rear_axle = self.wheelbase * 0.5

    self.inertia = self.mass * (self.wheelbase**2) * 0.001

    self.max_steer = 50.0
    self.steer_angle = 0.0
    self.steer_speed = math.radians(90)

    self.grip = 5.0
    self.front_stiffness = 1200.0
    self.rear_stiffness = 800.0

    self.engine_power = 800.0
    self.brake_power = 600.0
    self.engine_brake = 20.0
    self.air_resist = 0.3

  def update(self, dt: float, throttle: bool, brake: bool, steer: float):
    yaw_torque = self.update_physics(dt, throttle, brake, steer)
    self.integrate_rotation(dt, yaw_torque)
    self.update_pos(dt)

  def integrate_rotation(self, dt: float, yaw_torque: float):
    angular_accel = yaw_torque / self.inertia
    self.angular_velocity += angular_accel * dt
    self.angular_velocity -= self.angular_velocity * 1.5 * dt

    self.angle_deg += math.degrees(self.angular_velocity) * dt

  def update_physics(self, dt: float, throttle: bool, brake: bool, steer: float):
    tire_fric = 2
    target_steer = math.radians(self.max_steer) * steer

    if self.steer_angle < target_steer:
      self.steer_angle = min(self.steer_angle + self.steer_speed * dt, target_steer)
    else:
      self.steer_angle = max(self.steer_angle - self.steer_speed * dt, target_steer)

    angle_rad = math.radians(self.angle_deg)
    forward = pr.Vector2(math.sin(angle_rad), -math.cos(angle_rad))
    right = pr.Vector2(math.cos(angle_rad), math.sin(angle_rad))
    forward_speed = pr.vector2_dot_product(self.vel, forward)
    lateral_speed = pr.vector2_dot_product(self.vel, right)

    if throttle and brake:
      forward_speed -= self.brake_power * dt
      tire_fric = 5.0
    elif brake:
      forward_speed -= self.brake_power * dt
      tire_fric = 5.0
    elif throttle:
      forward_speed += self.engine_power * dt
    else:
      forward_speed -= self.engine_brake * dt

    forward_speed -= self.air_resist * forward_speed * dt
    lateral_speed -= self.air_resist * lateral_speed * dt

    lateral_speed -= lateral_speed * tire_fric * dt

    front_slip_angle = (
      math.atan2(
        lateral_speed + self.angular_velocity * self.front_axle,
        max(abs(forward_speed), 1.0),
      )
      - self.steer_angle
    )

    rear_slip_angle = math.atan2(
      lateral_speed - self.angular_velocity * self.rear_axle,
      max(abs(forward_speed), 1.0),
    )
    front_force = -front_slip_angle * self.front_stiffness
    rear_force = -rear_slip_angle * self.rear_stiffness

    total_lateral_force = front_force + rear_force
    lateral_accel = total_lateral_force / self.mass
    lateral_speed += lateral_accel * dt

    self.vel.x = forward.x * forward_speed + right.x * lateral_speed
    self.vel.y = forward.y * forward_speed + right.y * lateral_speed

    speed = pr.vector2_length(self.vel)

    yaw_torque = front_force * self.front_axle - rear_force * self.rear_axle

    print(
      f"{[f'VX {self.vel.x:<20.5f}', f'VY {self.vel.y:<20.5f}']} {
        [f'S {speed:<20.5f}', f'F {forward_speed:<20.5f}', f'L {lateral_speed:<20.5f}']
      } {
        [
          f'FSA {math.degrees(front_slip_angle):<20.5f}',
          f'RSA {math.degrees(rear_slip_angle):<20.5f}'
        ]
      } {[f'AV {self.angular_velocity:<20.5f}', f'YT {yaw_torque:<20.5f}']}, SA {
        self.steer_angle:<20.5f}"
    )

    return yaw_torque

  def update_pos(self, dt: float):
    self.pos.x += self.vel.x * dt
    self.pos.y += self.vel.y * dt

  def draw(self, alpha: float):
    rec = pr.Rectangle(self.pos.x, self.pos.y, self.size.x, self.size.y)

    pr.draw_rectangle_pro(
      rec, pr.Vector2(self.size.x / 2, self.size.y / 2), self.angle_deg, pr.RED
    )

    angle_rad = math.radians(self.angle_deg)

    # Forward vector
    pr.draw_line(
      int(self.pos.x),
      int(self.pos.y),
      int(self.pos.x + math.sin(angle_rad) * 100),
      int(self.pos.y - math.cos(angle_rad) * 100),
      pr.BLUE,
    )
    # Right vector
    pr.draw_line(
      int(self.pos.x),
      int(self.pos.y),
      int(self.pos.x + math.cos(angle_rad) * 100),
      int(self.pos.y + math.sin(angle_rad) * 100),
      pr.BLUE,
    )
