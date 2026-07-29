import math

import pyray as pr


class Engine:
  def __init__(self):
    # Engine constants
    self.trans_efficiency = 0.95
    self.gear_ratios = [3.5, 2.9, 2.4, 2.0, 1.7, 1.46, 1.28, 1.13]
    self.final_drive = 4.0
    self.gear = 0
    self.clutch = 1.0
    self.inertia = 0.1  # kg*m^2
    self.engine_brake = 75.0  # Nm
    self.clutch_stiffness = 15.0
    self.max_clutch = 2000.0
    self.max_t_rate = 80000.0  # Nm/s

    # Limits
    self.redline = 15000.0  # RPM
    self.peak_rpm = 11000.0  # RPM
    self.idle_rpm = 5000.0  # RPM
    self.max_omega = self.redline * 2 * math.pi / 60

    # Shift timing state
    self.shift_timer = 0.0
    self.shift_cooldown = 0.25  # s

    # Vars
    self.rpm = self.idle_rpm
    self.omega = self.idle_rpm * 2.0 * math.pi / 60.0
    self.clutch_t = 0.0
    self.net_engine_t = 0.0

  def torque_curve(self, rpm: float) -> float:
    max_t = 600.0  # Nm

    if rpm <= self.peak_rpm:
      x = rpm / self.peak_rpm
      return max_t * (1.0 - (1.0 - x) ** 2)

    x = (rpm - self.peak_rpm) / (self.redline - self.peak_rpm)
    x = pr.clamp(x, 0.0, 1.0)
    return max_t * (1.0 - 0.45 * x - 0.55 * x * x)

  def update_clutch_torque(self, dt: float, throttle: float, avg_tire_omega: float):
    if self.shift_timer > 0.0:
      self.shift_timer -= dt

    gear_ratio = self.gear_ratios[self.gear]
    engine_t = self.torque_curve(self.rpm) * throttle

    # Engine braking
    if not throttle:
      engine_t -= self.engine_brake * self.rpm / self.redline

    # Idle torque
    if self.rpm < self.idle_rpm:
      idle_error = self.idle_rpm - self.rpm
      engine_t += min(idle_error * 0.05, 80.0)

    # Cut power upon engine redline
    if self.rpm >= self.redline:
      engine_t = 0.0

    # Calculate difference between engine rpm and gearbox rpm to align gearbox to engine
    gearbox_omega = avg_tire_omega * gear_ratio * self.final_drive
    slip = self.omega - gearbox_omega

    desired = slip * self.clutch_stiffness
    desired = pr.clamp(
      desired,
      -self.max_clutch,
      self.max_clutch,
    )

    delta = desired - self.clutch_t
    max_delta = self.max_t_rate * dt

    delta = pr.clamp(delta, -max_delta, max_delta)

    self.clutch_t += delta
    self.net_engine_t = engine_t - self.clutch_t

    self.omega += (self.net_engine_t / self.inertia) * dt
    self.omega = pr.clamp(self.omega, 0.0, self.max_omega)
    self.rpm = self.omega * 60 / (2 * math.pi)

  def get_drive_torque(self) -> float:
    gear_ratio = self.gear_ratios[self.gear]
    return (
      self.clutch_t
      * gear_ratio
      * self.final_drive
      * self.trans_efficiency
      * self.clutch
    )

  # Add manual shifting later and make this optional
  def update_shift(
    self, dt: float, rpm: float, is_slipping: bool, avg_tire_omega: float
  ):
    if self.shift_timer > 0.0:
      return

    if not is_slipping and self.gear < len(self.gear_ratios) - 1 and rpm > 12500:
      self.gear += 1
      new_ratio = self.gear_ratios[self.gear]

      target_omega = avg_tire_omega * new_ratio * self.final_drive
      self.omega = pr.lerp(
        self.omega,
        target_omega,
        min(1.0, 20.0 * dt),
      )
      self.rpm = self.omega * 60 / (2 * math.pi)
      self.shift_timer = self.shift_cooldown

    elif self.gear > 0 and rpm < 6500:
      self.gear -= 1
      new_ratio = self.gear_ratios[self.gear]

      target_omega = avg_tire_omega * new_ratio * self.final_drive
      self.omega = pr.lerp(
        self.omega,
        target_omega,
        min(1.0, 20.0 * dt),
      )
      self.rpm = self.omega * 60 / (2 * math.pi)
      self.shift_timer = self.shift_cooldown
