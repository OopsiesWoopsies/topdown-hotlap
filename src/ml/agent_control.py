import numpy as np


class AgentControl:
  def __init__(self, ctrls):
    self.ctrls = ctrls

    self.steer_amt = 0.0
    self.throttle_amt = 0.0
    self.brake_amt = 0.0

    self.throttle_pressed = False
    self.brake_pressed = False

    self.prev_shift_req = 0
    self.shift_up_pending = False
    self.shift_down_pending = False

  def set_action(self, action):
    steering, longitudinal, shift = np.clip(action, -1.0, 1.0)

    self.steer_amt = float(steering)
    self.throttle_pressed = longitudinal > 0.1
    self.brake_pressed = longitudinal < -0.1

    shift_req = 1 if shift > 0.5 else -1 if shift < -0.5 else 0

    self.shift_up_pending = shift_req == 1 and self.prev_shift_req != 1
    self.shift_down_pending = shift_req == -1 and self.prev_shift_req != -1

    self.prev_shift_req = shift_req

  def get_dynamic_inputs(self, dt):
    if self.throttle_pressed:
      self.brake_amt = 0.0
      self.throttle_amt += self.ctrls.add_throttle * dt
    else:
      self.throttle_amt -= self.ctrls.sub_throttle * dt

    if self.brake_pressed:
      self.throttle_amt = 0.0
      self.brake_amt += self.ctrls.add_brake * dt
    else:
      self.brake_amt -= self.ctrls.sub_brake * dt

    self.throttle_amt = float(np.clip(self.throttle_amt, 0.0, 1.0))
    self.brake_amt = float(np.clip(self.brake_amt, 0.0, 1.0))

    inputs = {
      "throttle": self.throttle_amt,
      "brake": self.brake_amt,
      "shift_up": self.shift_up_pending,
      "shift_down": self.shift_down_pending,
    }

    self.shift_up_pending = False
    self.shift_down_pending = False

    return inputs

  def get_static_inputs(self):
    return {
      "throttle": self.throttle_amt,
      "brake": self.brake_amt,
      "shift_up": False,
      "shift_down": False,
    }

  def get_steering(self):
    return self.steer_amt
