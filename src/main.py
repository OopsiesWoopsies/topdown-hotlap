import pyray as pr

from game.world import World
from render.renderer import Renderer

# from os.path import join

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Top Down Hotlap")

pr.set_target_fps(144)

world = World()
renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT)

fixed_dt = 1.0 / 120.0
accumulator = 0.0

while not pr.window_should_close():
  frame_time = pr.get_frame_time()
  accumulator += frame_time

  while accumulator >= fixed_dt:
    world.update(fixed_dt)
    accumulator -= fixed_dt

  alpha = accumulator / fixed_dt

  pr.begin_drawing()
  pr.clear_background(pr.DARKGRAY)

  renderer.begin_world()
  pr.draw_rectangle(0, 0, 100, 100, pr.WHITE)

  renderer.draw(world, alpha)

  renderer.camera.target = world.car.render_pos
  renderer.camera.rotation = -world.car.angle_deg

  for x in range(-5000, 5000, 100):
    pr.draw_line(x, -5000, x, 5000, pr.GRAY)

  for y in range(-5000, 5000, 100):
    pr.draw_line(-5000, y, 5000, y, pr.GRAY)

  renderer.end_world()

  pr.draw_fps(0, 0)
  pr.end_drawing()
