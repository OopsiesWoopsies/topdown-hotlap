import math

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
  angle_deg = math.degrees(world.car.angle_rad) + 90
  renderer.camera.rotation = -angle_deg

  for x in range(-50000, 50000, 100):
    pr.draw_line(x, -50000, x, 50000, pr.GRAY)

  for y in range(-50000, 50000, 100):
    pr.draw_line(-50000, y, 50000, y, pr.GRAY)

  renderer.end_world()

  text = f"{round(world.car.render_pos.x, 3)}\n{round(world.car.render_pos.y, 3)}\n{round(pr.vector2_length(world.car.velo) * 3600 / 1000, 3)} km/h"
  pr.draw_text(text, 5, 30, 20, pr.BLACK)

  debug_vals = world.car.get_debug_vals()
  # print(debug_vals)
  text1 = f"Accel: {debug_vals['Accel']}\nLocal Accel: {debug_vals['LAccel']}\nVelo: {debug_vals['Velo']}\nLocal Velo: {debug_vals['LVelo']}\n"
  text2 = f"Speed: {debug_vals['Speed']}\nLongF: {debug_vals['LongF']}\nTractionF: {debug_vals['TractionF']}\nDragF: {debug_vals['DragF']}\n"
  text3 = f"DriveT: {debug_vals['DriveT']}\nBrakeT: {debug_vals['BrakeT']}\n"
  text4 = f"FLTire: {debug_vals['FLTire']}\nFRTire: {debug_vals['FRTire']}\nRLTire: {debug_vals['RLTire']}\nRRTire: {debug_vals['RRTire']}\n"
  text5 = f"EngRPM: {debug_vals['EngRPM']}\nGear: {debug_vals['Gear']}"
  text = text1 + text2 + text3 + text4 + text5
  pr.draw_text(text, 5, 90, 20, pr.BLACK)

  pr.draw_fps(0, 0)
  pr.end_drawing()
