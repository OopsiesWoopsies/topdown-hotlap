import time
from pathlib import Path

import pyray as pr

from game.car.car_body import Car
from game.track.physics_track import PhysicsTrack
from render.car.render_car import RenderCar
from render.render_track import RenderTrack
from utils.constants import Constants
from utils.layouts import tracks


def main():
  cons = Constants()
  physics_track = PhysicsTrack()
  render_track = RenderTrack()
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

  edit_pts = False
  draw_chunks = False

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
    draw_world(camera, render_car, screen_mouse_point, check_mouse_point, sidebar, draw_chunks)
    draw_grid(cons, camera, screen_width, screen_height)
    pr.end_mode_2d()
    page, track_index, edit_pts, draw_chunks = check_screen_click(
      cons,
      physics_track,
      render_track,
      draw_dict,
      screen_mouse_point,
      check_mouse_point,
      page,
      track_index,
      edit_pts,
    )

    draw_screen(
      cons,
      draw_dict,
      sidebar,
      screen_height,
      page,
      track_index,
    )
    pr.draw_fps(screen_width - 100, 5)
    pr.end_drawing()

    check_mouse_point = False

  render_track.close()
  pr.close_window()


def draw_world(
  camera: pr.Camera2D,
  render_car: RenderCar,
  render_track: RenderTrack,
  screen_mouse_point: pr.Vector2,
  check_mouse_point: bool,
  sidebar: pr.Rectangle,
  draw_chunks: bool,
):
  if draw_chunks:
    render_track.draw()
  render_car.draw_car()

  if pr.check_collision_point_rec(screen_mouse_point, sidebar):
    return
  elif check_mouse_point:
    world_point = pr.get_world_to_screen_2d(screen_mouse_point, camera)
    print(world_point.x, world_point.y)


def check_screen_click(
  cons: Constants,
  physics_track: PhysicsTrack,
  render_track: RenderTrack,
  draw_dict: dict[int, dict[str, any]],
  screen_mouse_point: pr.Vector2,
  check_mouse_point: bool,
  page: int,
  track_index: int,
  edit_pts: bool,
  draw_chunks: bool
) -> tuple[int, int, bool, bool]:

  track_amount = len(tracks)
  but_arr = draw_dict[page]["buts"]
  len_but = len(but_arr)
  actions = draw_dict[page]["actions"]
  hovering = False

  for i in range(len_but):
    rec: pr.Rectangle = but_arr[i]

    if pr.check_collision_point_rec(pr.get_mouse_position(), rec):
      hovering = True

    if check_mouse_point and pr.check_collision_point_rec(screen_mouse_point, rec):
      match actions[i]:
        case "edit_points":
          edit_pts = True
          draw_chunks = False
        case "gen_track":
          # <- Create track (also make a get function that returns all the necessary things to generate chunks)
          render_track.unload_chunks()
          track_components = physics_track.get_track_components()
          # <- Render chunks
          draw_chunks = True
          edit_pts = False
        case "page1":
          page = 0
          edit_pts = False
          draw_chunks = False
        case "page2":
          page = 1
          edit_pts = True
          draw_chunks = False
          # load points as dots, but don't generate track
        case "page3":
          page = 2
          edit_pts = False
          draw_chunks = False
        case "prev_track":
          track_index = (track_index - 1) % track_amount
        case "next_track":
          track_index = (track_index + 1) % track_amount
        case "new_track":
          page = 1
          # don't load points as dots (there's nothing to load...)

  if hovering:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_POINTING_HAND)
  else:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_DEFAULT)

  return page, track_index, edit_pts, draw_chunks


