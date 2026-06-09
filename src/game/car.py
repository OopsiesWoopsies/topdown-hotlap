import math

import pyray as pr


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.pos = pos
    self.size = size
    self.angle_deg = angle_deg

    self.forward_speed = 0.0
    self.lateral_speed = 0.0
    self.angular_speed = 0.0

    self.max_steer = 50.0

    self.engine_power = 1000.0
    self.brake_power = 1200.0
    self.engine_brake = 20.0
    self.air_resist = 0.5

  def update(self, dt: float, throttle: bool, brake: bool, steer: float):
    self.update_steering(dt, steer)
    self.update_physics(dt, throttle, brake)
    self.update_pos(dt)

  def update_steering(self, dt: float, steer: float):
    steering_strength = math.tanh(self.forward_speed / 20.0)
    self.angle_deg += self.max_steer * steer * steering_strength * dt

  def update_physics(self, dt: float, throttle: bool, brake: bool):
    if throttle and brake:
      self.forward_speed -= self.brake_power * dt
    elif brake:
      self.forward_speed -= self.brake_power * dt
    elif throttle:
      self.forward_speed += self.engine_power * dt
    else:
      self.forward_speed -= self.engine_brake * dt

    self.forward_speed -= self.air_resist * self.forward_speed * dt

    if self.forward_speed < 0:
      self.forward_speed = 0.0

  def update_pos(self, dt: float):
    angle_rad = math.radians(self.angle_deg)
    forward = pr.Vector2(math.sin(angle_rad), -math.cos(angle_rad))
    right = pr.Vector2(math.cos(angle_rad), math.sin(angle_rad))
    world_vel = pr.Vector2(
      forward.x * self.forward_speed + right.x * self.lateral_speed,
      forward.y * self.forward_speed + right.y * self.lateral_speed,
    )

    self.pos.x += world_vel.x * dt
    self.pos.y += world_vel.y * dt

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
