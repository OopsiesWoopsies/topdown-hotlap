import argparse
import time

from audio.engine import play_eng_sound
from game.constants import Constants
from game.world import World
from input.control import Control
from render.renderer import Renderer


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--train", action="store_true", help="Run ML training in headless mode"
  )
  args = parser.parse_args()
  is_training = args.train

  cons = Constants()
  ctrls = Control()
  world = World(cons, ctrls)

  fixed_dt = 1.0 / 360.0

  if not is_training:
    renderer = Renderer(cons, ctrls, world)
    eng_audio = play_eng_sound.PlaySound(world.car.engine)
    eng_audio.start_eng()

    last_time = time.perf_counter()
    close_window = False
    accumulator = 0.0

    while not close_window:
      # Static delta time
      current_time = time.perf_counter()
      frame_time = min(current_time - last_time, 0.25)
      last_time = current_time
      accumulator += frame_time

      while accumulator >= fixed_dt:
        eng_audio.pre_physics_update(world.car.engine.gear)
        world.update(fixed_dt)
        eng_audio.post_physics_update(world.car.engine.gear, world.inputs["throttle"])
        accumulator -= fixed_dt

      alpha = accumulator / fixed_dt
      close_window = renderer.render_screen(alpha, frame_time)

    eng_audio.close()
    renderer.close()

  else:
    print("Training ML model (Headless)")


main()
