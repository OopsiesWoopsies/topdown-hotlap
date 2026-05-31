import math

import pyray as pr

loop = 2 * math.pi


class Car:
  def __init__(self, pos: pr.Vector2, angle_deg: float, size: pr.Vector2):
    self.pos = pos
    self.render_pos = pos
    self.prev_pos = pr.Vector2(self.pos.x, self.pos.y)

    self.angle_rad = math.radians(angle_deg)
    self.angle_deg = angle_deg
    self.render_angle = angle_deg
    self.prev_angle = self.angle_rad
    self.wheel_base = 60

    self.speed = 0
    self.velo = pr.Vector2(0, 0)
    self.angular_velo = 0.0
    self.size = size
    self.forward = pr.Vector2(math.sin(self.angle_rad), -math.cos(self.angle_rad))

    self.max_steer_angle = math.radians(20)
    self.steer_angle = 0.0

    self.brake_power = 2000
    self.engine_power = 1000
    self.engine_brake = 100

    self.air_resist = 0.0005

    self.fl = Wheel(
      pos_center_offset=pr.Vector2(-size.x / 2, -size.y / 2),
      size=pr.Vector2(8, 15),
    )
    self.fr = Wheel(
      pos_center_offset=pr.Vector2(size.x / 2, -size.y / 2),
      size=pr.Vector2(8, 15),
    )
    self.rl = Wheel(
      pos_center_offset=pr.Vector2(-size.x / 2, size.y / 2),
      size=pr.Vector2(12, 15),
    )
    self.rr = Wheel(
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
    self.steer_angle = self.max_steer_angle * steer

    yaw_rate = (self.speed / self.wheel_base) * math.tan(self.steer_angle)

    self.angular_velo = yaw_rate
    self.angle_rad += yaw_rate * dt
    self.angle_rad %= loop

    # update forward vector from angle
    self.forward = pr.Vector2(math.sin(self.angle_rad), -math.cos(self.angle_rad))

  def update_speed(self, throttle: bool, brake: bool, dt: float):
    if throttle and brake:
      if self.speed > 0:
        brake_amount = self.brake_power * dt

        if brake_amount > self.speed:
          self.velo = pr.Vector2(0, 0)
        else:
          dir = pr.vector2_scale(self.velo, 1.0 / self.speed)
          self.velo.x -= dir.x * brake_amount
          self.velo.y -= dir.y * brake_amount
    # consider adding another feature when throttle + brake

    elif throttle:
      self.velo.x += self.forward.x * self.engine_power * dt
      self.velo.y += self.forward.y * self.engine_power * dt

    elif self.speed > 0:
      if brake:
        brake_amount = self.brake_power * dt

        if brake_amount > self.speed:
          self.velo = pr.Vector2(0, 0)
        else:
          dir = pr.vector2_scale(self.velo, 1.0 / self.speed)
          self.velo.x -= dir.x * brake_amount
          self.velo.y -= dir.y * brake_amount

      else:
        brake_amount = self.engine_brake * dt

        if brake_amount > self.speed:
          self.velo = pr.Vector2(0, 0)
        else:
          dir = pr.vector2_scale(self.velo, 1.0 / self.speed)
          self.velo.x -= dir.x * brake_amount
          self.velo.y -= dir.y * brake_amount

    self.speed = pr.vector2_length(self.velo)

    if self.speed > 0:
      drag = self.air_resist * self.speed * self.speed
      dir = pr.vector2_scale(self.velo, 1.0 / self.speed)
      self.velo.x -= dir.x * drag * dt
      self.velo.y -= dir.y * drag * dt

    self.speed = pr.vector2_length(self.velo)

  def update_movement(self, dt: float):
    self.pos.x += self.velo.x * dt
    self.pos.y += self.velo.y * dt

  def draw(self, alpha):
    print(self.speed)
    

    self.render_pos = pr.vector2_lerp(self.prev_pos, self.pos, alpha)
    self.render_angle = self.lerp_angle(self.prev_angle, self.angle_rad, alpha)

    self.angle_deg = math.degrees(self.render_angle)

    # Change to an actual texture
    rec = pr.Rectangle(self.render_pos.x, self.render_pos.y, self.size.x, self.size.y)
    pr.draw_rectangle_pro(
      rec, pr.Vector2(self.size.x / 2, self.size.y / 2), self.angle_deg, pr.RED
    )
    self.fl.draw(self.render_pos, self.angle_deg)
    self.fr.draw(self.render_pos, self.angle_deg)
    self.rl.draw(self.render_pos, self.angle_deg)
    self.rr.draw(self.render_pos, self.angle_deg)

  def lerp_angle(self, a: float, b: float, t: float):
    diff = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + diff * t


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
