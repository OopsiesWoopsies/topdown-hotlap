import math
import time
from pathlib import Path

import pyray as pr

from game.car.car_body import Car
from game.track.physics_track import PhysicsTrack
from render.car.render_car import RenderCar
from render.render_track import RenderTrack
from utils.constants import Constants
from utils.layouts import tracks


class Point:
  def __init__(
    self,
    cons: Constants,
    index: int,
    physics_pos: tuple[int, int],
    hitbox_size: int = 3,
  ):
    self.cons = cons
    self.index = index
    self.physics_pos = physics_pos
    self.world_pos = (physics_pos[0] * cons.PPM, physics_pos[1] * cons.PPM)
    self.hitbox_size = hitbox_size

    pos_x, pos_y = self.physics_pos
    self.hitbox = pr.Rectangle(
      pos_x - hitbox_size / 2, pos_y - hitbox_size / 2, hitbox_size, hitbox_size
    )
    pos_x, pos_y = self.world_pos
    hitbox_size *= self.cons.PPM
    self.draw_hitbox = pr.Rectangle(
      pos_x - hitbox_size / 2, pos_y - hitbox_size / 2, hitbox_size, hitbox_size
    )

  def update_pos(self, physics_pos: tuple[int, int]):
    self.physics_pt = physics_pos
    pos_x, pos_y = physics_pos
    self.world_pos = (pos_x * self.cons.PPM, pos_y * self.cons.PPM)

  def update_hitbox(self, physics_pos: tuple[int, int]):
    pos_x, pos_y = physics_pos
    self.hitbox = pr.Rectangle(
      pos_x - self.hitbox_size / 2,
      pos_y - self.hitbox_size / 2,
      self.hitbox_size,
      self.hitbox_size,
    )
    hitbox_size = self.hitbox_size * self.cons.PPM
    self.draw_hitbox = self.hitbox = pr.Rectangle(
      pos_x - hitbox_size / 2,
      pos_y - hitbox_size / 2,
      hitbox_size,
      hitbox_size,
    )

  def draw_point(self, finish_index: int):
    if finish_index == self.index:
      colour = pr.BLUE
    else:
      colour = pr.RED
    pr.draw_rectangle_pro(self.draw_hitbox, (0, 0), 0.0, colour)
    pr.draw_rectangle_lines_ex(self.draw_hitbox, 0.2 * self.cons.PPM, pr.WHITE)

    font = pr.get_font_default()
    text = str(self.index)
    text_size = pr.measure_text_ex(font, text, self.cons.FONT_SIZE, 1)
    pos_x, pos_y = self.world_pos
    px = pos_x + text_size.x
    py = pos_y - text_size.y / 2
    pr.draw_text_pro(
      font, text, (px, py), (text_size.x / 2, text_size.y / 2), 90, 50, 1, pr.BLACK
    )


