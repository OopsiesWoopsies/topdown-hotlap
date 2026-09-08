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

  page = 0  # 0-2 (inclusive, respectively featuring track selection / make new track, editing track, naming track)
  screen_mouse_point = pr.Vector2(0, 0)
  left_click = False
  check_mouse_point = False

  track_index = 2
  sidebar = pr.Rectangle(0, 0, 350, screen_height)

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

  draw_dict = create_buts(cons, sidebar, screen_width, screen_height)

  while not pr.window_should_close():
    # Toggle fullscreen
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
        sidebar = pr.Rectangle(0, 0, 350, screen_height)
        draw_dict = create_buts(cons, sidebar, screen_width, screen_height)
      else:
        old_screen_height = screen_height
        screen_width = cons.SCREEN_WIDTH
        screen_height = cons.SCREEN_HEIGHT

        pr.toggle_fullscreen()
        pr.set_window_size(screen_width, screen_height)
        scale = screen_height / old_screen_height
        camera.zoom *= scale
        camera.offset = (screen_width / 2, screen_height / 2)
        sidebar = pr.Rectangle(0, 0, 350, screen_height)
        draw_dict = create_buts(cons, sidebar, screen_width, screen_height)

    # Static dt
    current_time = time.perf_counter()
    frame_time = min(current_time - last_time, 0.25)
    last_time = current_time
    accumulator += frame_time

    while accumulator >= fixed_dt:
      pos_x, pos_y = control_screen(fixed_dt, camera, (pos_x, pos_y))
      accumulator -= fixed_dt

    # Clicking
    if left_click and pr.is_mouse_button_up(pr.MOUSE_LEFT_BUTTON):
      screen_mouse_point = pr.get_mouse_position()
      left_click = False
      check_mouse_point = True
    elif pr.is_mouse_button_down(pr.MOUSE_LEFT_BUTTON):
      left_click = True

    # Drawing
    pr.begin_drawing()
    pr.clear_background(pr.WHITE)

    pr.begin_mode_2d(camera)
    draw_world(camera, render_car, screen_mouse_point, check_mouse_point, sidebar)
    draw_grid(cons, camera, screen_width, screen_height)
    pr.end_mode_2d()

    page, track_index = draw_screen(
      cons,
      screen_mouse_point,
      check_mouse_point,
      draw_dict,
      sidebar,
      screen_height,
      page,
      track_index,
    )
    pr.draw_fps(screen_width - 100, 5)
    pr.end_drawing()

    check_mouse_point = False
  pr.close_window()


def draw_world(
  camera: pr.Camera2D,
  render_car: RenderCar,
  screen_mouse_point: pr.Vector2,
  check_mouse_point: bool,
  sidebar: pr.Rectangle,
):
  render_car.draw_car()

  if pr.check_collision_point_rec(screen_mouse_point, sidebar):
    return
  elif check_mouse_point:
    world_point = pr.get_world_to_screen_2d(screen_mouse_point, camera)
    print(world_point.x, world_point.y)


def draw_screen(
  cons: Constants,
  screen_mouse_point: pr.Vector2,
  check_mouse_point: bool,
  draw_dict: dict[int, dict[str, any]],
  sidebar: pr.Rectangle,
  screen_height: int,
  page: int,
  track_index: int,
) -> int:
  font = pr.get_font_default()
  rec_width = sidebar.width
  pr.draw_rectangle_pro(sidebar, (0, 0), 0.0, (0, 0, 0, 180))

  track_amount = len(tracks)
  but_arr = draw_dict[page]["buts"]
  texts = draw_dict[page]["texts"]
  text_arr = texts["strings"]
  text_pos_arr = texts["pos"]
  actions = draw_dict[page]["actions"]
  len_but = len(but_arr)

  hovering = False

  match page:
    case 0:
      for i in range(len_but):
        rec: pr.Rectangle = but_arr[i]
        text: str = text_arr[i]

        if pr.check_collision_point_rec(pr.get_mouse_position(), rec):
          hovering = True

        if check_mouse_point and pr.check_collision_point_rec(screen_mouse_point, rec):
          match actions[i]:
            case "page2":
              page = 1
            case "prev_track":
              track_index = (track_index - 1) % track_amount
            case "next_track":
              track_index = (track_index + 1) % track_amount

        x, y = text_pos_arr[i]
        pr.draw_rectangle_pro(rec, (0, 0), 0.0, pr.LIGHTGRAY)
        pr.draw_text_ex(
          font, text, pr.Vector2(int(x), int(y)), cons.FONT_SIZE, 1, pr.BLACK
        )

      text = tracks[track_index]["name"]
      half_text_width = pr.measure_text(text, cons.FONT_SIZE) / 2
      pr.draw_text(
        text,
        int(rec_width / 2 - half_text_width),
        int(screen_height / 3),
        cons.FONT_SIZE,
        pr.WHITE,
      )

      # check for left and right arrow collisions for track selection
      # check for create new track collision

    case 1:
      pass
    case 2:
      pass

  if hovering:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_POINTING_HAND)
  else:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_DEFAULT)

  return page, track_index


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


