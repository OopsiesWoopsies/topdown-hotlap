import math

import pyray as pr

OMEGA_TO_RPM = 60.0 / (2 * math.pi)
RPM_TO_OMEGA = 2.0 * math.pi / 60.0


class Engine:
  def __init__(self):
    # Engine constants
    self.trans_efficiency = 0.95
    self.gear_ratios = [-3.00, 0.0, 3.40, 2.75, 2.30, 1.95, 1.68, 1.46, 1.26, 1.01]
    self.final_drive = 4.6
    self.gear = 1
    self.overall_inertia = 0.1  # kg*m^2
    self.engine_brake = 75.0  # Nm
    self.max_clutch = 1100.0  # Nm
    self.max_t = 550.0  # Nm

    # Limits
    self.redline = 15000.0  # RPM
    self.peak_rpm = 11000.0  # RPM
    self.idle_rpm = 4000.0  # RPM
    self.max_omega = self.redline * RPM_TO_OMEGA
    self.idle_omega = self.idle_rpm * RPM_TO_OMEGA

    # Shift timing state
    self.shift_timer = 0.0
    self.shift_cd = 0.025  # s
    self.clutch_reengage_cd = 0.04  # s
    self.clutch_reengage_timer = 0.0

    # Vars
    self.rpm = self.idle_rpm
    self.omega = self.idle_omega
    self.trans_omega = 0.0
    self.clutch_t = 0.0
    self.net_engine_t = 0.0
    self.clutch = 1.0

    # Cases
    self.is_locked = True
    self.is_downshifting = False
    self.is_stalled = False
    self.anti_stall = False

  def torque_curve(self, rpm: float) -> float:
    if rpm <= self.peak_rpm:
      x = rpm / self.peak_rpm
      return self.max_t * (1.0 - (1.0 - x) ** 2)

    x = (rpm - self.peak_rpm) / (self.redline - self.peak_rpm)
    if x < 0.0:
      x = 0.0
    elif x > 1.0:
      x = 1.0
    return self.max_t * (1.0 - 0.45 * x - 0.55 * x * x)

  def update_clutch_torque(self, dt: float, throttle: float, avg_tire_omega: float):
    if self.shift_timer > 0.0:
      self.shift_timer -= dt
      self.clutch_reengage_timer = self.clutch_reengage_cd
    elif self.clutch_reengage_timer > 0.0:
      self.clutch_reengage_timer -= dt

    if self.shift_timer > 0.0:
      self.clutch = 0.0
      if self.is_downshifting and self.gear_ratios[self.gear] > 0:
        if self.omega < self.trans_omega:
          blip_amount = (self.trans_omega - self.omega) / 50.0
          throttle = blip_amount
          if throttle < 0.0:
            throttle = 0.0
          elif throttle > 1.0:
            throttle = 1.0
        else:
          throttle = 0.0
      else:
        throttle = 0.0
    else:
      if self.clutch_reengage_timer > 0.0:
        progress = 1.0 - (self.clutch_reengage_timer / self.clutch_reengage_cd)
        self.clutch = progress
        if self.clutch < 0.0:
          self.clutch = 0.0
        elif self.clutch > 1.0:
          self.clutch = 1.0
        throttle *= self.clutch
      else:
        self.clutch = 1.0

    if self.is_stalled:
      throttle = 0.0
      self.clutch = 0.0
      if self.gear <= 2:
        self.is_stalled = False
        self.rpm = self.idle_rpm
        self.omega = self.idle_omega

    elif self.anti_stall:
      throttle = 0.0
      self.clutch = 0.0
      if self.gear <= 2:
        self.anti_stall = False

    else:
      if self.rpm < 1000:
        self.is_stalled = True

      elif self.gear > 2 and self.rpm < self.idle_rpm - 500:
        self.anti_stall = True

      # Launch assist
      if (
        not self.is_stalled
        and not self.anti_stall
        and self.gear <= 2
        and self.rpm < self.idle_rpm + 1500.0
      ):
        launch_clutch = (self.rpm - self.idle_rpm) / 1500.0
        if launch_clutch < 0.0:
          launch_clutch = 0.0
        elif launch_clutch > 1.0:
          launch_clutch = 1.0
        self.clutch = min(self.clutch, launch_clutch)

    # Torque calculations
    gear_ratio = self.gear_ratios[self.gear]
    self.trans_omega = avg_tire_omega * gear_ratio * self.final_drive

    if self.is_stalled:
      engine_t = 0.0
      engine_t -= self.engine_brake * (self.rpm / self.redline)
    else:
      engine_t = self.torque_curve(self.rpm) * throttle
      engine_t -= self.engine_brake * (self.rpm / self.redline) * (1.0 - throttle)

      # Idle torque / Anti-stall
      if self.rpm < self.idle_rpm:
        idle_error = self.idle_rpm - self.rpm
        base_idle_t = self.engine_brake * (self.idle_rpm / self.redline)
        engine_t += base_idle_t + min(idle_error * 0.5, 50.0)

    # Calculate difference between engine rpm and gearbox rpm to align gearbox to engine
    slip = self.omega - self.trans_omega
    sync_torque = (slip / dt) * self.overall_inertia if dt > 0 else 0.0
    max_capacity = self.max_clutch * self.clutch

    if (
      self.gear != 1
      and self.clutch > 0.0
      and abs(sync_torque) <= max_capacity
      and abs(slip) < 15.0
    ):
      self.is_locked = True
      self.omega = self.trans_omega
      self.net_engine_t = 0.0
      self.clutch_t = engine_t
      if self.clutch_t < -max_capacity:
        self.clutch_t = -max_capacity
      elif self.clutch_t > max_capacity:
        self.clutch_t = max_capacity
    else:
      self.is_locked = False

      if self.gear == 1 or self.clutch == 0.0:
        self.clutch_t = 0.0
      else:
        self.clutch_t = sync_torque
        if self.clutch_t < -max_capacity:
          self.clutch_t = -max_capacity
        elif self.clutch_t > max_capacity:
          self.clutch_t = max_capacity

      # Engine omega updates
      self.net_engine_t = engine_t - self.clutch_t
      self.omega += (self.net_engine_t / self.overall_inertia) * dt

    if self.omega < 0.0:
      self.omega = 0.0
    elif self.omega > self.max_omega:
      self.omega = self.max_omega
    self.rpm = self.omega * OMEGA_TO_RPM

  def get_drive_torque(self) -> float:
    gear_ratio = self.gear_ratios[self.gear]
    return self.clutch_t * gear_ratio * self.final_drive * self.trans_efficiency

  def get_reflected_inertia(self) -> float:
    if not self.is_locked:
      return 0.0
    total_ratio = self.gear_ratios[self.gear] * self.final_drive
    return self.overall_inertia * total_ratio**2

  def update_shift(
    self, is_slipping: bool, inputs: dict[str, float | bool], auto_shift: bool = True
  ):
    if self.shift_timer > 0.0 or self.clutch_reengage_timer > 0.0:
      return

    if not auto_shift:
      if inputs["shift_up"] and self.gear < len(self.gear_ratios) - 1:
        self.gear += 1
        self.shift_timer = self.shift_cd
        self.is_downshifting = False

      elif inputs["shift_down"] and self.gear > 0:
        curr_gear_ratio = self.gear_ratios[self.gear]
        if curr_gear_ratio != 0.0:
          new_rpm = (
            self.gear_ratios[self.gear - 1] / self.gear_ratios[self.gear] * self.rpm
          )
        else:
          new_rpm = self.idle_rpm
        if new_rpm >= 15000:
          return
        self.gear -= 1
        self.shift_timer = self.shift_cd
        self.is_downshifting = True
      return

    if is_slipping:
      return
    if self.gear < len(self.gear_ratios) - 1 and self.rpm > 13000:
      self.gear += 1
      self.shift_timer = self.shift_cd
      self.is_downshifting = False

    elif self.gear > 0 and self.rpm < 6500:
      self.gear -= 1
      self.shift_timer = self.shift_cd
      self.is_downshifting = True
