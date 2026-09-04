import pyray as pr


class RenderControls:
  def __init__(self, screen_width: int, screen_height: int):
    # Draw coords
    self.throt_draw_x = 10
    self.throt_draw_y = screen_height * 0.9
    self.throt_draw_width = 70
    self.throt_draw_height = 15

    self.brake_draw_x = 10
    self.brake_draw_y = self.throt_draw_y + 30
    self.brake_draw_width = 70
    self.brake_draw_height = 15

    self.steer_wheel_width = 100
    self.steer_wheel_height = 50
    self.steer_wheel_x = screen_width - self.steer_wheel_width
    self.steer_wheel_y = screen_height * 0.9

    self.wheel = pr.Rectangle(
      self.steer_wheel_x,
      self.steer_wheel_y,
      self.steer_wheel_width,
      self.steer_wheel_height,
    )
    self.wheel_origin = pr.Vector2(
      self.steer_wheel_width / 2, self.steer_wheel_height / 2
    )

    self.throttle_rec_1 = pr.Rectangle(
      self.throt_draw_x,
      self.throt_draw_y,
      self.throt_draw_width * 0,
      self.throt_draw_height,
    )
    self.throttle_rec_2 = pr.Rectangle(
      self.throt_draw_x + self.throt_draw_width * 2,
      self.throt_draw_y + self.throt_draw_height,
      self.throt_draw_width * 0,
      self.throt_draw_height,
    )
    self.throttle_otln = pr.Rectangle(
      self.throt_draw_x,
      self.throt_draw_y,
      self.throt_draw_width * 2,
      self.throt_draw_height,
    )
    self.brake_otln = pr.Rectangle(
      self.brake_draw_x,
      self.brake_draw_y,
      self.brake_draw_width * 2,
      self.brake_draw_height,
    )
    self.brake_rec_1 = pr.Rectangle(
      self.brake_draw_x,
      self.brake_draw_y,
      self.brake_draw_width * 0,
      self.brake_draw_height,
    )
    self.brake_rec_2 = pr.Rectangle(
      self.brake_draw_x + self.brake_draw_width * 2,
      self.brake_draw_y + self.brake_draw_height,
      self.brake_draw_width * 0,
      self.brake_draw_height,
    )
    self.tb_origin = pr.Vector2(0, 0)

  def update_draw_positions(self, screen_width: int, screen_height: int):
    self.throt_draw_y = screen_height * 0.9
    self.brake_draw_y = self.throt_draw_y + 30
    self.steer_wheel_y = screen_height * 0.9
    self.steer_wheel_x = screen_width - self.wheel.width

    self.throttle_rec_1 = pr.Rectangle(
      self.throt_draw_x,
      self.throt_draw_y,
      0,
      self.throt_draw_height,
    )
    self.throttle_rec_2 = pr.Rectangle(
      self.throt_draw_x + self.throt_draw_width * 2,
      self.throt_draw_y + self.throt_draw_height,
      0,
      self.throt_draw_height,
    )
    self.throttle_otln = pr.Rectangle(
      self.throt_draw_x,
      self.throt_draw_y,
      self.throt_draw_width * 2,
      self.throt_draw_height,
    )
    self.brake_otln = pr.Rectangle(
      self.brake_draw_x,
      self.brake_draw_y,
      self.brake_draw_width * 2,
      self.brake_draw_height,
    )
    self.brake_rec_1 = pr.Rectangle(
      self.brake_draw_x,
      self.brake_draw_y,
      0,
      self.brake_draw_height,
    )
    self.brake_rec_2 = pr.Rectangle(
      self.brake_draw_x + self.brake_draw_width * 2,
      self.brake_draw_y + self.brake_draw_height,
      0,
      self.brake_draw_height,
    )

    self.wheel = pr.Rectangle(
      self.steer_wheel_x,
      self.steer_wheel_y,
      self.steer_wheel_width,
      self.steer_wheel_height,
    )

  def draw(self, steer_deg: float, inputs: dict[str, float | bool]):
    # Throttle and brake
    throttle_amt = inputs["throttle"]
    brake_amt = inputs["brake"]
    self.throttle_rec_1.width = self.throt_draw_width * throttle_amt
    self.throttle_rec_2.width = self.throt_draw_width * throttle_amt
    self.brake_rec_1.width = self.brake_draw_width * brake_amt
    self.brake_rec_2.width = self.brake_draw_width * brake_amt

    pr.draw_rectangle_pro(self.throttle_rec_1, self.tb_origin, 0, pr.GREEN)
    pr.draw_rectangle_pro(self.throttle_rec_2, self.tb_origin, 180, pr.GREEN)
    pr.draw_rectangle_lines_ex(self.throttle_otln, 2, pr.LIME)
    pr.draw_rectangle_pro(self.brake_rec_1, self.tb_origin, 0, pr.RED)
    pr.draw_rectangle_pro(self.brake_rec_2, self.tb_origin, 180, pr.RED)
    pr.draw_rectangle_lines_ex(self.brake_otln, 2, pr.Color(152, 19, 28, 255))

    # Steering wheel (temp rectangle)
    pr.draw_rectangle_pro(
      self.wheel,
      self.wheel_origin,
      steer_deg * 180 / 25,
      pr.DARKPURPLE,
    )