def create_buts(
  cons: Constants, sidebar: pr.Rectangle, screen_width: int, screen_height: int
) -> dict[int, dict[str, any]]:
  draw_info = {}
  margin = 14
  font = pr.get_font_default()

  for i in range(3):
    draw_info[i] = {
      "texts": {"strings": [], "pos": []},
      "buts": [],
      "actions": [],
    }

  # Pg 1
  page = 0
  buts = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Edit button
  edit_text = "EDIT TRACK"
  text_size = pr.measure_text_ex(font, edit_text, cons.FONT_SIZE, 1)

  rec_x = sidebar.width / 2 - text_size.x / 2
  rec_y = screen_height / 3 * 2
  rec_height = text_size.y + margin

  edit_text_x = int(rec_x)
  edit_text_y = int(rec_y)

  edit_but = pr.Rectangle(
    rec_x - margin / 2, rec_y - margin / 2, text_size.x + margin, rec_height
  )

  actions.append("page2")
  buts.append(edit_but)
  texts["strings"].append(edit_text)
  texts["pos"].append((edit_text_x, edit_text_y))

  # Track index arrows
  left_arrow_text = "<"
  left_arrow_x = rec_x - rec_height - margin
  left_arrow_y = rec_y - margin / 2

  left_arrow = pr.Rectangle(left_arrow_x, left_arrow_y, rec_height, rec_height)

  text_size = pr.measure_text_ex(font, left_arrow_text, cons.FONT_SIZE, 1)
  left_text_arrow_x = left_arrow_x + rec_height / 2 - text_size.x / 2
  left_text_arrow_y = left_arrow_y + rec_height / 2 - text_size.y / 2

  actions.append("prev_track")
  buts.append(left_arrow)
  texts["strings"].append(left_arrow_text)
  texts["pos"].append((left_text_arrow_x, left_text_arrow_y))

  right_arrow_text = ">"
  right_arrow_x = rec_x + edit_but.width
  right_arrow_y = left_arrow_y

  right_arrow = pr.Rectangle(right_arrow_x, right_arrow_y, rec_height, rec_height)
  text_size = pr.measure_text_ex(font, left_arrow_text, cons.FONT_SIZE, 1)
  right_text_arrow_x = right_arrow_x + rec_height / 2 - text_size.x / 2
  right_text_arrow_y = right_arrow_y + rec_height / 2 - text_size.y / 2

  actions.append("next_track")
  buts.append(right_arrow)
  texts["strings"].append(right_arrow_text)
  texts["pos"].append((right_text_arrow_x, right_text_arrow_y))

  # Create Track
  create_text = "Create Track"

  text_size = pr.measure_text_ex(font, create_text, cons.FONT_SIZE, 1)

  create_x = sidebar.width - text_size.x
  create_y = screen_height - text_size.y

  create_track = pr.Rectangle(
    create_x - margin, create_y - margin, text_size.x + margin, text_size.y + margin
  )
  create_text_x = create_track.x + margin / 2
  create_text_y = create_track.y + margin / 2

  actions.append("create_track")
  buts.append(create_track)
  texts["strings"].append(create_text)
  texts["pos"].append((create_text_x, create_text_y))

  # Append arrays
  draw_info[page]["texts"] = texts
  draw_info[page]["buts"] = buts
  draw_info[page]["actions"] = actions

  # Pg 2
  # but = []
  # texts = []

  print(draw_info)
  return draw_info


if __name__ == "__main__":
  main()
