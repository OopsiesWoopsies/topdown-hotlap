import math

import pyray as pr


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.pos = pos
    self.size = size
    self.angle_deg = angle_deg

    self.vel = pr.Vector2(0, 0)
    self.angular_velocity = 0.0
    self.max_lateral_accel = 10.0

    self.wheelbase = 60.0
    self.max_steer = 50.0
    self.grip = 5.0
    self.cornering_stiffness = 10.0

    self.engine_power = 800.0
    self.brake_power = 600.0
    self.engine_brake = 20.0
    self.air_resist = 0.3

  def update(self, dt: float, throttle: bool, brake: bool, steer: float):
    self.update_steering(dt, steer)
    self.update_physics(dt, throttle, brake)
    self.update_pos(dt)

  def update_steering(self, dt: float, steer: float):
    angle_rad = math.radians(self.angle_deg)
    forward = pr.Vector2(math.sin(angle_rad), -math.cos(angle_rad))
    forward_speed = pr.vector2_dot_product(self.vel, forward)

    steer_angle = math.radians(self.max_steer) * steer
    target_yaw_rate = forward_speed / self.wheelbase * math.tan(steer_angle)

    yaw_response = 1
    self.angular_velocity += (
      (target_yaw_rate - self.angular_velocity) * yaw_response * dt
    )

    self.angle_deg += math.degrees(self.angular_velocity) * dt

  def update_physics(self, dt: float, throttle: bool, brake: bool):
    tire_fric = 2
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

    if forward_speed < 0:
      forward_speed = 0

    slip_angle = math.atan2(lateral_speed, max(abs(forward_speed), 1.0))
    lateral_force = -slip_angle * self.cornering_stiffness
    lateral_force = pr.clamp(
      lateral_force, -self.max_lateral_accel, self.max_lateral_accel
    )

    lateral_speed += lateral_force * dt

    self.vel.x = forward.x * forward_speed + right.x * lateral_speed
    self.vel.y = forward.y * forward_speed + right.y * lateral_speed

    speed = pr.vector2_length(self.vel)

    print(
      f"{[f'{self.vel.x:<20.5f}', f'{self.vel.y:<20.5f}']} {
        [f'{speed:<20.5f}', f'{forward_speed:<20.5f}', f'{lateral_speed:<20.5f}']
      } {math.degrees(slip_angle):<20.5f} {self.angular_velocity:<20.5f}"
    )

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