def main():
  cons = Constants()
  physics_track = PhysicsTrack()
  render_track = RenderTrack()
  screen_width = cons.SCREEN_WIDTH
  screen_height = cons.SCREEN_HEIGHT
  pr.init_window(screen_width, screen_height, "Track Editor")
  # pr.set_target_fps(144)

  track_info: dict[str, str | int | list[tuple[int, int]]] = {
    "name": "",
    "finish": 0,
    "track": [],
  }
  points: list[Point] = []

  base_cam_zoom = 1 / cons.PPM * 20
  camera = pr.Camera2D(
    (screen_width / 2, screen_height / 2), (0, 0), -90.0, base_cam_zoom
  )
  pos_x = 0.0
  pos_y = 0.0

  page = 0  # 0-2 (inclusive, respectively featuring track selection / make new track, editing track, naming track)
  screen_mouse_point = pr.Vector2(0, 0)
  left_click = False
  right_click = False
  check_left_mouse_point = False
  check_right_mouse_point = False

  edit_pts = False
  draw_chunks = False
  clicked_point = False

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
      pos_x, pos_y = control_screen(cons, fixed_dt, camera, (pos_x, pos_y))
      accumulator -= fixed_dt

    # Clicking
    if left_click and pr.is_mouse_button_up(pr.MOUSE_LEFT_BUTTON):
      screen_mouse_point = pr.get_mouse_position()
      left_click = False
      check_left_mouse_point = True
    elif pr.is_mouse_button_down(pr.MOUSE_LEFT_BUTTON):
      left_click = True

    if right_click and pr.is_mouse_button_up(pr.MOUSE_RIGHT_BUTTON):
      screen_mouse_point = pr.get_mouse_position()
      right_click = False
      check_right_mouse_point = True
    elif pr.is_mouse_button_down(pr.MOUSE_RIGHT_BUTTON):
      right_click = True

    # Check for clicks
    clicked_point = check_world_click(
      cons,
      camera,
      screen_mouse_point,
      check_left_mouse_point,
      check_right_mouse_point,
      sidebar,
      edit_pts,
      clicked_point,
      track_info["track"],
      points,
    )
    page, track_index, edit_pts, draw_chunks = check_screen_click(
      cons,
      physics_track,
      render_track,
      draw_dict,
      screen_mouse_point,
      check_left_mouse_point,
      page,
      track_index,
      edit_pts,
      draw_chunks,
      track_info,
      points,
    )

    # Drawing
    pr.begin_drawing()
    pr.clear_background(pr.DARKGREEN)

    pr.begin_mode_2d(camera)
    draw_world(
      camera,
      render_car,
      render_track,
      page,
      draw_chunks,
      track_info,
      points,
    )
    draw_grid(cons, camera, screen_width, screen_height)
    pr.end_mode_2d()
    draw_screen(
      cons,
      sidebar,
      draw_dict,
      screen_height,
      page,
      track_index,
    )
    pr.draw_fps(screen_width - 100, 5)
    pr.end_drawing()

    check_left_mouse_point = False
    check_right_mouse_point = False

  render_track.close()
  pr.close_window()


def check_world_click(
  cons: Constants,
  camera: pr.Camera2D,
  screen_mouse_point: pr.Vector2,
  check_left_mouse_point: bool,
  check_right_mouse_point: bool,
  sidebar: pr.Rectangle,
  edit_pts: bool,
  clicked_point: bool,
  track_points: list[tuple[int, int]],
  points: list[Point],
) -> bool:
  if (
    not edit_pts
    or not (check_left_mouse_point or check_right_mouse_point)
    or pr.check_collision_point_rec(screen_mouse_point, sidebar)
  ):
    return

  world_pos = pr.get_screen_to_world_2d(screen_mouse_point, camera)
  physics_pos = (round(world_pos.x / cons.PPM), round(world_pos.y / cons.PPM))
  print(physics_pos)

  point_clicked = False
  for pt in points:
    if pr.check_collision_point_rec(physics_pos, pt.hitbox):
      point_clicked = True
      selected_pt = pt
      break

  if check_left_mouse_point:
    if point_clicked:
      clicked_point = True

    else:
      new_pt = Point(cons, len(points), physics_pos)
      points.append(new_pt)
      track_points.append(physics_pos)
  elif check_right_mouse_point and point_clicked:
    index = selected_pt.index
    for pt in points:  # Update indexes after the impending deletion
      pt.index -= 1

    pt = track_points.pop(index)
    points.pop(index)
    clicked_point = False
    print(f"Deleted point: {pt}")

  return clicked_point


def draw_world(
  camera: pr.Camera2D,
  render_car: RenderCar,
  render_track: RenderTrack,
  page: int,
  draw_chunks: bool,
  track_info: dict[str, str | int | list[tuple[float, float]]],
  points: list[Point],
):
  if draw_chunks:
    render_track.draw(camera)
  render_car.draw_car()

  if page == 1:
    finish_i = track_info["finish"]
    for pt in points:
      pt.draw_point(finish_i)


