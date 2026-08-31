import math

import pyray as pr

from game.constants import Constants
from game.world import World
from render.renderer import Renderer

DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720

screen_width = DEFAULT_SCREEN_WIDTH
screen_height = DEFAULT_SCREEN_HEIGHT

pr.init_window(screen_width, screen_height, "Top Down Hotlap")

pr.set_target_fps(144)

cons = Constants()
world = World(cons)
renderer = Renderer(screen_width, screen_height, world.car, cons)

fixed_dt = 1.0 / 144.0
accumulator = 0.0

while not pr.window_should_close():
  if pr.is_key_pressed(pr.KEY_F11):
    if not pr.is_window_fullscreen():
      monitor = pr.get_current_monitor()
      FULLSCREEN_WIDTH = pr.get_monitor_width(monitor)
      FULLSCREEN_HEIGHT = pr.get_monitor_height(monitor)

      pr.set_window_size(FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT)
      pr.toggle_fullscreen()
      cons.update_PPM(round(FULLSCREEN_HEIGHT / screen_height * cons.PPM))
      world.track.create_track()
      renderer.update_textures(world.car, cons)
      renderer.camera.offset = pr.Vector2(FULLSCREEN_WIDTH / 2, FULLSCREEN_HEIGHT * 0.7)
      screen_width = FULLSCREEN_WIDTH
      screen_height = FULLSCREEN_HEIGHT
    else:
      screen_width = DEFAULT_SCREEN_WIDTH
      screen_height = DEFAULT_SCREEN_HEIGHT

      pr.toggle_fullscreen()
      pr.set_window_size(screen_width, screen_height)
      cons.update_PPM(round(screen_height / FULLSCREEN_HEIGHT * cons.PPM))
      world.track.create_track()
      renderer.update_textures(world.car, cons)
      renderer.camera.offset = pr.Vector2(screen_width / 2, screen_height * 0.7)

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
  if pr.is_key_down(pr.KEY_C):
    target_zoom = 0.3
  elif pr.is_key_down(pr.KEY_SPACE):
    target_zoom = 0.08
  elif pr.is_key_down(pr.KEY_V):
    target_zoom = 2.5
  else:
    target_zoom = max(1.0 - (world.car.speed * 0.0099), 0.5)
  renderer.camera.zoom = (
    renderer.camera.zoom + (target_zoom - renderer.camera.zoom) * frame_time * 5
  )
  renderer.camera.target = (render_pos[0] + offset_x, render_pos[1] + offset_y)

  # Drawing world
  pr.begin_drawing()
  pr.clear_background(pr.DARKGREEN)

  if pr.is_key_pressed(pr.KEY_R):
    world_coords = pr.vector2_scale(
      pr.get_screen_to_world_2d(pr.get_mouse_position(), renderer.camera), 1 / 30
    )
    print(world_coords.x, world_coords.y)

  renderer.begin_world()
  renderer.draw_world(world)

  # Grid (temp)
  # for x in range(-100000, 100000, 100):
  #   pr.draw_line(x, -100000, x, 100000, pr.BLACK)

  # for y in range(-100000, 100000, 100):
  #   pr.draw_line(-100000, y, 100000, y, pr.BLACK)

  renderer.end_world()

  # Drawing on screen
  renderer.draw_screen(world, screen_width, screen_height)

  debug_vals = world.car.get_debug_vals()
  # print(debug_vals)
  text1 = f"Accel: {debug_vals['Accel']}\nLocal Accel: {debug_vals['LAccel']}\nVelo: {debug_vals['Velo']}\nLocal Velo: {debug_vals['LVelo']}\n"
  text2 = f"Speed: {debug_vals['Speed']}\nDragF: {debug_vals['DragF']}\n"
  text3 = f"DriveT: {debug_vals['DriveT']}\nBrakeT: {debug_vals['BrakeT']}\n"
  text4 = f"FLTire: {debug_vals['FLTire']}\nFRTire: {debug_vals['FRTire']}\nRLTire: {debug_vals['RLTire']}\nRRTire: {debug_vals['RRTire']}\n"
  text5 = f"EngRPM: {debug_vals['EngRPM']}\nGear: {debug_vals['Gear']}\n"
  text6 = f"YawRate: {debug_vals['YawRate']}\n"
  # text = text1 + text2 + text3 + text5 + text6
  # pr.draw_text(text, 5, 90, 20, pr.BLACK)
  # pr.draw_text(text4, 5, 380, 15, pr.BLACK)

  pr.draw_fps(0, 0)
  world.timer.draw_timer(5, 10)
  pr.end_drawing()

world.close()
renderer.close()
pr.close_window()
