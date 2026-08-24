import pyray as pr


class Control:
  def __init__(self):
    # Keybinds
    self.throttle_keybind = pr.MOUSE_LEFT_BUTTON
    self.brake_keybind = pr.MOUSE_RIGHT_BUTTON
    self.quick_keybind = pr.KEY_LEFT_SHIFT
    self.stop_keybind = pr.KEY_LEFT_CONTROL

    self.shift_up_keybind = pr.KEY_E
    self.shift_down_keybind = pr.KEY_Q
    self.shift_up_key_up = True
    self.shift_down_key_up = True

    # Steering
    self.steer_amt = 0.0
    self.sens = 1
    self.straight_steer_margin = 0.01

    # Throttle & Brake
    self.throttle_amt = 0.0
    self.add_throttle = 1
    self.sub_throttle = 4

    self.brake_amt = 0.0
    self.add_brake = 2
    self.sub_brake = 4

    self.quick_amt = 2

  def get_inputs(self, dt: float) -> dict[str]:
    throttle = pr.is_mouse_button_down(self.throttle_keybind)
    brake = pr.is_mouse_button_down(self.brake_keybind)
    quick = pr.is_key_down(self.quick_keybind)
    stop = pr.is_key_down(self.stop_keybind)
    req_shift_up_key_down = pr.is_key_down(self.shift_up_keybind)
    req_shift_down_key_down = pr.is_key_down(self.shift_down_keybind)

    shift_up = False
    shift_down = False

    if self.shift_up_key_up and req_shift_up_key_down:
      shift_up = True
      self.shift_up_key_up = False
    elif not req_shift_up_key_down:
      self.shift_up_key_up = True
    if self.shift_down_key_up and req_shift_down_key_down:
      shift_down = True
      self.shift_down_key_up = False
    elif not req_shift_down_key_down:
      self.shift_down_key_up = True

    if stop:
      return {
        "throttle": self.throttle_amt,
        "brake": self.brake_amt,
        "shift_up": shift_up,
        "shift_down": shift_down,
      }

    if throttle:
      if quick:
        self.throttle_amt += self.quick_amt * dt
      self.brake_amt = 0.0
      self.throttle_amt += self.add_throttle * dt
    else:
      if quick:
        self.throttle_amt -= self.quick_amt * dt
      self.throttle_amt -= self.sub_throttle * dt

    if brake:
      if quick:
        self.brake_amt += self.quick_amt * dt
      self.throttle_amt = 0.0
      self.brake_amt += self.add_brake * dt
    else:
      if quick:
        self.brake_amt -= self.quick_amt * dt
      self.brake_amt -= self.sub_brake * dt

    if self.throttle_amt < 0.0:
      self.throttle_amt = 0.0
    elif self.throttle_amt > 1.0:
      self.throttle_amt = 1.0

    if self.brake_amt < 0.0:
      self.brake_amt = 0.0
    elif self.brake_amt > 1.0:
      self.brake_amt = 1.0

    return {
      "throttle": self.throttle_amt,
      "brake": self.brake_amt,
      "shift_up": shift_up,
      "shift_down": shift_down,
    }

  def get_steering(self) -> float:
    center_x = pr.get_screen_width() / 2
    self.steer_amt = self.sens * (pr.get_mouse_position().x - center_x) / center_x

    if abs(self.steer_amt) < self.straight_steer_margin:
      self.steer_amt = 0
    if self.steer_amt < -1.0:
      self.steer_amt = -1.0
    elif self.steer_amt > 1.0:
      self.steer_amt = 1.0
    return self.steer_amt

  def draw(self, steer_deg: float):
    # Throttle and brake
    throt_draw_x = 10
    throt_draw_y = 650
    throt_draw_width = 70
    throt_draw_height = 15

    brake_draw_x = 10
    brake_draw_y = 680
    brake_draw_width = 70
    brake_draw_height = 15

    throttle_rec_1 = pr.Rectangle(
      throt_draw_x,
      throt_draw_y,
      throt_draw_width * self.throttle_amt,
      throt_draw_height,
    )
    throttle_rec_2 = pr.Rectangle(
      throt_draw_x + throt_draw_width * 2,
      throt_draw_y + throt_draw_height,
      throt_draw_width * self.throttle_amt,
      throt_draw_height,
    )
    throttle_otln = pr.Rectangle(
      throt_draw_x, throt_draw_y, throt_draw_width * 2, throt_draw_height
    )
    brake_otln = pr.Rectangle(
      brake_draw_x, brake_draw_y, brake_draw_width * 2, brake_draw_height
    )
    brake_rec_1 = pr.Rectangle(
      brake_draw_x,
      brake_draw_y,
      brake_draw_width * self.brake_amt,
      brake_draw_height,
    )
    brake_rec_2 = pr.Rectangle(
      brake_draw_x + brake_draw_width * 2,
      brake_draw_y + brake_draw_height,
      brake_draw_width * self.brake_amt,
      brake_draw_height,
    )
    origin = pr.Vector2(0, 0)

    pr.draw_rectangle_pro(throttle_rec_1, origin, 0, pr.GREEN)
    pr.draw_rectangle_pro(throttle_rec_2, origin, 180, pr.GREEN)
    pr.draw_rectangle_lines_ex(throttle_otln, 2, pr.LIME)
    pr.draw_rectangle_pro(brake_rec_1, origin, 0, pr.RED)
    pr.draw_rectangle_pro(brake_rec_2, origin, 180, pr.RED)
    pr.draw_rectangle_lines_ex(brake_otln, 2, pr.Color(152, 19, 28, 255))

    # Steering wheel (temp rectangle)
    wheel = pr.Rectangle(1100, 650, 100, 50)
    origin = pr.Vector2(wheel.width / 2, wheel.height / 2)
    pr.draw_rectangle_pro(
      wheel,
      origin,
      steer_deg * 180 / 25,
      pr.DARKPURPLE,
    )