def check_screen_click(
  cons: Constants,
  physics_track: PhysicsTrack,
  render_track: RenderTrack,
  draw_dict: dict[int, dict[str, any]],
  screen_mouse_point: pr.Vector2,
  check_left_mouse_point: bool,
  page: int,
  track_index: int,
  edit_pts: bool,
  draw_chunks: bool,
  track_info: dict[str, str | int | list[tuple[float, float]]],
  points: list[Point],
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
    if not check_left_mouse_point or not pr.check_collision_point_rec(
      screen_mouse_point, rec
    ):
      continue

    match actions[i]:
      case "edit_points":
        edit_pts = True
        draw_chunks = False
      case "gen_track":
        draw_chunks = True
        edit_pts = False

        physics_track.create_track(track_info["track"], track_info["finish"])
        render_track.render_chunks(cons, physics_track.get_track_components())
      case "prev_track":
        track_index = (track_index - 1) % track_amount
      case "next_track":
        track_index = (track_index + 1) % track_amount
      case "new_track":
        page = 1
      case "print":
        track_info["track"] = tuple(track_info["track"])
        print(track_info)
        track_info["track"] = list(track_info["track"])
      case "page1":
        page = 0
        edit_pts = False
        draw_chunks = False
      case "page2":
        page = 1
        edit_pts = True
        draw_chunks = False

        track = tracks[track_index]
        track_info["name"] = track["name"]
        track_info["track"] = list(track["track"])
        track_info["finish"] = track["finish"]

        points.clear()

        for i, physics_pos in enumerate(track["track"]):
          points.append(Point(cons, i, physics_pos))
      case "page3":
        page = 2
        edit_pts = False
        draw_chunks = False

  if hovering:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_POINTING_HAND)
  else:
    pr.set_mouse_cursor(pr.MOUSE_CURSOR_DEFAULT)

  return page, track_index, edit_pts, draw_chunks


def draw_screen(
  cons: Constants,
  sidebar: pr.Rectangle,
  draw_dict: dict[int, dict[str, any]],
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
      # Draw length of track
      pass
    case 2:
      pass


def control_screen(
  cons: Constants, dt: float, camera: pr.Camera2D, pos: tuple[float, float]
):
  pos_x, pos_y = pos
  speed = 500

  zoom_rate = 0
  zoom_speed = 0

  if pr.is_key_down(pr.KEY_LEFT_SHIFT):
    speed = 1250
    zoom_speed = 1.0

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
    zoom_rate = -1.5 - zoom_speed
  if pr.is_key_down(pr.KEY_EQUAL):
    zoom_rate = 1.5 + zoom_speed

  camera.target = (pos_x, pos_y)
  if zoom_rate != 0:
    camera.zoom *= math.exp(zoom_rate * dt)
  if camera.zoom < 1.6 / cons.PPM:
    camera.zoom = 1.6 / cons.PPM
  elif camera.zoom > 50 / cons.PPM:
    camera.zoom = 50 / cons.PPM

  return pos_x, pos_y


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

  align_but_info("CREATE TRACK", "new_track", create_x, create_y, margin, 2)

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

  # Next button
  next_x = sidebar.width - margin
  next_y = 5 + margin
  align_but_info("->", "page3", next_x, next_y, margin, 2)

  # Edit Points
  edit_pt_x = sidebar.width / 2
  edit_pt_y = screen_height * 3 / 4
  align_but_info("EDIT POINTS", "edit_points", edit_pt_x, edit_pt_y, margin, 1)

  # Generate Track
  gen_track_x = sidebar.width / 2
  gen_track_y = screen_height * 3 / 4 + 50
  align_but_info("GENERATE TRACK", "gen_track", gen_track_x, gen_track_y, margin, 1)

  draw_info[page]["texts"] = texts
  draw_info[page]["buts"] = buts
  draw_info[page]["actions"] = actions

  # --Pg 3--  (Name track and print it)
  page = 2
  buts = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Back button
  back_x = margin
  back_y = 5 + margin
  align_but_info("<-", "page2", back_x, back_y, margin, 0)

  # Print main track points to terminal
  print_x = sidebar.width / 2
  print_y = screen_height * 3 / 4
  align_but_info("PRINT TRACK", "print", print_x, print_y, margin, 1)

  draw_info[page]["texts"] = texts
  draw_info[page]["buts"] = buts
  draw_info[page]["actions"] = actions

  return draw_info


def draw_grid(
  cons: Constants, camera: pr.Camera2D, screen_width: int, screen_height: int
):  # 2m x 2m gridbox
  if camera.zoom < 2.5 / cons.PPM:
    return

  spacing = cons.PPM * 2

  tl = pr.get_screen_to_world_2d((0, 0), camera)
  br = pr.get_screen_to_world_2d((screen_width, screen_height), camera)

  start_x = int(round(tl.x) // spacing) * spacing + spacing
  end_x = int(round(br.x) // spacing) * spacing

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
