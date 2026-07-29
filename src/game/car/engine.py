import math

import pyray as pr

OMEGA_TO_RPM = 60.0 / (2 * math.pi)
RPM_TO_OMEGA = 2.0 * math.pi / 60.0


class Engine:
  def __init__(self):
    # Engine constants
    self.trans_efficiency = 0.95
    self.gear_ratios = [3.5, 2.9, 2.4, 2.0, 1.7, 1.46, 1.28, 1.13]
    self.final_drive = 4.0
    self.gear = 0
    self.inertia = 0.1  # kg*m^2
    self.engine_brake = 75.0  # Nm
    self.max_clutch = 2000.0
    self.max_t = 550.0  # Nm

    # Limits
    self.redline = 15000.0  # RPM
    self.peak_rpm = 11000.0  # RPM
    self.idle_rpm = 5000.0  # RPM
    self.max_omega = self.redline * RPM_TO_OMEGA
    self.idle_omega = self.idle_rpm * RPM_TO_OMEGA

    # Shift timing state
    self.shift_timer = 0.0
    self.shift_cooldown = 0.25  # s

    # Vars
    self.rpm = self.idle_rpm
    self.omega = self.idle_omega
    self.clutch_t = 0.0
    self.net_engine_t = 0.0
    self.clutch = 1.0

  def torque_curve(self, rpm: float) -> float:
    if rpm <= self.peak_rpm:
      x = rpm / self.peak_rpm
      return self.max_t * (1.0 - (1.0 - x) ** 2)

    x = (rpm - self.peak_rpm) / (self.redline - self.peak_rpm)
    x = pr.clamp(x, 0.0, 1.0)
    return self.max_t * (1.0 - 0.45 * x - 0.55 * x * x)

  def update_clutch_torque(self, dt: float, throttle: float, avg_tire_omega: float):
    gear_ratio = self.gear_ratios[self.gear]
    engine_t = self.torque_curve(self.rpm) * throttle
    gearbox_omega = avg_tire_omega * gear_ratio * self.final_drive

    # Engine braking
    if not throttle:
      engine_t -= self.engine_brake * self.rpm / self.redline

    # Idle torque
    if self.rpm < self.idle_rpm:
      idle_error = self.idle_rpm - self.rpm
      base_idle_t = self.engine_brake * (self.idle_rpm / self.redline)
      engine_t += base_idle_t + min(idle_error * 0.1, 80.0)

    # Cut power upon engine redline
    if self.rpm >= self.redline:
      engine_t = 0.0
    if self.shift_timer > 0.0:
      self.shift_timer -= dt
      self.clutch = 0.0
      target_omega = gearbox_omega
      self.omega = pr.lerp(self.omega, target_omega, 15.0 * dt)
    elif self.rpm < self.idle_rpm + 500:
      self.clutch = abs(avg_tire_omega) / self.idle_omega
      self.clutch = pr.clamp(self.clutch, 0.0, 1.0)
    else:
      self.clutch = 1.0

    # Calculate difference between engine rpm and gearbox rpm to align gearbox to engine
    slip = self.omega - gearbox_omega
    sync_torque = (slip / dt) * self.inertia
    max_capacity = self.max_clutch * self.clutch

    if self.clutch and abs(sync_torque) <= max_capacity:
      self.omega = gearbox_omega
      self.net_engine_t = 0.0
      self.clutch_t = pr.clamp(engine_t, -max_capacity, max_capacity)
    else:
      if self.clutch == 0.0:
        self.clutch_t = 0.0
      else:
        self.clutch_t = math.copysign(max_capacity, slip)

      self.net_engine_t = engine_t - self.clutch_t
      self.omega += (self.net_engine_t / self.inertia) * dt

    self.omega = pr.clamp(self.omega, 0.0, self.max_omega)
    self.rpm = self.omega * OMEGA_TO_RPM

  def get_drive_torque(self) -> float:
    gear_ratio = self.gear_ratios[self.gear]
    return self.clutch_t * gear_ratio * self.final_drive * self.trans_efficiency

  # Add manual shifting later and make this optional
  def update_shift(self, is_slipping: bool):
    if self.shift_timer > 0.0:
      return

    if (
      not is_slipping
      and self.gear < len(self.gear_ratios) - 1
      and (self.rpm > 12500 or (self.rpm > 12000 and self.gear + 1 >= 6))
    ):
      self.gear += 1
      self.shift_timer = self.shift_cooldown

    elif self.gear > 0 and self.rpm < 6500:
      self.gear -= 1
      self.shift_timer = self.shift_cooldown
