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
    self.colour = pr.RED

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
    self.physics_pos = physics_pos
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
    pos_x *= self.cons.PPM
    pos_y *= self.cons.PPM
    self.draw_hitbox = pr.Rectangle(
      pos_x - hitbox_size / 2,
      pos_y - hitbox_size / 2,
      hitbox_size,
      hitbox_size,
    )

  def draw(self):
    pr.draw_rectangle_rec(self.draw_hitbox, self.colour)
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
  render_track = RenderTrack(cons)
  screen_width = cons.SCREEN_WIDTH
  screen_height = cons.SCREEN_HEIGHT
  pr.init_window(screen_width, screen_height, "Track Editor")
  pr.set_target_fps(144)

  track_info: dict[str, str | int | float | list[tuple[int, int]]] = {
    "name": "",
    "finish": 0,
    "length": 0.0,
    "track": [],
  }
  points: list[Point] = []

  base_cam_zoom = 1 / cons.PPM * 20
  camera = pr.Camera2D(
    (screen_width / 2, screen_height / 2), (0, 0), -90.0, base_cam_zoom
  )
  pos_x = 0.0
  pos_y = 0.0

  # General states
  page = 0  # 0-2 (inclusive, respectively featuring track selection / make new track, editing track, naming track)
  screen_mouse_point = pr.Vector2(0, 0)
  left_click = False
  right_click = False
  check_left_mouse_point = False
  check_right_mouse_point = False
  but_hovering = False
  input_hovering = False

  # Screen button states
  edit_points = False
  draw_chunks = False
  is_draw_grid = True

  # Screen input states
  enable_numpad = False
  enable_keyboard = False
  input_index = None
  track_index = 0

  # World states
  point_selected = None
  possessed_point = None

  # Screen elements
  sidebar = pr.Rectangle(0, 0, 350, screen_height)

  # Hot loop init
  last_time = time.perf_counter()
  accumulator = 0.0
  fixed_dt = 1 / 144.0

  # Car for reference
  car = Car(cons, (0.0, 0.0), 0, (5.6, 2.0))
  scripoint_dir = Path(__file__).resolve().parent.parent.parent
  car_path = scripoint_dir / "assets" / "imgs" / "car.png"
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

  draw_info = create_screen_elements(
    cons, sidebar, screen_width, screen_height, track_info
  )

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
        draw_info = create_screen_elements(
          cons, sidebar, screen_width, screen_height, track_info
        )
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
        draw_info = create_screen_elements(
          cons, sidebar, screen_width, screen_height, track_info
        )

    # Static dt
    current_time = time.perf_counter()
    frame_time = min(current_time - last_time, 0.25)
    last_time = current_time
    accumulator += frame_time

    while accumulator >= fixed_dt:
      if not (enable_numpad or enable_keyboard):
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
    _, input_info = draw_info

    input_hovering, enable_numpad, enable_keyboard, input_index = (
      check_input_screen_click(
        input_info,
        screen_mouse_point,
        check_left_mouse_point,
        page,
        input_index,
        enable_numpad,
        enable_keyboard,
        point_selected,
        track_info,
        points,
      )
    )

    if not enable_numpad:
      point_selected, possessed_point = check_world_click(
        cons,
        camera,
        screen_mouse_point,
        check_left_mouse_point,
        check_right_mouse_point,
        sidebar,
        edit_points,
        point_selected,
        possessed_point,
        input_info,
        track_info,
        points,
      )

      page, track_index, edit_points, draw_chunks, is_draw_grid, but_hovering = (
        check_button_screen_click(
          cons,
          physics_track,
          render_track,
          draw_info,
          screen_mouse_point,
          check_left_mouse_point,
          page,
          track_index,
          edit_points,
          draw_chunks,
          is_draw_grid,
          track_info,
          points,
        )
      )

      if but_hovering:
        pr.set_mouse_cursor(pr.MOUSE_CURSOR_POINTING_HAND)
      elif input_hovering:
        pr.set_mouse_cursor(pr.MOUSE_CURSOR_IBEAM)
      else:
        pr.set_mouse_cursor(pr.MOUSE_CURSOR_DEFAULT)

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
      points,
    )
    if is_draw_grid:
      draw_grid(cons, camera, screen_width, screen_height)
    pr.end_mode_2d()
    draw_screen(
      cons,
      camera,
      sidebar,
      draw_info,
      screen_height,
      page,
      track_index,
      edit_points,
      draw_chunks,
      enable_numpad,
      enable_keyboard,
      point_selected,
      possessed_point,
      input_index,
      track_info,
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
  edit_points: bool,
  point_selected: Point,
  possessed_point: Point,
  input_info: dict[int, dict[str, any]],
  track_info: dict[str, str | int | list[tuple[int, int]]],
  points: list[Point],
) -> tuple[Point, Point]:
  # Check for possessed point moving
  if point_selected != None:
    if check_left_mouse_point:
      point_selected.colour = (
        pr.BLUE if track_info["finish"] == point_selected.index else pr.RED
      )
      action_i = find_action_index(input_info[1]["actions"], "change_i")
      input_info[1]["content"][action_i]["string"] = "NAN"
      return None, None
    return point_selected, None

  if possessed_point != None:  # Follow mouse
    world_pos = pr.get_screen_to_world_2d(pr.get_mouse_position(), camera)
    physics_pos = (round(world_pos.x / cons.PPM), round(world_pos.y / cons.PPM))
    possessed_point.update_pos(physics_pos)
    possessed_point.update_hitbox(physics_pos)

    if check_left_mouse_point:  # Save position
      possessed_point.colour = (
        pr.BLUE if track_info["finish"] == possessed_point.index else pr.RED
      )
      index = possessed_point.index
      track_info["track"][index] = physics_pos
      return None, None
    return None, possessed_point

  # Check for any mouse updates
  if (
    not edit_points
    or not (check_left_mouse_point or check_right_mouse_point)
    or pr.check_collision_point_rec(screen_mouse_point, sidebar)
  ):
    return None, None

  world_pos = pr.get_screen_to_world_2d(screen_mouse_point, camera)
  physics_pos = (round(world_pos.x / cons.PPM), round(world_pos.y / cons.PPM))

  point_clicked = False
  for point in reversed(points):
    if pr.check_collision_point_rec(physics_pos, point.hitbox):
      point_clicked = True
      if check_left_mouse_point:
        if pr.is_key_down(pr.KEY_LEFT_CONTROL):
          possessed_point = point
        else:
          point_selected = point
        break
      if check_right_mouse_point:
        point_selected = point
        break

  if check_left_mouse_point:  # Point addition
    if not point_clicked:  # Unless point clicked, leading to existing point movement
      new_point = Point(cons, len(points), physics_pos)
      points.append(new_point)
      track_info["track"].append(physics_pos)
    else:
      if pr.is_key_down(pr.KEY_LEFT_CONTROL):
        possessed_point.colour = pr.YELLOW
      else:
        point_selected.colour = pr.MAGENTA
        action_i = find_action_index(input_info[1]["actions"], "change_i")
        input_info[1]["content"][action_i]["string"] = str(point_selected.index)
  elif check_right_mouse_point and point_clicked:  # Point deletion
    if len(points) == 1:  # Always keep one point in the world
      point_selected = None
      possessed_point = None
      return point_selected, possessed_point

    num = track_info["finish"]
    index = point_selected.index

    if num >= index and num != 0:
      track_info["finish"] -= 1
      action_i = find_action_index(input_info[1]["actions"], "finish_i")
      input_info[1]["content"][action_i]["string"] = str(track_info["finish"])

    for i in range(
      index + 1, len(points)
    ):  # Update indexes after the impending deletion
      points[i].index -= 1

    point = track_info["track"].pop(index)
    points.pop(index)

    points[track_info["finish"]].colour = pr.BLUE
    point_selected = None
    possessed_point = None

  return point_selected, possessed_point


