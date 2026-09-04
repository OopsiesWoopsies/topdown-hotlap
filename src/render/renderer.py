import math
from os.path import join

import pyray as pr

from game.constants import Constants
from game.world import PhysicsTrack, World
from input.control import Control
from render.car.render_car import RenderCar
from render.car.render_car_data import RenderCarData
from render.car.render_controls import RenderControls
from render.render_track import RenderTrack

DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720


class Renderer:
  def __init__(
    self,
    cons: Constants,
    ctrls: Control,
    world: World,
  ):
    self.screen_width = DEFAULT_SCREEN_WIDTH
    self.screen_height = DEFAULT_SCREEN_HEIGHT
    pr.init_window(self.screen_width, self.screen_height, "Top Down Hotlap")
    pr.set_target_fps(144)

    self.world = world
    self.ctrls = ctrls
    car = world.car
    # Camera
    self.cons = cons
    self.base_cam_zoom = 1 / cons.PPM * 20
    self.camera = pr.Camera2D(
      (self.screen_width / 2, self.screen_height * 0.7), (0, 0), 0, self.base_cam_zoom
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
    car_texture = pr.load_texture_from_image(car_image)
    pr.unload_image(car_image)

    self.render_car = RenderCar(cons, car_texture, car)
    self.render_car_data = RenderCarData(car, self.screen_width, self.screen_height)

    # Track
    self.render_track = RenderTrack()
    self.create_track_chunks(world.track)

    # Controls
    self.render_ctrls = RenderControls(self.screen_width, self.screen_height)

  def render_screen(self, alpha, frame_time) -> bool:
    if pr.is_key_pressed(pr.KEY_F11):
      if not pr.is_window_fullscreen():
        monitor = pr.get_current_monitor()
        FULLSCREEN_WIDTH = pr.get_monitor_width(monitor)
        FULLSCREEN_HEIGHT = pr.get_monitor_height(monitor)
        old_screen_height = self.screen_height
        self.screen_width = FULLSCREEN_WIDTH
        self.screen_height = FULLSCREEN_HEIGHT

        pr.set_window_size(self.screen_width, self.screen_height)
        pr.toggle_fullscreen()
        scale = self.screen_height / old_screen_height
        self.update_screen(scale)
      else:
        old_screen_height = self.screen_height
        self.screen_width = DEFAULT_SCREEN_WIDTH
        self.screen_height = DEFAULT_SCREEN_HEIGHT

        pr.toggle_fullscreen()
        pr.set_window_size(self.screen_width, self.screen_height)
        scale = self.screen_height / old_screen_height
        self.update_screen(scale)

    # Determine camera stats
    self.render_car.calculate_render_state(alpha)
    offset_distance = self.world.car.speed * 0.9
    render_angle = self.render_car.render_angle_rad
    render_pos = self.render_car.render_car_pos
    offset_x = math.cos(render_angle) * offset_distance
    offset_y = math.sin(render_angle) * offset_distance
    angle_deg = math.degrees(self.render_car.render_angle_rad) + 90

    self.camera.rotation = -angle_deg
    if pr.is_key_down(pr.KEY_C):
      target_zoom = self.base_cam_zoom * 0.35
    elif pr.is_key_down(pr.KEY_SPACE):
      target_zoom = self.base_cam_zoom * 0.1
    elif pr.is_key_down(pr.KEY_V):
      target_zoom = self.base_cam_zoom * 4
    else:
      target_zoom = max(
        self.base_cam_zoom - (self.base_cam_zoom * self.world.car.speed * 0.0099),
        0.2 * self.base_cam_zoom,
      )
    self.camera.zoom = (
      self.camera.zoom + (target_zoom - self.camera.zoom) * frame_time * 5
    )
    self.camera.target = (render_pos[0] + offset_x, render_pos[1] + offset_y)

    # Drawing world
    pr.begin_drawing()
    pr.clear_background(pr.DARKGREEN)

    if pr.is_key_pressed(pr.KEY_R):
      world_coords = pr.vector2_scale(
        pr.get_screen_to_world_2d(pr.get_mouse_position(), self.camera),
        1 / self.cons.PPM,
      )
      print(world_coords.x, world_coords.y)

    # Drawing in world
    self.begin_world()
    self.draw_world()
    # draw_grid()  # --DEBUG-- #
    self.end_world()

    # Drawing on screen
    self.draw_screen(self.ctrls)
    # draw_debug(self.world)  # --DEBUG-- #

    pr.draw_fps(self.screen_width - 100, 0)
    pr.end_drawing()

    return pr.window_should_close()

  def update_screen(self, scale: float):
    self.render_ctrls.update_draw_positions(self.screen_width, self.screen_height)
    self.render_car_data.update_scale(self.screen_width, self.screen_height)
    self.camera.offset = (self.screen_width / 2, self.screen_height * 0.7)
    self.base_cam_zoom = self.base_cam_zoom * scale

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

  def draw_world(self):
    self.render_track.draw(self.camera)
    self.render_car.draw_car()

  def draw_screen(self, ctrls: Control):
    self.render_car_data.draw()
    self.render_ctrls.draw(self.world.car.steer_angle, ctrls.get_static_inputs())
    self.render_car_data.update_data()
    self.render_car_data.draw()
    self.world.timer.draw_timer(10, 10)

  def close(self):
    self.render_track.close()
    self.render_car.close()

    pr.close_window()


def draw_grid():
  for x in range(-100000, 100000, 100):
    pr.draw_line(x, -100000, x, 100000, pr.BLACK)

  for y in range(-100000, 100000, 100):
    pr.draw_line(-100000, y, 100000, y, pr.BLACK)


def draw_debug(world: World):
  debug_vals = world.car.get_debug_vals()
  print(debug_vals)
  text1 = f"Accel: {debug_vals['Accel']}\nLocal Accel: {debug_vals['LAccel']}\nVelo: {debug_vals['Velo']}\nLocal Velo: {debug_vals['LVelo']}\n"
  text2 = f"Speed: {debug_vals['Speed']}\nDragF: {debug_vals['DragF']}\n"
  text3 = f"DriveT: {debug_vals['DriveT']}\nBrakeT: {debug_vals['BrakeT']}\n"
  text4 = f"FLTire: {debug_vals['FLTire']}\nFRTire: {debug_vals['FRTire']}\nRLTire: {debug_vals['RLTire']}\nRRTire: {debug_vals['RRTire']}\n"
  text5 = f"EngRPM: {debug_vals['EngRPM']}\nGear: {debug_vals['Gear']}\n"
  text6 = f"YawRate: {debug_vals['YawRate']}\n"
  text = text1 + text2 + text3 + text5 + text6
  pr.draw_text(text, 5, 90, 20, pr.BLACK)
  pr.draw_text(text4, 5, 380, 15, pr.BLACK)
