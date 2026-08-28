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

    self.last_rpm = 0.0
    self.last_throttle = 0.0

    self.exhaust_body = butter(
      3,
      [200, 7000],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_low = butter(
      3,
      [350, 2000],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_high = butter(
      3,
      [300, 5500],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.exhaust_air = butter(
      2,
      [700, 7500],
      btype="bandpass",
      fs=sample_rate,
      output="sos",
    )
    self.rasp_filter = butter(
      2,
      1800,
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

  def gen_combustion_pulses(
    self,
    base_phase: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    firing_phase = base_phase * self.firing_order
    phase = firing_phase % 1.0
    pulse_width = 0.1
    distance = np.minimum(
      phase,
      1.0 - phase,
    )

    pulse = np.exp(-0.5 * (distance / pulse_width) ** 2)
    decay = np.exp(-phase * 10.0)
    pulse *= 0.15 + 0.85 * decay
    pulse *= 0.4 + 0.6 * throttle_curve

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

    rasp = noise * envelope**2.0

    return rasp * (0.25 + 0.75 * throttle_curve)

  def gen_engine_orders(
    self,
    base_phase: np.ndarray,
    rpm_curve: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    primary_order = self.cylinders / 2.0

    orders = {
      0.5: 0.06,
      1.0: 0.12,
      1.5: 0.03,
      2.0: 0.05,
      3.0: 0.15,
      4.0: 0.03,
      5.0: 0.001,
      6.0: 0.006,
      7.0: 0.0,
      8.0: 0.0,
    }

    firing_phase = base_phase * primary_order
    sound = np.zeros_like(base_phase)
    rpm_norm = np.clip(
      rpm_curve / self.redline,
      0.0,
      1.0,
    )
    for order, weight in orders.items():
      phase = firing_phase * order
      wave_b = np.sin(2.0 * np.pi * phase * 1.105)
      wave_c = np.sin(2.0 * np.pi * phase * 0.895)
      wave_d = np.sin(2.0 * np.pi * phase * 2.0) * 0.25
      wave = (wave_b + wave_c + wave_d) * 0.7

      if order >= 3.0:
        rpm_gain = 0.15 + 0.85 * rpm_norm
      else:
        rpm_gain = 1.0

      sound += wave * weight * rpm_gain * (0.55 + 0.45 * throttle_curve)

    return sound

  def gen_mechanical_orders(
    self,
    base_phase: np.ndarray,
    rpm_curve: np.ndarray,
    throttle_curve: np.ndarray,
  ):
    sound = np.zeros_like(base_phase)
    orders = {
      1.0: 0.08,
      2.0: 0.05,
      4.0: 0.035,
      6.0: 0.025,
      8.0: 0.015,
    }
    rpm_norm = np.clip(
      rpm_curve / self.redline,
      0.0,
      1.0,
    )
    for order, weight in orders.items():
      phase = base_phase * order
      sound += (
        np.sin(2.0 * np.pi * phase)
        * weight
        * (0.25 + 0.75 * rpm_norm)
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
      body * 0.90
      + low * 0.25
      + high * (0.1 + 0.40 * rpm_norm)
      + air * (0.01 + 0.05 * rpm_norm)
    )

    return output

  def generate_instance(
    self,
    rpm: float,
    throttle: float,
    n_samples: int,
  ):
    rpm_curve = np.linspace(
      self.last_rpm,
      rpm,
      n_samples,
    )

    throttle_curve = np.linspace(
      self.last_throttle,
      throttle,
      n_samples,
    )

    self.last_rpm = rpm
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
      combustion * 0.9 + engine_orders * 0.5 + mechanical * 0.65 + rasp * 0.01
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
      combustion * 0.9 + engine_orders * 0.5 + mechanical * 0.65 + rasp * 0.01
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
    dur=3.0,
    start_rpm=4000,
    end_rpm=15000,
    throttle=0.0,
  )

  sd.play(sound, samplerate=aud.sample_rate)
  sd.wait()


if __name__ == "__main__":
  main()
