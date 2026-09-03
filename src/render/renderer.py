from os.path import join

import pyray as pr

from game.constants import Constants
from game.world import Car, PhysicsTrack, World
from input.control import Control
from render.render_controls import RenderControls
from render.render_track import RenderTrack


class Renderer:
  def __init__(
    self, cons: Constants, world: World, screen_width: int, screen_height: int
  ):
    car = world.car
    # Camera
    self.cons = cons
    self.base_cam_zoom = 1 / cons.PPM * 20
    self.camera = pr.Camera2D(
      (screen_width / 2, screen_height * 0.7), (0, 0), 0, self.base_cam_zoom
    )

    # Car
    self.car_path = join("assets", "imgs", "car.png")
    car_image = pr.load_image(self.car_path)
    pr.image_rotate(car_image, 90)
    pr.image_resize_nn(
      car_image,
      int(car.size[0] * cons.PPM),
      int(car.size[1] * cons.PPM),
    )
    self.car_texture = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

    # Track
    self.render_track = RenderTrack()
    self.create_track_chunks(world.track)

    # Controls
    self.render_ctrls = RenderControls(screen_width, screen_height)

  def update_screen(
    self, car: Car, screen_width: int, screen_height: int, scale: float
  ):
    self.update_textures(car)
    self.camera.offset = (screen_width / 2, screen_height * 0.7)
    self.base_cam_zoom = self.base_cam_zoom * scale
    self.render_ctrls.update_draw_positions(screen_width, screen_height)

  def update_textures(self, car: Car):
    car_image = pr.load_image(self.car_path)
    pr.image_rotate(car_image, 90)
    pr.image_resize_nn(
      car_image,
      int(car.size[0] * self.cons.PPM),
      int(car.size[1] * self.cons.PPM),
    )

    self.car_texture = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

  def begin_world(self):
    pr.begin_mode_2d(self.camera)

  def end_world(self):
    pr.end_mode_2d()

  def create_track_chunks(self, track: PhysicsTrack):
    self.render_track.render_chunks(
      self.cons,
      track.center_pts,
      track.left_bound_pts,
      track.right_bound_pts,
      track.sector_lines,
      track.finish_line,
    )

  def draw_world(self, world: World):
    self.render_track.draw(self.camera)
    world.car.draw_car(self.car_texture)

  def draw_screen(
    self, ctrls: Control, world: World, screen_width: int, screen_height: int
  ):
    world.car.draw_data(screen_width, screen_height)
    self.render_ctrls.draw(world.car.steer_angle, ctrls.get_static_inputs())
    world.timer.draw_timer(10, 10)

  def close(self):
    self.render_track.close()
    pr.unload_texture(self.car_texture)
