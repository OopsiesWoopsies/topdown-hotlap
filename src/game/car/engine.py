import math

import pyray as pr

ENGINE_BRAKE = 75.0  # Nm


class Engine:
  def __init__(self):
    # Engine constants
    self.trans_efficiency = 0.95
    self.gear_ratios = [3.5, 2.9, 2.4, 2.0, 1.7, 1.46, 1.28, 1.13]
    self.final_drive = 4.0
    self.gear = 0
    self.clutch = 1.0
    self.inertia = 0.1  # kg*m^2

    # Limits
    self.redline = 15000.0  # RPM
    self.peak_rpm = 10000.0  # RPM
    self.idle_rpm = 5000.0  # RPM

    self.rpm = self.idle_rpm
    self.omega = self.idle_rpm * 2.0 * math.pi / 60.0

  def get_rpm(self) -> float:
    return self.rpm

  def torque_curve(self, rpm: float) -> float:
    max_torque = 400.0  # Nm

    x = rpm / self.peak_rpm
    x = max(0.0, x)

    return max_torque * (1.0 - (x - 1.0) ** 2)

  def get_drive_torque(
    self, dt: float, throttle: float, avg_tire_omega: float
  ) -> float:
    gear_ratio = self.gear_ratios[self.gear]
    target_rpm = (
      abs(avg_tire_omega) * gear_ratio * self.final_drive * 60 / (2 * math.pi)
    )

    self.rpm += (target_rpm - self.rpm) * 10.0 * dt
    self.rpm = pr.clamp(self.rpm, self.idle_rpm, self.redline)

    if throttle > 0:
      engine_torque = self.torque_curve(self.rpm) * throttle
    else:
      engine_torque = -ENGINE_BRAKE

    return engine_torque * gear_ratio * self.final_drive * self.trans_efficiency

  # Remove to add manual shifting later
  def update_shift(self, rpm: float):
    if rpm > 12000 and self.gear < len(self.gear_ratios) - 1:
      self.gear += 1

    elif rpm < 6000 and self.gear > 0:
      self.gear -= 1