def draw_world(
  camera: pr.Camera2D,
  render_car: RenderCar,
  render_track: RenderTrack,
  page: int,
  draw_chunks: bool,
  points: list[Point],
):
  if draw_chunks:
    render_track.draw_borders(camera)
    render_track.draw(camera)
  render_car.draw_car()

  if page == 1 or page == 2:
    for point in points:
      point.draw()


def check_input_screen_click(
  input_info: dict[int, dict[str, any]],
  screen_mouse_point: pr.Vector2,
  check_left_mouse_point: bool,
  page: int,
  input_index: int | None,
  enable_numpad: bool,
  enable_keyboard: bool,
  point_selected: Point | None,
  track_info: dict[str, str | int | list[tuple[float, float]]],
  points: list[Point],
) -> tuple[bool, bool, bool, int | None]:
  def check_input_deletion(input_content_details: dict[str, str]):
    if (
      pr.is_key_pressed(pr.KEY_BACKSPACE)
      or pr.is_key_pressed_repeat(pr.KEY_BACKSPACE)
      and len(input_content_details["string"]) > 0
    ):
      input_content_details["string"] = input_content_details["string"][:-1]

  input_hovering = False
  input_arr = input_info[page]["inputs"]
  input_actions = input_info[page]["actions"]
  if input_index != None:
    input_content_details = input_info[page]["content"][input_index]
  len_input = len(input_arr)

  # Check for number inputs
  if enable_numpad or enable_keyboard:
    if input_index == None:
      print("No input rec..?")
      enable_numpad = False
      enable_keyboard = False
      return input_hovering, enable_numpad, enable_keyboard, input_index

    if pr.is_key_pressed(pr.KEY_ENTER) or check_left_mouse_point:
      action = input_actions[input_index]
      string = input_content_details["string"]
      enable_numpad = False
      enable_keyboard = False
      input_index = None

      match action:
        case "change_i":
          if len(string) == 0:
            input_content_details["string"] = str(point_selected.index)
            return input_hovering, enable_numpad, enable_keyboard, input_index

          # Validate index and check if it is the finish index
          point_num = len(track_info["track"])
          new_index = int(string)
          old_index = point_selected.index
          if new_index < 0:
            new_index = 0
          elif new_index >= point_num:
            new_index = point_num - 1

          # Update index and sync with array
          pos = track_info["track"].pop(old_index)
          track_info["track"].insert(new_index, pos)
          points.pop(old_index)
          points.insert(new_index, point_selected)

          start_index = min(old_index, new_index)
          end_index = max(old_index, new_index)
          for i in range(start_index, end_index + 1):
            points[i].index = i

          # Update change index string
          if track_info["finish"] >= start_index and track_info["finish"] <= end_index:
            action_i = find_action_index(input_actions, "finish_i")
            diff = old_index - new_index
            if diff == 0:
              op = 0
            else:
              op = diff / abs(diff)
            if point_selected.index != track_info["finish"]:
              points[track_info["finish"]].colour = pr.RED
            track_info["finish"] += int(op)
            input_info[page]["content"][action_i]["string"] = str(track_info["finish"])
            points[track_info["finish"]].colour = pr.BLUE

          return input_hovering, enable_numpad, enable_keyboard, input_index

        case "finish_i":
          if len(string) == 0:
            input_content_details["string"] = str(track_info["finish"])
            return input_hovering, enable_numpad, enable_keyboard, input_index

          point_num = len(track_info["track"])
          num = int(string)
          if num < 0:
            num = 0
          elif num >= point_num:
            num = point_num - 1

          points[track_info["finish"]].colour = pr.RED
          points[num].colour = pr.BLUE
          track_info["finish"] = num
          input_content_details["string"] = str(num)
          return input_hovering, enable_numpad, enable_keyboard, input_index

        case "gen_x" | "gen_y":
          if len(string) == 0:
            return input_hovering, enable_numpad, enable_keyboard, input_index

          num = int(string)
          if num < -5000:
            num = -5000
          elif num > 5000:
            num = 5000
          input_content_details["string"] = str(num)
          return input_hovering, enable_numpad, enable_keyboard, input_index

        case "set_name":
          if len(string) == 0:
            input_content_details["string"] = track_info["name"]
            return input_hovering, enable_numpad, enable_keyboard, input_index

          track_info["name"] = input_content_details["string"]
          return input_hovering, enable_numpad, enable_keyboard, input_index

    check_input_deletion(input_content_details)

    key = pr.get_char_pressed()
    while key > 0:
      if enable_numpad:
        if key == 45 and len(input_content_details["string"]) == 0:
          input_content_details["string"] = "-"
        elif key >= 48 and key <= 57:
          input_content_details["string"] += chr(key)
      elif (
        enable_keyboard
        and key >= 32
        and key <= 126
        and len(input_content_details["string"]) < 20
      ):
        input_content_details["string"] += chr(key)

      key = pr.get_char_pressed()

    return input_hovering, enable_numpad, enable_keyboard, input_index

  # Check for input clicking
  for i in range(len_input):
    rec: pr.Rectangle = input_arr[i]
    if pr.check_collision_point_rec(pr.get_mouse_position(), rec):
      input_hovering = True
    if not check_left_mouse_point or not pr.check_collision_point_rec(
      screen_mouse_point, rec
    ):
      continue

    # Find which input
    if point_selected != None:
      if input_actions[i] == "change_i":
        enable_numpad = True
        input_index = i
    else:
      match input_actions[i]:
        case "gen_x" | "gen_y" | "finish_i":
          enable_numpad = True
          input_index = i
        case "set_name":
          enable_keyboard = True
          input_index = i

      if input_index != None:
        input_content_details = input_info[page]["content"][input_index]
        input_content_details["string"] = ""

  return input_hovering, enable_numpad, enable_keyboard, input_index


