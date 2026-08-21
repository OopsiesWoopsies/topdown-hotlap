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

fixed_dt = 1.0 / 144.0
accumulator = 0.0

while not pr.window_should_close():
  # Static delta time
  frame_time = min(pr.get_frame_time(), 0.25)
  accumulator += frame_time

  while accumulator >= fixed_dt:
    world.update(fixed_dt)
    accumulator -= fixed_dt

  alpha = accumulator / fixed_dt

  # Determine camera stats
  world.car.calculate_render_state(alpha)
  offset_distance = world.car.speed * 0.9
  render_angle = world.car.render_angle_rad
  render_pos = world.car.render_pos
  offset_x = math.cos(render_angle) * offset_distance
  offset_y = math.sin(render_angle) * offset_distance
  angle_deg = math.degrees(world.car.render_angle_rad) + 90

  renderer.camera.rotation = -angle_deg
  target_zoom = max(1.0 - (world.car.speed * 0.0099), 0.5)
  renderer.camera.zoom = pr.lerp(renderer.camera.zoom, target_zoom, frame_time * 5)
  renderer.camera.target = pr.Vector2(render_pos.x + offset_x, render_pos.y + offset_y)

  # Drawing world
  pr.begin_drawing()
  pr.clear_background(pr.DARKGREEN)

  renderer.begin_world()
  renderer.draw(world)

  # Grid (temp)
  for x in range(-100000, 100000, 100):
    pr.draw_line(x, -100000, x, 100000, pr.BLACK)

  for y in range(-100000, 100000, 100):
    pr.draw_line(-100000, y, 100000, y, pr.BLACK)

  renderer.end_world()

  # Drawing on screen
  world.car.draw_data(SCREEN_WIDTH, SCREEN_HEIGHT)
  world.controls.draw(world.car.steer_angle)

  # text = f"{round(world.car.render_pos.x, 3)}\n{round(world.car.render_pos.y, 3)}\n{round(pr.vector2_length(world.car.velo) * 3600 / 1000, 3)} km/h"
  # pr.draw_text(text, 5, 30, 20, pr.BLACK)

  debug_vals = world.car.get_debug_vals()
  # print(debug_vals)
  text1 = f"Accel: {debug_vals['Accel']}\nLocal Accel: {debug_vals['LAccel']}\nVelo: {debug_vals['Velo']}\nLocal Velo: {debug_vals['LVelo']}\n"
  text2 = f"Speed: {debug_vals['Speed']}\nDragF: {debug_vals['DragF']}\n"
  text3 = f"DriveT: {debug_vals['DriveT']}\nBrakeT: {debug_vals['BrakeT']}\n"
  text4 = f"FLTire: {debug_vals['FLTire']}\nFRTire: {debug_vals['FRTire']}\nRLTire: {debug_vals['RLTire']}\nRRTire: {debug_vals['RRTire']}\n"
  text5 = f"EngRPM: {debug_vals['EngRPM']}\nGear: {debug_vals['Gear']}\n"
  text6 = f"YawRate: {debug_vals['YawRate']}\n"
  text = text1 + text2 + text3 + text5 + text6
  # pr.draw_text(text, 5, 90, 20, pr.BLACK)
  # pr.draw_text(text4, 5, 380, 15, pr.BLACK)

  pr.draw_fps(0, 0)
  world.timer.draw_timer(5, 10)
  pr.end_drawing()

pr.close_window()
