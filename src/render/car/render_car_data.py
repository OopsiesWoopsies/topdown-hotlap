import pyray as pr

from game.car.car_body import Car


class RenderCarData:
  def __init__(self, car: Car, screen_width: int, screen_height: int):
    self.car = car
    engine = car.engine

    self.anti_stall = False
    self.shift_light = (74, 250, 0, 200)  # A shade of green

    self.screen_width = screen_width
    self.screen_height = screen_height
    self.screen_width_half = screen_width / 2

    # Gear text
    self.gear_draw_font_size = 30
    match engine.gear:
      case 1:
        self.curr_gear_text = "N"
      case 0:
        self.curr_gear_text = "R"
      case _:
        self.curr_gear_text = str(engine.gear - 1)

    text_width = pr.measure_text(self.curr_gear_text, self.gear_draw_font_size)
    self.gear_draw_pos_x = int(self.screen_width_half - text_width / 2)
    self.gear_draw_pos_y = screen_height - 80

    # Anti stall text
    self.anti_stall_draw_font_size = 20
    self.anti_stall_text = "AS: OFF"

    text_width = pr.measure_text(self.anti_stall_text, self.anti_stall_draw_font_size)
    self.anti_stall_draw_pos_x = int(self.screen_width_half - text_width / 2)
    self.anti_stall_draw_pos_y = screen_height - 40

    # Speed text (kph and mph)
    self.speed_kph_draw_font_size = 20
    self.speed_kph_text = "0 kph"

    text_width = pr.measure_text(self.speed_kph_text, self.speed_kph_draw_font_size)
    self.speed_kph_draw_pos_x = int(self.screen_width_half - text_width / 2 - 100)
    self.speed_kph_draw_pos_y = screen_height - 70

    self.speed_mph_draw_font_size = 18
    self.speed_mph_text = "0 mph"

    text_width = pr.measure_text(self.speed_mph_text, self.speed_mph_draw_font_size)
    self.speed_mph_draw_pos_x = int(self.screen_width_half - text_width / 2 - 100)
    self.speed_mph_draw_pos_y = screen_height - 50

    # RPM text
    self.rpm_draw_font_size = 20
    self.rpm_text = f"{round(engine.rpm)} RPM"

    text_width = pr.measure_text(self.rpm_text, self.rpm_draw_font_size)
    self.rpm_draw_pos_x = int(self.screen_width_half - text_width / 2 + 100)
    self.rpm_draw_pos_y = screen_height - 70

    # Dashboard
    x_offset = self.screen_width_half * 0.07
    y_offset = screen_height * 0.01
    self.bl = (self.screen_width_half - 200 - x_offset, screen_height)  # Bottom-left
    self.br = (self.screen_width_half + 200 + x_offset, screen_height)  # Bottom-right
    self.tr = (
      self.screen_width_half + 150 + x_offset,
      screen_height - 100 - y_offset,
    )  # Top-right
    self.tl = (
      self.screen_width_half - 150 - x_offset,
      screen_height - 100 - y_offset,
    )  # Top-left

  def update_scale(self, new_screen_width: int, new_screen_height: int):
    self.screen_width = new_screen_width
    self.screen_height = new_screen_height
    self.screen_width_half = self.screen_width / 2

    # Dashboard
    x_offset = self.screen_width_half * 0.07
    y_offset = self.screen_height * 0.01
    self.bl = (
      self.screen_width_half - 200 - x_offset,
      self.screen_height,
    )  # Bottom-left
    self.br = (
      self.screen_width_half + 200 + x_offset,
      self.screen_height,
    )  # Bottom-right
    self.tr = (
      self.screen_width_half + 150 + x_offset,
      self.screen_height - 100 - y_offset,
    )  # Top-right
    self.tl = (
      self.screen_width_half - 150 - x_offset,
      self.screen_height - 100 - y_offset,
    )  # Top-left

  def update_data(self):
    engine = self.car.engine

    # Shift lights
    eng_rpm_ratio = engine.rpm / engine.peak_rpm
    if eng_rpm_ratio > 1.05:
      self.shift_light = (27, 119, 239, 200)  # A shade of blue
    elif eng_rpm_ratio > 0.6:
      self.shift_light = (255, 239, 1, 200)  # A shade of yellow
    else:
      self.shift_light = (74, 250, 0, 200)  # A shade of green

    # Gear text
    match engine.gear:
      case 1:
        self.curr_gear_text = "N"
      case 0:
        self.curr_gear_text = "R"
      case _:
        self.curr_gear_text = str(engine.gear - 1)

    text_width = pr.measure_text(self.curr_gear_text, self.gear_draw_font_size)
    self.gear_draw_pos_x = int(self.screen_width_half - text_width / 2)
    self.gear_draw_pos_y = self.screen_height - 80

    # Anti stall text
    if engine.anti_stall:
      self.anti_stall_text = "AS: ON"
    else:
      self.anti_stall_text = "AS: OFF"

    text_width = pr.measure_text(self.anti_stall_text, self.anti_stall_draw_font_size)
    self.anti_stall_draw_pos_x = int(self.screen_width_half - text_width / 2)
    self.anti_stall_draw_pos_y = self.screen_height - 40

    # Speed text (kph and mph)
    self.speed_kph_draw_font_size = 20
    speed_kph = pr.vector2_length(self.car.velo) * 3.6
    self.speed_kph_text = f"{round(speed_kph)} kph"

    text_width = pr.measure_text(self.speed_kph_text, self.speed_kph_draw_font_size)
    self.speed_kph_draw_pos_x = int(self.screen_width_half - text_width / 2 - 100)
    self.speed_kph_draw_pos_y = self.screen_height - 70

    self.speed_mph_draw_font_size = 18
    speed_mph = speed_kph * 0.621371
    self.speed_mph_text = f"{round(speed_mph)} mph"

    text_width = pr.measure_text(self.speed_mph_text, self.speed_mph_draw_font_size)
    self.speed_mph_draw_pos_x = int(self.screen_width_half - text_width / 2 - 100)
    self.speed_mph_draw_pos_y = self.screen_height - 50

    # RPM text
    self.rpm_draw_font_size = 20
    self.rpm_text = f"{round(engine.rpm)} RPM"

    text_width = pr.measure_text(self.rpm_text, self.rpm_draw_font_size)
    self.rpm_draw_pos_x = int(self.screen_width_half - text_width / 2 + 100)
    self.rpm_draw_pos_y = self.screen_height - 70

  def draw(self):
    # Shift light above dashboard
    pr.draw_rectangle_rounded(
      pr.Rectangle(self.tl[0], self.tl[1] - 10, self.tr[0] - self.tl[0], 8),
      0.2,
      10,
      self.shift_light,
    )

    # Dashboard
    pr.draw_triangle(self.bl, self.br, self.tr, (0, 0, 0, 120))  # Translucent black
    pr.draw_triangle(self.bl, self.tr, self.tl, (0, 0, 0, 120))  # Translucent black

    pr.draw_text(
      self.curr_gear_text,
      self.gear_draw_pos_x,
      self.gear_draw_pos_y,
      self.gear_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      self.anti_stall_text,
      self.anti_stall_draw_pos_x,
      self.anti_stall_draw_pos_y,
      self.anti_stall_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      self.speed_kph_text,
      self.speed_kph_draw_pos_x,
      self.speed_kph_draw_pos_y,
      self.speed_kph_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      self.speed_mph_text,
      self.speed_mph_draw_pos_x,
      self.speed_mph_draw_pos_y,
      self.speed_mph_draw_font_size,
      pr.WHITE,
    )
    pr.draw_text(
      self.rpm_text,
      self.rpm_draw_pos_x,
      self.rpm_draw_pos_y,
      self.rpm_draw_font_size,
      pr.WHITE,
    )
