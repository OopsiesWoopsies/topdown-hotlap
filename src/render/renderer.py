import pyray as pr

from game.world import World


class Renderer:
  def __init__(self, screen_width: int, screen_height: int):
    self.camera = pr.Camera2D(
      pr.Vector2(screen_width / 2, screen_height * 0.7), pr.Vector2(0, 0), 0, 1.0
    )

  def begin_world(self):
    pr.begin_mode_2d(self.camera)

  def end_world(self):
    pr.end_mode_2d()

  def draw(self, world: World, alpha: float):
    world.track.draw()
    world.car.draw_car(alpha)
