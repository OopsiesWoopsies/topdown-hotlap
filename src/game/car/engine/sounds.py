import numpy as np
import sounddevice as sd
from scipy.signal import butter, sosfilt, sosfilt_zi


class EngineAudSynthesizer:
  def __init__(
    self,
    cylinders: int,
    redline: float,
    amp: float,
    sample_rate: int = 44100,
    seed: int | None = None,
  ):
    self.cylinders = cylinders
    self.redline = redline
    self.amp = amp
    self.sample_rate = sample_rate
    self.firing_order = cylinders / 2.0
    self.rng = np.random.default_rng(seed)
    self.pulse_width = 0.1
    self.pulse_width = 1 / self.pulse_width

    self.last_rpm = 0.0
    self.last_throttle = 0.0
    self.shifting_gear = False

    self.exhaust_body = butter(
      3,
      [100, 1200],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_low = butter(
      3,
      [40, 1000],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_high = butter(
      3,
      [500, 2000],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_air = butter(
      2,
      [200, 3500],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.rasp_filter = butter(
      2,
      3000,
      btype="lowpass",
      fs=sample_rate,
      output="sos",
    )

    self.phase = 0
    self.body_zi = sosfilt_zi(self.exhaust_body)
    self.low_zi = sosfilt_zi(self.exhaust_low)
    self.high_zi = sosfilt_zi(self.exhaust_high)
    self.air_zi = sosfilt_zi(self.exhaust_air)
    self.rasp_zi = sosfilt_zi(self.rasp_filter)

    self.engine_orders = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0])
    self.engine_weights = np.array([0.19, 0.12, 0.17, 0.08, 0.01, 0.008, 0.00, 0.00])
    self.engine_high_mask = self.engine_orders >= 3.0

    self.mechanical_orders = np.array([1.0, 2.0, 4.0, 6.0, 8.0])
    self.mechanical_weights = np.array([0.28, 0.15, 0.015, 0.005, 0.002])

  def gen_combustion_pulses(
    self,
    base_phase: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    firing_phase = base_phase * self.firing_order
    phase = (firing_phase) % 1.0
    dist = np.minimum(
      phase,
      1.0 - phase,
    )

    dist_scaled = dist * self.pulse_width

    pulse = np.exp(-0.5 * dist_scaled * dist_scaled)
    decay = np.exp(-phase * 10.0)
    pulse *= 0.95 + 0.05 * decay
    pulse *= 0.9 + 0.1 * throttle_curve

    return pulse

  def gen_exhaust_rasp(
    self,
    combustion_pulses: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    noise = self.rng.normal(
      0.0,
      1.0,
      len(combustion_pulses),
    )

    noise, self.rasp_zi = sosfilt(self.rasp_filter, noise, zi=self.rasp_zi)

    envelope = np.maximum(
      combustion_pulses,
      0.0,
    )

    rasp = noise * envelope * envelope

    return rasp * (0.25 + 0.75 * throttle_curve)

  def gen_engine_orders(
    self,
    base_phase: np.ndarray,
    rpm_curve: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    firing_phase = base_phase * (self.cylinders / 2.0)
    phases = 2.0 * np.pi * firing_phase[:, np.newaxis] * self.engine_orders

    wave_b = np.sin(2.0 * np.pi * phases * 1.105)
    wave_c = np.sin(2.0 * np.pi * phases * 0.895)
    wave_d = np.sin(2.0 * np.pi * phases * 2.0) * 0.25
    wave = (wave_b + wave_c + wave_d) * 1.5

    rpm_norm = np.clip(
      rpm_curve / self.redline,
      0.0,
      1.0,
    )

    high_gain = 0.1 + 0.08 * rpm_norm[:, np.newaxis]
    low_gain = 1.0 + 1.2 * rpm_norm[:, np.newaxis]
    rpm_gain = np.where(self.engine_high_mask, high_gain, low_gain)

    weighted_waves = wave * self.engine_weights * rpm_gain
    sound = np.sum(weighted_waves, axis=1) * (0.55 + 0.45 * throttle_curve)

    return sound

  def gen_mechanical_orders(
    self,
    base_phase: np.ndarray,
    rpm_curve: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    phases = 2.0 * np.pi * base_phase[:, np.newaxis] * self.mechanical_orders
    weighted_waves = np.sin(phases) * self.mechanical_weights
    rpm_norm = np.clip(
      rpm_curve / self.redline,
      0.0,
      1.0,
    )
    sound = (
      np.sum(weighted_waves, axis=1)
      * (0.85 + 0.15 * rpm_norm)
      * (0.8 + 0.2 * throttle_curve)
    )

    return sound

  def process_exhaust(
    self,
    sound: np.ndarray,
    rpm_curve: np.ndarray,
  ):
    body, self.body_zi = sosfilt(self.exhaust_body, sound, zi=self.body_zi)
    low, self.low_zi = sosfilt(self.exhaust_low, sound, zi=self.low_zi)
    high, self.high_zi = sosfilt(self.exhaust_high, sound, zi=self.high_zi)
    air, self.air_zi = sosfilt(self.exhaust_air, sound, zi=self.air_zi)
    rpm_norm = np.clip(
      rpm_curve / self.redline,
      0.0,
      1.0,
    )
    output = (
      body * 1.20
      + low * 0.65
      + high * (0.1 + 0.20 * rpm_norm)
      + air * (0.01 + 0.05 * rpm_norm)
    )

    return output

  def generate_instance(
    self,
    rpm: float,
    throttle: float,
    n_samples: int,
  ):
    if self.shifting_gear:
      rpm_curve = np.full(n_samples, rpm)
      self.last_rpm = rpm
      self.shifting_gear = False
    else:
      rpm_curve = np.linspace(
        self.last_rpm,
        rpm,
        n_samples,
      )
      self.last_rpm = rpm

    throttle_curve = np.linspace(
      self.last_throttle,
      throttle,
      n_samples,
    )
    self.last_throttle = throttle

    f_rot = rpm_curve / 60.0

    base_phase = self.phase + np.cumsum(f_rot) / self.sample_rate
    self.phase = base_phase[-1] % 1.0
    combustion = self.gen_combustion_pulses(
      base_phase,
      throttle_curve,
    )
    engine_orders = self.gen_engine_orders(
      base_phase,
      rpm_curve,
      throttle_curve,
    )
    mechanical = self.gen_mechanical_orders(
      base_phase,
      rpm_curve,
      throttle_curve,
    )
    rasp = self.gen_exhaust_rasp(
      combustion,
      throttle_curve,
    )
    mixed_sound = (
      combustion * 1.5 + engine_orders * 0.45 + mechanical * 0.6 + rasp * 0.3
    )
    mixed_sound = self.process_exhaust(
      mixed_sound,
      rpm_curve,
    )
    mixed_sound = np.tanh(mixed_sound * 3.5)

    return mixed_sound * self.amp

  def _gen_rev_sweep(
    self, dur: float, start_rpm: float, end_rpm: float, throttle: float = 1.0
  ):
    n_samples = int(dur * self.sample_rate)

    rpm_curve = np.linspace(start_rpm, end_rpm, n_samples)
    throttle_curve = np.full(n_samples, throttle)

    f_rot = rpm_curve / 60.0
    base_phase = np.cumsum(f_rot) / self.sample_rate

    combustion = self.gen_combustion_pulses(
      base_phase,
      throttle_curve,
    )
    engine_orders = self.gen_engine_orders(
      base_phase,
      rpm_curve,
      throttle_curve,
    )
    mechanical = self.gen_mechanical_orders(
      base_phase,
      rpm_curve,
      throttle_curve,
    )
    rasp = self.gen_exhaust_rasp(
      combustion,
      throttle_curve,
    )

    mixed_sound = (
      combustion * 1.5 + engine_orders * 0.45 + mechanical * 0.6 + rasp * 0.3
    )
    mixed_sound = self.process_exhaust(mixed_sound, rpm_curve)
    mixed_sound = np.tanh(mixed_sound * 3.5)

    max_val = np.max(np.abs(mixed_sound))
    if max_val > 0:
      mixed_sound /= max_val

    return mixed_sound * self.amp


def main():
  aud = EngineAudSynthesizer(
    cylinders=6,
    redline=15000,
    amp=0.1,
    sample_rate=44100,
  )

  print(f"Playing V{aud.cylinders}: 4000 -> 15,000 RPM...")

  sound = aud._gen_rev_sweep(
    dur=1.3,
    start_rpm=4000,
    end_rpm=15000,
    throttle=1.0,
  )

  sd.play(sound, samplerate=aud.sample_rate)
  sd.wait()


if __name__ == "__main__":
  main()
