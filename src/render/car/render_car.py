import math

import pyray as pr

from game.car.axle import Axle
from game.car.car_body import Car
from game.car.tire import Tire
from game.constants import Constants


class RenderCar:
  def __init__(self, cons: Constants, car_tex: pr.Texture, car: Car):
    self.cons = cons
    self.car_tex = car_tex
    self.car = car

    self.interp_car_pos = car.pos
    self.render_car_pos = (car.pos[0] * cons.PPM, car.pos[1] * cons.PPM)
    self.render_angle_rad = self.car.angle_rad

  def calculate_render_state(self, alpha: float):
    interp_pos_x = (
      self.car.prev_pos[0] + (self.car.pos[0] - self.car.prev_pos[0]) * alpha
    )
    interp_pos_y = (
      self.car.prev_pos[1] + (self.car.pos[1] - self.car.prev_pos[1]) * alpha
    )
    self.render_angle_rad = (
      self.car.prev_angle_rad + (self.car.angle_rad - self.car.prev_angle_rad) * alpha
    )
    self.interp_car_pos = (interp_pos_x, interp_pos_y)

  def draw_car(self):
    interp_pos_x, interp_pos_y = self.interp_car_pos
    render_pos_x = interp_pos_x * self.cons.PPM
    render_pos_y = interp_pos_y * self.cons.PPM

    self.render_car_pos = (render_pos_x, render_pos_y)

    angle_deg = math.degrees(self.render_angle_rad)
    size_draw_x = self.car.size[0] * self.cons.PPM
    size_draw_y = self.car.size[1] * self.cons.PPM
    cg_x, cg_y = self.car.cg
    cg_draw = (
      (size_draw_x / 2) + (cg_x * self.cons.PPM),
      (size_draw_y / 2) + (cg_y * self.cons.PPM),
    )

    src_rec = pr.Rectangle(0.0, 0.0, self.car_tex.width, self.car_tex.height)
    dest_rec = pr.Rectangle(render_pos_x, render_pos_y, size_draw_x, size_draw_y)
    pr.draw_texture_pro(self.car_tex, src_rec, dest_rec, cg_draw, angle_deg, pr.WHITE)

    self.draw_axle(self.car.rear_axle, 0)
    self.draw_axle(self.car.front_axle, self.car.steer_angle)

  def draw_axle(self, axle: Axle, steer_deg: float):
    forward_x = math.cos(self.render_angle_rad)
    forward_y = math.sin(self.render_angle_rad)
    interp_pos_x, interp_pos_y = self.interp_car_pos

    render_pos_x = (interp_pos_x + forward_x * axle.distance_to_cg) * self.cons.PPM
    render_pos_y = (interp_pos_y + forward_y * axle.distance_to_cg) * self.cons.PPM
    render_pos = (render_pos_x, render_pos_y)

    axle_width_draw = axle.axle_width * self.cons.PPM
    track_width_draw = axle.track_width * self.cons.PPM

    rec = pr.Rectangle(render_pos_x, render_pos_y, axle_width_draw, track_width_draw)
    origin = (axle_width_draw / 2, track_width_draw / 2)

    angle_deg = math.degrees(self.render_angle_rad)

    pr.draw_rectangle_pro(rec, origin, angle_deg, pr.BLACK)

    self.draw_tire(
      axle.left_tire, -1, render_pos, angle_deg, steer_deg, axle.half_track_width
    )
    self.draw_tire(
      axle.right_tire, 1, render_pos, angle_deg, steer_deg, axle.half_track_width
    )

  def draw_tire(
    self,
    tire: Tire,
    sign: int,
    axle_render_pos: tuple[float, float],
    angle_deg: float,
    steer_deg: float,
    half_track_width: float,
  ):
    right_x = -math.sin(self.render_angle_rad)
    right_y = math.cos(self.render_angle_rad)

    render_pos_x = (
      axle_render_pos[0] + right_x * half_track_width * sign * self.cons.PPM
    )
    render_pos_y = (
      axle_render_pos[1] + right_y * half_track_width * sign * self.cons.PPM
    )

    diameter_draw = tire.radius * 2 * self.cons.PPM
    width_draw = tire.width * self.cons.PPM

    rec = pr.Rectangle(render_pos_x, render_pos_y, diameter_draw, width_draw)
    origin = (diameter_draw / 2, width_draw / 2)

    pr.draw_rectangle_pro(rec, origin, angle_deg + steer_deg, pr.BLACK)

  def close(self):
    pr.unload_texture(self.car_tex)