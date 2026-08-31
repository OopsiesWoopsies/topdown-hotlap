from os.path import join

import pyray as pr

from game.constants import Constants
from game.world import Car, World
from input.control import Control


class Renderer:
  def __init__(self, screen_width: int, screen_height: int, car: Car, cons: Constants):
    self.camera = pr.Camera2D((screen_width / 2, screen_height * 0.7), (0, 0), 0, 1.0)

    self.car_path = join("assets", "imgs", "car.png")
    car_image = pr.load_image(self.car_path)
    pr.image_rotate(car_image, 90)
    pr.image_resize_nn(
      car_image,
      int(car.size[0] * cons.PPM),
      int(car.size[1] * cons.PPM),
    )

    self.car_texture: pr.Texture2D = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

  def update_textures(self, car: Car, cons: Constants):
    car_image = pr.load_image(self.car_path)
    pr.image_rotate(car_image, 90)
    pr.image_resize_nn(
      car_image,
      int(car.size[0] * cons.PPM),
      int(car.size[1] * cons.PPM),
    )

    self.car_texture: pr.Texture2D = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

  def begin_world(self):
    pr.begin_mode_2d(self.camera)

  def end_world(self):
    pr.end_mode_2d()

  def draw_world(self, world: World):
    world.track.draw()
    world.car.draw_car(self.car_texture)

  def draw_screen(
    self, ctrls: Control, world: World, screen_width: int, screen_height: int
  ):
    world.car.draw_data(screen_width, screen_height)
    ctrls.draw(world.car.steer_angle)

  def close(self):
    pr.unload_texture(self.car_texture)
