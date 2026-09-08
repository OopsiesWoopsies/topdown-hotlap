import time
from pathlib import Path

import pyray as pr

from game.car.car_body import Car
from render.car.render_car import RenderCar
from utils.constants import Constants
from utils.layouts import tracks


def main():
  cons = Constants()
  screen_width = cons.SCREEN_WIDTH
  screen_height = cons.SCREEN_HEIGHT
  pr.init_window(screen_width, screen_height, "Track Editor")
  # pr.set_target_fps(144)

  base_cam_zoom = 1 / cons.PPM * 20
  camera = pr.Camera2D(
    (screen_width / 2, screen_height / 2), (0, 0), -90.0, base_cam_zoom
  )
  pos_x = 0.0
  pos_y = 0.0

  track_index = 2

  last_time = time.perf_counter()
  accumulator = 0.0
  fixed_dt = 1 / 144.0

  # Car for reference
  car = Car(cons, (0.0, 0.0), 0, (5.6, 2.0))
  script_dir = Path(__file__).resolve().parent.parent.parent
  car_path = script_dir / "assets" / "imgs" / "car.png"
  car_image = pr.load_image(str(car_path))
  pr.image_rotate(car_image, 90)
  pr.image_resize_nn(
    car_image,
    int(car.size[0] * cons.PPM),
    int(car.size[1] * cons.PPM),
  )
  car_texture = pr.load_texture_from_image(car_image)
  pr.unload_image(car_image)

  render_car = RenderCar(cons, car_texture, car)

  while not pr.window_should_close():
    if pr.is_key_pressed(pr.KEY_F11):
      if not pr.is_window_fullscreen():
        monitor = pr.get_current_monitor()
        FULLSCREEN_WIDTH = pr.get_monitor_width(monitor)
        FULLSCREEN_HEIGHT = pr.get_monitor_height(monitor)
        old_screen_height = screen_height
        screen_width = FULLSCREEN_WIDTH
        screen_height = FULLSCREEN_HEIGHT

        pr.set_window_size(screen_width, screen_height)
        pr.toggle_fullscreen()
        scale = screen_height / old_screen_height
        camera.zoom *= scale
        camera.offset = (screen_width / 2, screen_height / 2)

      else:
        old_screen_height = screen_height
        screen_width = cons.SCREEN_WIDTH
        screen_height = cons.SCREEN_HEIGHT

        pr.toggle_fullscreen()
        pr.set_window_size(screen_width, screen_height)
        scale = screen_height / old_screen_height
        camera.zoom *= scale
        camera.offset = (screen_width / 2, screen_height / 2)

    current_time = time.perf_counter()
    frame_time = min(current_time - last_time, 0.25)
    last_time = current_time
    accumulator += frame_time

    while accumulator >= fixed_dt:
      pos_x, pos_y = control_screen(fixed_dt, camera, (pos_x, pos_y))
      accumulator -= fixed_dt

    pr.begin_drawing()
    pr.clear_background(pr.WHITE)

    pr.begin_mode_2d(camera)
    draw_world(render_car)
    draw_grid(cons, camera, screen_width, screen_height)
    pr.end_mode_2d()

    draw_screen(cons, screen_height, track_index)
    pr.draw_fps(screen_width - 100, 5)
    pr.end_drawing()
  pr.close_window()


def control_screen(dt, camera: pr.Camera2D, pos: tuple[float, float]):
  pos_x, pos_y = pos
  speed = 500

  zoom = 0
  zoom_speed = 0

  if pr.is_key_down(pr.KEY_LEFT_SHIFT):
    speed = 1000
    zoom_speed = 0.5

  dt_speed = speed * dt / camera.zoom
  if pr.is_key_down(pr.KEY_W):
    pos_x += dt_speed
  if pr.is_key_down(pr.KEY_A):
    pos_y -= dt_speed
  if pr.is_key_down(pr.KEY_S):
    pos_x -= dt_speed
  if pr.is_key_down(pr.KEY_D):
    pos_y += dt_speed

  if pr.is_key_down(pr.KEY_MINUS):
    zoom = -0.1 - zoom_speed
  if pr.is_key_down(pr.KEY_EQUAL):
    zoom = 0.1 + zoom_speed

  camera.target = (pos_x, pos_y)
  camera.zoom = camera.zoom + zoom * dt
  camera.zoom = max(0.05, camera.zoom)

  return pos_x, pos_y


def draw_world(render_car: RenderCar):
  render_car.draw_car()


def draw_screen(cons: Constants, screen_height: int, track_index: int):
  rec_width = 350
  pr.draw_rectangle(0, 0, rec_width, screen_height, (0, 0, 0, 180))
  track_amount = len(tracks)

  text = tracks[track_index]["name"]
  half_text_width = pr.measure_text(text, cons.FONT_SIZE) / 2

  pr.draw_text(text, int(rec_width / 2 - half_text_width), 10, cons.FONT_SIZE, pr.WHITE)


def draw_grid(
  cons: Constants, camera: pr.Camera2D, screen_width: int, screen_height: int
):  # 2m x 2m gridbox
  if camera.zoom < 0.05:
    return

  spacing = cons.PPM * 2

  tl = pr.get_screen_to_world_2d((0, 0), camera)
  br = pr.get_screen_to_world_2d((screen_width, screen_height), camera)

  start_x = int(round(tl.x) // spacing) * spacing
  end_x = int(round(br.x) // spacing) * spacing + spacing

  start_y = int(round(tl.y) // spacing) * spacing
  end_y = int(round(br.y) // spacing) * spacing + spacing

  bound_top = int(tl.y)
  bound_bottom = int(br.y)
  bound_left = int(tl.x)
  bound_right = int(br.x)

  for x in range(end_x, start_x, spacing):
    pr.draw_line(x, bound_top, x, bound_bottom, pr.BLACK)

  for y in range(start_y, end_y, spacing):
    pr.draw_line(bound_left, y, bound_right, y, pr.BLACK)


if __name__ == "__main__":
  main()
