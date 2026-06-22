import math

import pyray as pr

ENGINE_BRAKE = 75.0  # Nm


def torque_curve(rpm: float) -> float:
  peak_rpm = 12000.0  # RPM
  max_torque = 400.0  # Nm

  x = rpm / peak_rpm
  x = pr.clamp(x, 0.0, 1.0)

  return max_torque * x * (2 - x)


class Engine:
  def __init__(self):
    # Engine constants
    self.trans_efficiency = 0.95
    self.gear_ratios = [3.3, 2.4, 1.85, 1.5, 1.15, 0.97, 0.8, 0.68]
    self.final_drive = 4.0
    self.gear = 0
    self.clutch = 1.0
    self.inertia = 0.1  # kg*m^2

    # Limits
    self.redline = 15000.0  # RPM
    self.idle_rpm = 5000.0  # RPM

    self.rpm = self.idle_rpm
    self.omega = self.idle_rpm * 2.0 * math.pi / 60.0

  def get_rpm(self) -> float:
    return self.rpm

  def get_drive_torque(self, dt: float, wheel_omega: float, throttle: bool) -> float:
    gear_ratio = self.gear_ratios[self.gear]
    target_rpm = wheel_omega * gear_ratio * self.final_drive * 60 / (2 * math.pi)
    if wheel_omega < 5.0 and self.rpm > 3000:
      self.clutch = 0.0
    else:
      self.clutch = 1.0

    self.rpm += (target_rpm - self.rpm) * self.clutch * 10.0 * dt

    self.rpm = max(self.rpm, self.idle_rpm)
    if throttle:
      engine_torque = torque_curve(self.rpm)
    else:
      engine_torque = -ENGINE_BRAKE

    return engine_torque * gear_ratio * self.final_drive * self.trans_efficiency

  # Remove to add manual shifting later
  def update_shift(self, rpm: float):
    if rpm > 12000 and self.gear < len(self.gear_ratios) - 1:
      self.gear += 1

    elif rpm < 6000 and self.gear > 0:
      self.gear -= 1