def check_button_screen_click(
  cons: Constants,
  physics_track: PhysicsTrack,
  render_track: RenderTrack,
  draw_info: tuple[dict[int, dict[str, any], dict[int, dict[str, any]]]],
  screen_mouse_point: pr.Vector2,
  check_left_mouse_point: bool,
  page: int,
  track_index: int,
  edit_points: bool,
  draw_chunks: bool,
  is_draw_grid: bool,
  track_info: dict[str, str | int | list[tuple[float, float]]],
  points: list[Point],
) -> tuple[int, int, bool, bool, bool, bool]:
  track_amount = len(tracks)
  hovering = False

  but_info, input_info = draw_info

  but_arr = but_info[page]["buts"]
  but_actions = but_info[page]["actions"]
  len_but = len(but_arr)
  for i in range(len_but):
    rec: pr.Rectangle = but_arr[i]
    if pr.check_collision_point_rec(pr.get_mouse_position(), rec):
      hovering = True
    if not check_left_mouse_point or not pr.check_collision_point_rec(
      screen_mouse_point, rec
    ):
      continue

    match but_actions[i]:
      case "edit_points":
        edit_points = True
        draw_chunks = False
      case "gen_track":
        if len(points) < 4:
          print("Not enough points. Generate at least 4 points.")
        else:
          draw_chunks = True
          edit_points = False

          physics_track.create_track(track_info["track"], track_info["finish"])
          render_track.render_chunks(physics_track.get_track_components())
      case "toggle_grid":
        is_draw_grid = not is_draw_grid
      case "gen_point":
        if edit_points:
          content = input_info[page]["content"]
          actions = input_info[page]["actions"]
          x_found = False
          y_found = False
          for i in range(len(content)):
            match actions[i]:
              case "gen_x":
                if content[i]["string"] == "":
                  x = 0
                else:
                  x = int(content[i]["string"])
                  content[i]["string"] = ""
                x_found = True
              case "gen_y":
                if content[i]["string"] == "":
                  y = 0
                else:
                  y = int(content[i]["string"])
                  content[i]["string"] = ""
                y_found = True
            if x_found and y_found:
              break

          coord = (x, y)
          point = Point(cons, len(points), coord)
          points.append(point)
          track_info["track"].append(coord)
      case "prev_track":
        track_index = (track_index - 1) % track_amount
      case "next_track":
        track_index = (track_index + 1) % track_amount
      case "new_track":
        page = 1
        edit_points = True
        draw_chunks = False

        track_info["name"] = ""
        track_info["track"] = [(0, 0)]
        track_info["finish"] = 0

        point = Point(cons, 0, (0, 0))
        points.append(point)
        point.colour = pr.BLUE
      case "print":  # Calculates track length prints track information to terminal
        physics_track.create_track(track_info["track"], track_info["finish"])
        sum_length = 0
        center_points = physics_track.center_pts
        for i in range(len(physics_track.center_pts) - 1):
          a_x, a_y = center_points[i]
          b_x, b_y = center_points[i + 1]
          length_x = abs(b_x) - abs(a_x)
          length_y = abs(b_y) - abs(a_y)

          sum_length += math.sqrt(length_x * length_x + length_y * length_y)

        track_info["length"] = round(sum_length, 2)

        track_info["track"] = tuple(track_info["track"])
        print(track_info)
        track_info["track"] = list(track_info["track"])
      case "page1":
        page = 0
        edit_points = False
        draw_chunks = False

        actions = input_info[1]["actions"]

        track_info["name"] = ""
        track_info["track"] = []
        track_info["finish"] = "NAN"
        track_info["length"] = 0.0
        points.clear()
        action_i = find_action_index(actions, "finish_i")
        input_info[1]["content"][action_i]["string"] = str(0)

        actions = input_info[2]["actions"]
        action_i = find_action_index(actions, "set_name")
        input_info[2]["content"][action_i]["string"] = ""
      case "page2":
        page = 1

        if len(points) == 0:
          track = tracks[track_index]
          track_info["name"] = track["name"]
          track_info["track"] = list(track["track"])
          track_info["finish"] = track["finish"]
          track_info["length"] = track["length"]

          for i, physics_pos in enumerate(track["track"]):
            points.append(Point(cons, i, physics_pos))

          points[track_info["finish"]].colour = pr.BLUE
          actions = input_info[page]["actions"]

          action_i = find_action_index(actions, "finish_i")
          input_info[page]["content"][action_i]["string"] = str(track_info["finish"])

          actions = input_info[2]["actions"]
          action_i = find_action_index(actions, "set_name")
          input_info[2]["content"][action_i]["string"] = track_info["name"]

      case "page3":
        page = 2
        edit_points = False

  return page, track_index, edit_points, draw_chunks, is_draw_grid, hovering


