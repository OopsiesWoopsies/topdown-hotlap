import time
from pathlib import Path

import pyray as pr

from game.car.car_body import Car
from render.car.render_car import RenderCar
from utils.constants import Constants


def main():
  cons = Constants()
  pr.init_window(cons.SCREEN_WIDTH, cons.SCREEN_HEIGHT, "Track Editor")
  pr.set_target_fps(144)

  base_cam_zoom = 1 / cons.PPM * 20
  camera = pr.Camera2D(
    (cons.SCREEN_WIDTH, cons.SCREEN_HEIGHT), (0, 0), -90.0, base_cam_zoom
  )
  pos_x = 0.0
  pos_y = 0.0

  last_time = time.perf_counter()
  accumulator = 0.0
  fixed_dt = 1 / 144.0

  # Car for reference
  car = Car(cons, (0.0, 0.0), 0, (5.6, 2.0))
  script_dir = Path(__file__).parent
  car_path = script_dir.parent / "assets" / "imgs" / "car.png"
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
    draw_grid(cons)
    pr.end_mode_2d()

    draw_screen()
    pr.draw_fps(cons.SCREEN_WIDTH - 100, 5)
    pr.end_drawing()
  pr.close_window()


def control_screen(dt, camera: pr.Camera2D, pos: tuple[float, float]):
  pos_x, pos_y = pos
  speed = 750

  zoom = 0
  zoom_speed = 0

  if pr.is_key_down(pr.KEY_LEFT_SHIFT):
    speed = 1500
    zoom_speed = 0.5

  dt_speed = speed * dt
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

  return pos_x, pos_y


def draw_world(render_car: RenderCar):
  render_car.draw_car()


def draw_screen():
  pass


def draw_grid(cons: Constants):  # 2m x 2m gridbox
  for x in range(-100000, 100000, cons.PPM * 2):
    pr.draw_line(x, -100000, x, 100000, pr.BLACK)

  for y in range(-100000, 100000, cons.PPM * 2):
    pr.draw_line(-100000, y, 100000, y, pr.BLACK)


if __name__ == "__main__":
  main()
