import math

import pyray as pr

loop = 2 * math.pi


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.pos = pos
    self.render_pos = pos
    self.prev_pos = pr.Vector2(self.pos.x, self.pos.y)

    self.velo = 0.0
    self.size = size

    self.angle_rad = math.radians(angle_deg)
    self.prev_angle = self.angle_rad

    self.direction = pr.Vector2(math.sin(self.angle_rad), -math.cos(self.angle_rad))
    self.max_steer = 0.01

    self.brake_power = 2000
    self.engine_power = 1000
    self.engine_brake = 100

    self.air_resist = 0.0005

    self.flw = Wheel(
      pos_center_offset=pr.Vector2(-size.x / 2, -size.y / 2),
      size=pr.Vector2(8, 15),
    )
    self.frw = Wheel(
      pos_center_offset=pr.Vector2(size.x / 2, -size.y / 2),
      size=pr.Vector2(8, 15),
    )
    self.rlw = Wheel(
      pos_center_offset=pr.Vector2(-size.x / 2, size.y / 2),
      size=pr.Vector2(12, 15),
    )
    self.rrw = Wheel(
      pos_center_offset=pr.Vector2(size.x / 2, size.y / 2),
      size=pr.Vector2(12, 15),
    )

  def update(self, throttle: bool, brake: bool, steer: float, dt: float):
    self.prev_pos = pr.Vector2(self.pos.x, self.pos.y)
    self.prev_angle = self.angle_rad

    self.update_speed(throttle, brake, dt)
    self.update_steer(steer, dt)
    self.update_movement(dt)

  def update_steer(self, steer: float, dt: float):
    if self.velo > 1:
      self.angle_rad += self.max_steer * steer * self.velo * dt
      self.angle_rad %= loop

    # update direction from angle
    self.direction.x = math.sin(self.angle_rad)
    self.direction.y = -math.cos(self.angle_rad)

  def update_speed(self, throttle: bool, brake: bool, dt: float):
    if throttle and brake:
      self.velo -= self.brake_power * dt
      if self.velo < 0:
        self.velo = 0
    # consider adding another feature when throttle + brake

    elif throttle:
      self.velo += self.engine_power * dt

    elif brake:
      self.velo -= self.brake_power * dt
      if self.velo < 0:
        self.velo = 0

    else:
      self.velo -= self.engine_brake * dt

    if self.velo < 0:
      self.velo = 0

    drag = self.air_resist * self.velo * self.velo
    self.velo -= drag * dt

  def update_movement(self, dt: float):
    self.pos.x += self.direction.x * self.velo * dt
    self.pos.y += self.direction.y * self.velo * dt

  def draw(self, alpha):
    self.render_pos = pr.vector2_lerp(self.prev_pos, self.pos, alpha)

    angle_deg = math.degrees(self.angle_rad)

    # Change to an actual texture
    rec = pr.Rectangle(self.render_pos.x, self.render_pos.y, self.size.x, self.size.y)
    pr.draw_rectangle_pro(
      rec, pr.Vector2(self.size.x / 2, self.size.y / 2), angle_deg, pr.RED
    )
    self.flw.draw(self.render_pos, angle_deg)
    self.frw.draw(self.render_pos, angle_deg)
    self.rlw.draw(self.render_pos, angle_deg)
    self.rrw.draw(self.render_pos, angle_deg)


class Wheel:
  def __init__(self, pos_center_offset: pr.Vector2, size: pr.Vector2):
    self.pos_center_offset = pos_center_offset
    self.temp = 70.0
    self.wheel_angle_offset = 0
    # friction value (or calculate grip with just the temperature)

    self.size = size

  def draw(self, car_pos: pr.Vector2, angle_deg: float):
    angle_rad = math.radians(angle_deg)

    rx = self.pos_center_offset.x * math.cos(
      angle_rad
    ) - self.pos_center_offset.y * math.sin(angle_rad)

    ry = self.pos_center_offset.x * math.sin(
      angle_rad
    ) + self.pos_center_offset.y * math.cos(angle_rad)
    rec = pr.Rectangle(
      car_pos.x + rx,
      car_pos.y + ry,
      self.size.x,
      self.size.y,
    )

    pr.draw_rectangle_pro(
      rec, pr.Vector2(self.size.x / 2, self.size.y / 2), angle_deg, pr.BLACK
    )