def draw_screen(
  cons: Constants,
  camera: pr.Camera2D,
  sidebar: pr.Rectangle,
  draw_info: tuple[dict[int, dict[str, any]], dict[int, dict[str, any]]],
  screen_height: int,
  page: int,
  track_index: int,
  edit_points: bool,
  draw_chunks: bool,
  enable_numpad: bool,
  enable_keyboard: bool,
  point_selected: Point | None,
  possessed_point: Point | None,
  input_index: int,
  track_info: dict[str, str | int | float | list[tuple[int, int]]],
) -> tuple[int, int, bool]:
  font = pr.get_font_default()
  sidebar_width = sidebar.width
  pr.draw_rectangle_rec(sidebar, (0, 0, 0, 180))

  but_info, input_info = draw_info

  but_arr = but_info[page]["buts"]
  but_texts = but_info[page]["texts"]
  but_text_arr = but_texts["strings"]
  but_text_pos_arr = but_texts["pos"]

  input_arr = input_info[page]["inputs"]
  input_labels = input_info[page]["labels"]
  input_label_arr = input_labels["strings"]
  input_label_pos_arr = input_labels["pos"]
  input_contents = input_info[page]["content"]

  for i, input_elm in enumerate(input_arr):
    label: str = input_label_arr[i]
    content: dict = input_contents[i]

    x, y = input_label_pos_arr[i]
    colour = pr.BLUE
    if (enable_numpad or enable_keyboard) and input_index == i:
      colour = pr.RED
    if input_info[page]["actions"][i] == "change_i":
      if point_selected == None:
        pr.draw_rectangle_rec(input_elm, pr.DARKGRAY)
        pr.draw_rectangle_lines_ex(input_elm, 5, pr.BLACK)
      else:
        pr.draw_rectangle_rec(input_elm, pr.LIGHTGRAY)
        pr.draw_rectangle_lines_ex(input_elm, 5, colour)
    else:
      if point_selected == None:
        pr.draw_rectangle_rec(input_elm, pr.LIGHTGRAY)
        pr.draw_rectangle_lines_ex(input_elm, 5, colour)
      else:
        pr.draw_rectangle_rec(input_elm, pr.DARKGRAY)
        pr.draw_rectangle_lines_ex(input_elm, 5, pr.BLACK)

    pr.draw_text_ex(font, label, pr.Vector2(x, y), cons.FONT_SIZE, 1, pr.WHITE)
    x, y = content["str_pos"]
    pr.draw_text_ex(
      font, content["string"], pr.Vector2(x, y), cons.FONT_SIZE, 1, pr.BLACK
    )

  for i, but_elm in enumerate(but_arr):
    text: str = but_text_arr[i]

    x, y = but_text_pos_arr[i]
    pr.draw_rectangle_rec(but_elm, pr.LIGHTGRAY)
    pr.draw_text_ex(font, text, pr.Vector2(x, y), cons.FONT_SIZE, 1, pr.BLACK)

    if (
      edit_points
      and but_info[page]["actions"][i] == "edit_points"
      or draw_chunks
      and but_info[page]["actions"][i] == "gen_track"
    ):
      pr.draw_rectangle_lines_ex(but_elm, 5, pr.RED)

  match page:
    case 0:
      text = tracks[track_index]["name"]
      half_text_width = pr.measure_text(text, cons.FONT_SIZE) / 2
      pr.draw_text(
        text,
        int(sidebar_width / 2 - half_text_width),
        int(screen_height / 3),
        cons.FONT_SIZE,
        pr.WHITE,
      )

    case 1:
      # Mouse position
      pos = pr.get_screen_to_world_2d(pr.get_mouse_position(), camera)
      physics_text = f"({round(pos.x / cons.PPM, 1)}m, {round(pos.y / cons.PPM, 1)}m)"
      world_text = f"({round(pos.x, 3)}px, {round(pos.y, 3)}px)"
      height = int(screen_height / 2)
      pr.draw_text(physics_text, 10, height, cons.FONT_SIZE, pr.WHITE)
      pr.draw_text(world_text, 10, height + 25, 18, pr.WHITE)

      # Selected point coordinate
      if point_selected != None:
        text = f"{point_selected.physics_pos}"
      elif possessed_point != None:
        text = f"{possessed_point.physics_pos}"
      else:
        text = "Point: (x, y)"

      text_width = pr.measure_text(text, cons.FONT_SIZE)
      pr.draw_text(
        text, int(sidebar_width / 2 - text_width / 2), 10, cons.FONT_SIZE, pr.WHITE
      )

      # Total points
      text = f"# pts: {len(track_info['track'])}"
      text_width = pr.measure_text(text, cons.FONT_SIZE)
      pr.draw_text(
        text, int(sidebar_width / 2 - text_width / 2), 35, cons.FONT_SIZE, pr.WHITE
      )
    case 2:
      # Track length
      text = f"Length: {track_info['length']}m"
      pr.draw_text(text, 10, int(screen_height / 2), cons.FONT_SIZE, pr.WHITE)


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


