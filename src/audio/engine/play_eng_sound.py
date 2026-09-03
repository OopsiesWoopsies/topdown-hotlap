import numpy as np
import sounddevice as sd

from audio.engine.sound import EngineAudSynthesizer

print("[SYSTEM] Audio modules loaded")
from game.car.engine.engine import Engine


class PlaySound:
  def __init__(self, engine: Engine):
    self.engine = engine
    self.engine_sound = EngineAudSynthesizer(6, self.engine.redline, 0.1)
    self.eng_aud_stream = sd.OutputStream(
      samplerate=self.engine_sound.sample_rate,
      channels=1,
      dtype="float32",
      callback=self.aud_callback,
      blocksize=128,
    )

    self.throttle = 0.0
    self.old_gear = 0

  def aud_callback(self, outdata, frames, time, status):
    if status:
      print(status)
    sound = self.engine_sound.generate_instance(self.engine.rpm, self.throttle, frames)

    outdata[:, 0] = sound.astype(np.float32)

  def pre_physics_update(self, old_gear: int):
    self.old_gear = old_gear

  def post_physics_update(self, new_gear: int, throttle: float):
    self.throttle = throttle
    if self.old_gear != new_gear:
      self.engine_sound.shifting_gear = True

  def start_eng(self):
    self.eng_aud_stream.start()

  def close(self):
    self.eng_aud_stream.stop()
    self.eng_aud_stream.close()
