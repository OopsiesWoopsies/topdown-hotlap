import pyray as pr


class Keyboard:
  def __init__(self):
    self.throttle_keybind = pr.MOUSE_LEFT_BUTTON
    self.brake_keybind = pr.MOUSE_RIGHT_BUTTON
    self.sens = 1

    self.straight = 0.05

  def get_inputs(self) -> dict[str]:
    throttle = pr.is_mouse_button_down(self.throttle_keybind)
    brake = pr.is_mouse_button_down(self.brake_keybind)

    return {"throttle": throttle, "brake": brake}

  def get_steering(self) -> float:
    center_x = pr.get_screen_width() / 2
    steer = self.sens * (pr.get_mouse_position().x - center_x) / center_x

    if abs(steer) < self.straight:
      steer = 0
    return pr.clamp(steer, -1, 1)