def draw_screen(
  cons: Constants,
  draw_dict: dict[int, dict[str, any]],
  sidebar: pr.Rectangle,
  screen_height: int,
  page: int,
  track_index: int,
) -> tuple[int, int, bool]:
  font = pr.get_font_default()
  rec_width = sidebar.width
  pr.draw_rectangle_pro(sidebar, (0, 0), 0.0, (0, 0, 0, 180))

  but_arr = draw_dict[page]["buts"]
  texts = draw_dict[page]["texts"]
  text_arr = texts["strings"]
  text_pos_arr = texts["pos"]
  len_but = len(but_arr)

  for i in range(len_but):
    rec: pr.Rectangle = but_arr[i]
    text: str = text_arr[i]

    x, y = text_pos_arr[i]
    pr.draw_rectangle_pro(rec, (0, 0), 0.0, pr.LIGHTGRAY)
    pr.draw_text_ex(font, text, pr.Vector2(int(x), int(y)), cons.FONT_SIZE, 1, pr.BLACK)
    match page:
      case 0:
        text = tracks[track_index]["name"]
        half_text_width = pr.measure_text(text, cons.FONT_SIZE) / 2
        pr.draw_text(
          text,
          int(rec_width / 2 - half_text_width),
          int(screen_height / 3),
          cons.FONT_SIZE,
          pr.WHITE,
        )

      case 1:
        pass
      case 2:
        pass


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
  def align_but_info(
    text: str,
    action: str,
    unaligned_pos_x: int,
    unaligned_pos_y: int,
    margin: int,
    alignment: int,
  ) -> pr.Rectangle:
    """Aligns the button relative to the point, so if it is centered aligned at the given position,
    it will size itself that will symmetrical down the middle. If it is left aligned, then it will push everything to the right of the position.
    It is the same logic for right alignment. The text is centered aligned in the rectangle. The alignment refers to the x-axis.

    Args:
      text: The text inside the button.
      action: What pressing the button will do.
      unaligned_pos_x: The desired x position for alignment.
      unaligned_pos_y: The desired y position for alignment.
      margin: The margin between the text and edge of the button.
      alignment: 0-2, indicating left, center, right alignment respectively.

    Returns:
      The aligned rectangle. It can be used to format other buttons relative to it.
    """

    text_size = pr.measure_text_ex(font, text, cons.FONT_SIZE, 1)

    match alignment:
      case 0:  # left aligned
        aligned_text_x = unaligned_pos_x
      case 1:  # centered
        aligned_text_x = unaligned_pos_x - text_size.x / 2
      case 2:  # right aligned
        aligned_text_x = unaligned_pos_x - text_size.x
    aligned_text_y = unaligned_pos_y - text_size.y / 2

    rec = pr.Rectangle(
      aligned_text_x - margin / 2,
      aligned_text_y - margin / 2,
      text_size.x + margin,
      text_size.y + margin,
    )

    actions.append(action)
    buts.append(rec)
    texts["strings"].append(text)
    texts["pos"].append((aligned_text_x, aligned_text_y))

    return rec

  draw_info = {}
  margin = 14
  font = pr.get_font_default()

  for i in range(3):
    draw_info[i] = {
      "texts": {"strings": [], "pos": []},
      "buts": [],
      "actions": [],
    }

  # --Pg 1--  (Edit / Create track)
  page = 0
  buts = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Edit button
  edit_track_x = sidebar.width / 2
  edit_track_y = screen_height / 3 * 2

  edit_track_but: pr.Rectangle = align_but_info(
    "EDIT TRACK", "page2", edit_track_x, edit_track_y, margin, 1
  )

  # Track index arrows
  left_arrow_x = edit_track_x - edit_track_but.width / 2 - margin
  left_arrow_y = edit_track_y
  align_but_info("<-", "prev_track", left_arrow_x, left_arrow_y, margin, 2)

  right_arrow_x = edit_track_x + edit_track_but.width / 2 + margin
  right_arrow_y = edit_track_y

  align_but_info("->", "next_track", right_arrow_x, right_arrow_y, margin, 0)

  # Create Track
  create_x = sidebar.width - margin
  create_y = screen_height - margin * 2

  align_but_info("Create Track", "new_track", create_x, create_y, margin, 2)

  # Append arrays
  draw_info[page]["texts"] = texts
  draw_info[page]["buts"] = buts
  draw_info[page]["actions"] = actions

  # --Pg 2--  (Edit / Create points)
  page = 1
  buts = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Back button
  back_x = margin
  back_y = 5 + margin
  align_but_info("<-", "page1", back_x, back_y, margin, 0)

  # Edit Points
  edit_pt_x = sidebar.width / 2
  edit_pt_y = screen_height * 3 / 4
  align_but_info("Edit Points", "edit_points", edit_pt_x, edit_pt_y, margin, 1)

  # Generate Track
  gen_track_x = sidebar.width / 2
  gen_track_y = screen_height * 3 / 4 + 50
  align_but_info("Generate Track", "gen_track", gen_track_x, gen_track_y, margin, 1)

  draw_info[page]["texts"] = texts
  draw_info[page]["buts"] = buts
  draw_info[page]["actions"] = actions

  return draw_info


if __name__ == "__main__":
  main()
