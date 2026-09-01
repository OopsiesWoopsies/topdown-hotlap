import numpy as np
import sounddevice as sd

from game.car.car_body import Car
from game.car.engine.sounds import EngineAudSynthesizer
from game.constants import Constants
from game.track.timer import Timer
from game.track.track import Track
from input.control import Control


class World:
  def __init__(self, cons: Constants, ctrls: Control):
    self.controls = ctrls
    self.car = Car(cons, pos=(0.0, 0.0), angle_deg=180, size=(5.6, 2.0))
    self.track = Track(cons)
    self.timer = Timer()

    self.throttle = 0.0
    self.engine_sound = EngineAudSynthesizer(6, self.car.engine.redline, 0.1)
    self.aud_stream = sd.OutputStream(
      samplerate=self.engine_sound.sample_rate,
      channels=1,
      dtype="float32",
      callback=self.aud_callback,
      blocksize=128,
    )
    self.aud_stream.start()

  def aud_callback(self, outdata, frames, time, status):
    if status:
      print(status)
    sound = self.engine_sound.generate_instance(
      self.car.engine.rpm, self.throttle, frames
    )

    outdata[:, 0] = sound.astype(np.float32)

  def update(self, dt):
    inputs = self.controls.get_inputs(dt)
    steer = self.controls.get_steering()
    old_gear = self.car.engine.gear
    sector = self.car.update(self.track, dt, inputs, steer)
    new_gear = self.car.engine.gear
    self.throttle = inputs["throttle"]
    if old_gear != new_gear:
      self.engine_sound.shifting_gear = True

    if self.car.off_track and not self.timer.lap_timer_stopped:
      self.timer.stop_lap_timer()
      self.track.stop_lap()
    if not self.track.start_lap:
      return
    if sector == 0:
      self.timer.start_lap_timer()
    elif sector == 2 or sector == 3:
      self.timer.set_sector_time(sector - 1)
    elif sector == 1:
      self.timer.set_sector_time(sector - 1)
      self.timer.set_lap_time()

  def close(self):
    self.aud_stream.stop()
    self.aud_stream.close()
