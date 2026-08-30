from os.path import join

import pyray as pr

from game.constants import PIXELS_PER_METER
from game.world import Car, World


class Renderer:
  def __init__(self, screen_width: int, screen_height: int, car: Car):
    self.camera = pr.Camera2D((screen_width / 2, screen_height * 0.7), (0, 0), 0, 1.0)

    path = join("assets", "imgs", "car.png")
    car_image = pr.load_image(path)
    pr.image_rotate(car_image, 90)
    pr.image_resize_nn(
      car_image,
      int(car.size[0] * PIXELS_PER_METER),
      int(car.size[1] * PIXELS_PER_METER),
    )

    self.car_texture: pr.Texture2D = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

  def begin_world(self):
    pr.begin_mode_2d(self.camera)

  def end_world(self):
    pr.end_mode_2d()

  def draw(self, world: World):
    world.track.draw()
    world.car.draw_car(self.car_texture)

  def close(self):
    pr.unload_texture(self.car_texture)