def create_screen_elements(
  cons: Constants,
  sidebar: pr.Rectangle,
  screen_width: int,
  screen_height: int,
  track_info: dict[str, str | int | list[tuple[int, int]]],
) -> tuple[dict[int, dict[str, any]], dict[int, dict[str, any]]]:
  def align_info(
    text: str,
    action: str,
    unaligned_pos_x: int,
    unaligned_pos_y: int,
    margin: int,
    alignment: int,
    is_input: bool = False,
    index: int = -1,
    width: int = 10,
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
      is_input: Change how alignment is calculated since inputs are drawn differently.
      index: Only applies to inputs.
      width: Only applies to inputs (width of the input box).

    Returns:
      The aligned rectangle. It can be used to format other buttons relative to it.
    """

    text_size = pr.measure_text_ex(font, text, cons.FONT_SIZE, 1)

    if is_input:
      rec_width = width
    else:
      rec_width = text_size.x + margin

    rec_height = text_size.y + margin

    match alignment:
      case 0:  # left aligned
        aligned_text_x = unaligned_pos_x
      case 1:  # centered
        aligned_text_x = unaligned_pos_x - text_size.x / 2
        if is_input:
          aligned_text_x -= rec_width / 2
      case 2:  # right aligned
        aligned_text_x = unaligned_pos_x - text_size.x
        if is_input:
          aligned_text_x -= rec_width

    aligned_text_y = unaligned_pos_y - text_size.y / 2

    rec_x = aligned_text_x - margin / 2
    rec_y = aligned_text_y - margin / 2

    if is_input:
      rec_x += text_size.x + margin

      content[index] = {
        "string": "",
        "str_pos": (int(rec_x + margin / 2), int(rec_y + margin / 2)),
      }

    rec = pr.Rectangle(rec_x, rec_y, rec_width, rec_height)

    actions.append(action)
    recs.append(rec)
    texts["strings"].append(text)
    texts["pos"].append((int(aligned_text_x), int(aligned_text_y)))

    return rec

  draw_but_info = {}
  draw_input_info = {}
  margin = 14
  font = pr.get_font_default()

  for i in range(3):
    draw_but_info[i] = {
      "texts": {"strings": [], "pos": []},
      "buts": [],
      "actions": [],
    }
    draw_input_info[i] = {
      "labels": {"strings": [], "pos": []},
      "content": {},
      "inputs": [],
      "actions": [],
    }

  # --Pg 1--  (Edit / Create track)
  page = 0
  recs = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Edit button
  edit_track_x = sidebar.width / 2
  edit_track_y = screen_height / 3 * 2

  edit_track_but: pr.Rectangle = align_info(
    "EDIT TRACK", "page2", edit_track_x, edit_track_y, margin, 1
  )

  # Track index arrows
  left_arrow_x = edit_track_x - edit_track_but.width / 2 - margin
  left_arrow_y = edit_track_y
  align_info("<-", "prev_track", left_arrow_x, left_arrow_y, margin, 2)

  right_arrow_x = edit_track_x + edit_track_but.width / 2 + margin
  right_arrow_y = edit_track_y
  align_info("->", "next_track", right_arrow_x, right_arrow_y, margin, 0)

  # Create Track
  create_x = sidebar.width - margin
  create_y = screen_height - margin * 2
  align_info("CREATE TRACK", "new_track", create_x, create_y, margin, 2)

  # Append arrays
  draw_but_info[page]["texts"] = texts
  draw_but_info[page]["buts"] = recs
  draw_but_info[page]["actions"] = actions

  # --Pg 2--  (Edit / Create points)
  page = 1

  # --INPUTS--
  recs = []
  texts = {"strings": [], "pos": []}
  content: dict[int, dict] = {}
  actions = []

  # x & y inputs for point input
  gen_pointy_x = 10
  gen_pointy_y = sidebar.height / 6
  rec = align_info("X:", "gen_y", gen_pointy_x, gen_pointy_y, margin, 0, True, 0, 100)

  gen_pointx_x = 10
  gen_pointx_y = rec.y + rec.height * 2
  gen_y_rec = align_info(
    "Y:", "gen_x", gen_pointx_x, gen_pointx_y, margin, 0, True, 1, 100
  )

  # Update Index
  update_i_x = sidebar.width - margin
  update_i_y = gen_pointy_y
  rec = align_info(
    "Change Index", "change_i", update_i_x, update_i_y, margin, 2, True, 2, 54
  )
  content[2]["string"] = "NAN"

  # Finish index
  finish_i_x = update_i_x
  finish_i_y = gen_pointx_y
  rec = align_info(
    "Finish Index:", "finish_i", finish_i_x, finish_i_y, margin, 2, True, 3, 50
  )
  content[3]["string"] = str(track_info["finish"])

  draw_input_info[page]["labels"] = texts
  draw_input_info[page]["content"] = content
  draw_input_info[page]["inputs"] = recs
  draw_input_info[page]["actions"] = actions

  # --BUTTONS--
  recs = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Generate New Point
  new_point_submit_x = gen_pointx_x
  new_point_submit_y = gen_y_rec.y + gen_y_rec.height + margin * 2
  align_info(
    "GEN POINT", "gen_point", new_point_submit_x, new_point_submit_y, margin, 0
  )

  # Back Button
  back_x = margin
  back_y = 5 + margin
  align_info("<-", "page1", back_x, back_y, margin, 0)

  # Next Button
  next_x = sidebar.width - margin
  next_y = 5 + margin
  align_info("->", "page3", next_x, next_y, margin, 2)

  # Edit Points
  edit_point_x = sidebar.width / 2
  edit_point_y = screen_height * 3 / 4
  align_info("EDIT POINTS", "edit_points", edit_point_x, edit_point_y, margin, 1)

  # Generate Track
  gen_track_x = sidebar.width / 2
  gen_track_y = screen_height * 3 / 4 + 50
  align_info("GENERATE TRACK", "gen_track", gen_track_x, gen_track_y, margin, 1)

  # Toggle Grid
  toggle_grid_x = sidebar.width - margin
  toggle_grid_y = sidebar.height - margin * 2
  align_info("TOGGLE GRID", "toggle_grid", toggle_grid_x, toggle_grid_y, margin, 2)

  draw_but_info[page]["texts"] = texts
  draw_but_info[page]["buts"] = recs
  draw_but_info[page]["actions"] = actions

  # --Pg 3--  (Name track and print it)
  page = 2

  # --INPUTS--
  recs = []
  texts = {"strings": [], "pos": []}
  content: dict[int, dict] = {}
  actions = []

  # Name input
  set_name_x = sidebar.width / 2
  set_name_y = screen_height / 5
  rec = align_info("Name:", "set_name", set_name_x, set_name_y, margin, 1, True, 0, 250)
  content[0]["string"] = track_info["name"]

  draw_input_info[page]["labels"] = texts
  draw_input_info[page]["content"] = content
  draw_input_info[page]["inputs"] = recs
  draw_input_info[page]["actions"] = actions

  # --BUTTONS--
  recs = []
  texts = {"strings": [], "pos": []}
  actions = []

  # Back button
  back_x = margin
  back_y = 5 + margin
  align_info("<-", "page2", back_x, back_y, margin, 0)

  # Print main track points to terminal
  print_x = sidebar.width / 2
  print_y = screen_height * 3 / 4
  align_info(
    "Print Track & Calculate\nTrack Length", "print", print_x, print_y, margin, 1
  )

  draw_but_info[page]["texts"] = texts
  draw_but_info[page]["buts"] = recs
  draw_but_info[page]["actions"] = actions

  return draw_but_info, draw_input_info


def find_action_index(input_actions: list[str], desired_action: str) -> int | None:
  for i, action in enumerate(input_actions):
    if desired_action == action:
      return i
  return None


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
