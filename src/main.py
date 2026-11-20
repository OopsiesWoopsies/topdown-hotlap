import argparse
import math
import time
from collections import deque
from pathlib import Path

import numpy as np
import pyray as pr
import torch

from audio.engine import play_eng_sound
from game.world import World
from input.control import Control
from ml.agent_control import AgentControl
from ml.environment.racing_env import RacingEnv
from ml.models.policy import PolicyNetwork, select_action
from render.renderer import Renderer
from utils.constants import Constants

recent_logs = deque(maxlen=20)


def evaluate(deterministic=True):
  cons = Constants()
  human_controls = Control()
  agent_controls = AgentControl(human_controls)
  world = World(agent_controls, is_human=False)

  pts = world.track.center_pts
  start = pts[0]
  next_pt = pts[1]

  angle = math.degrees(
    math.atan2(
      next_pt[1] - start[1],
      next_pt[0] - start[0],
    )
  )

  world.car.reset(pos=start, angle_deg=angle)
  world.timer.reset()

  print("Initial off-track:", world.car.off_track)
  print("Initial car position:", world.car.pos)
  print("Track start:", start)

  env = RacingEnv()
  env.car = world.car
  env.physics_track = world.track
  env.car_last_index = 0

  checkpoint_path = (
    Path(__file__).resolve().parent / "ml" / "models" / "racing_ppo_checkpoint.pt"
  )

  if not checkpoint_path.exists():
    raise FileNotFoundError(f"No trained checkpoint found at {checkpoint_path}")

  checkpoint = torch.load(
    checkpoint_path,
    map_location="cpu",
    weights_only=True,
  )

  policy = PolicyNetwork()
  policy.load_state_dict(checkpoint["policy_state_dict"])
  policy.eval()

  eng_audio = play_eng_sound.PlaySound(world.car.engine)
  renderer = Renderer(cons, agent_controls, world, eng_audio)
  eng_audio.start_eng()

  fixed_dt = 1.0 / 360.0
  action_interval = env.action_interval

  last_time = time.perf_counter()
  accumulator = 0.0
  action_elapsed = 0.0
  steps = 0
  terminated = False

  env.throttle_amt = agent_controls.throttle_amt
  env.brake_amt = agent_controls.brake_amt
  observation = env._get_observation()
  obs_tensor = torch.as_tensor(observation, dtype=torch.float32)

  with torch.no_grad():
    if deterministic:
      action = torch.tanh(policy(obs_tensor).mean).cpu().numpy().astype(np.float32)
    else:
      action, _, _ = select_action(policy, observation)

  agent_controls.set_action(action)

  try:
    while not pr.window_should_close() and not terminated:
      current_time = time.perf_counter()
      frame_time = min(current_time - last_time, 0.25)
      last_time = current_time
      accumulator += frame_time

      while accumulator >= fixed_dt and not terminated:
        eng_audio.pre_physics_update(world.car.engine.gear)
        world.update(fixed_dt)
        eng_audio.post_physics_update(
          world.car.engine.gear,
          world.inputs["throttle"],
        )

        accumulator -= fixed_dt
        action_elapsed += fixed_dt

        if world.car.off_track:
          terminated = True
          print("Off-track detected at speed:", world.car.speed)
          print("Car position:", world.car.pos)
          break

        if action_elapsed >= action_interval - 1e-9:
          if world.car.off_track:
            terminated = True
            break
          action_elapsed -= action_interval

          env.throttle_amt = agent_controls.throttle_amt
          env.brake_amt = agent_controls.brake_amt
          observation = env._get_observation()
          obs_tensor = torch.as_tensor(observation, dtype=torch.float32)

          with torch.no_grad():
            if deterministic:
              distribution = policy(obs_tensor)
              action = torch.tanh(distribution.mean).cpu().numpy().astype(np.float32)
            else:
              action, _, _ = select_action(policy, observation)

          agent_controls.set_action(action)
          steps += 1

          # log_agent_state(observation, action)
          recent_logs.append(
            {
              "step": steps,
              "speed": world.car.speed * 3.6,
              "steering": float(action[0]),
              "longitudinal": float(action[1]),
              "shift": float(action[2]),
              "gear": world.car.engine.gear - 1,
              "position": tuple(world.car.pos),
              "observation": observation.copy(),
            }
          )

      alpha = accumulator / fixed_dt
      if renderer.render_screen(alpha, frame_time):
        break

  finally:
    eng_audio.close()
    renderer.close()
    env.close()

  print(f"Evaluation decisions: {steps}")
  print(f"Off track: {world.car.off_track}")
  print(f"Final speed: {world.car.speed * 3.6:.1f} km/h")
  print(f"Final pos: {world.car.pos}")

  print(f"Debug:\n{world.car.get_debug_vals()}")
  print("\n===== LAST 20 DECISIONS BEFORE CRASH =====")

  for log in recent_logs:
    print(
      f"Step: {log['step']:4d} | "
      f"Speed: {log['speed']:6.1f} km/h | "
      f"Steer: {log['steering']:+.3f} | "
      f"Long: {log['longitudinal']:+.3f} | "
      f"Shift: {log['shift']:+.3f} | "
      f"Gear: {log['gear']} | "
      f"Pos: {log['position']} | "
      f"Obs: {np.round(log['observation'], 3)}"
    )


def main():
  parser = argparse.ArgumentParser()
  modes = parser.add_mutually_exclusive_group()
  modes.add_argument(
    "--train",
    action="store_true",
    help="Train the ML model in headless mode",
  )
  modes.add_argument(
    "--evaluate",
    action="store_true",
    help="Visually evaluate the trained ML model",
  )

  parser.add_argument("--total-timesteps", type=int, default=100_000)
  parser.add_argument("--rollout-size", type=int, default=1024)
  parser.add_argument("--update-epochs", type=int, default=4)
  parser.add_argument(
    "--new",
    action="store_true",
    help="Reset everything and start from scratch",
  )
  args = parser.parse_args()

  if args.train:
    from ml.training.train import train

    train(
      total_timesteps=args.total_timesteps,
      rollout_size=args.rollout_size,
      update_epochs=args.update_epochs,
      new=args.new,
    )
    return

  if args.evaluate:
    evaluate()
    return

  # Normal human-controlled game.
  cons = Constants()
  ctrls = Control()
  world = World(ctrls, is_human=True)

  eng_audio = play_eng_sound.PlaySound(world.car.engine)
  renderer = Renderer(cons, ctrls, world, eng_audio)
  eng_audio.start_eng()

  fixed_dt = 1.0 / 360.0
  last_time = time.perf_counter()
  accumulator = 0.0
  close_window = False

  try:
    while not close_window:
      current_time = time.perf_counter()
      frame_time = min(current_time - last_time, 0.25)
      last_time = current_time
      accumulator += frame_time

      while accumulator >= fixed_dt:
        eng_audio.pre_physics_update(world.car.engine.gear)
        world.update(fixed_dt)
        eng_audio.post_physics_update(
          world.car.engine.gear,
          world.inputs["throttle"],
        )
        accumulator -= fixed_dt

      alpha = accumulator / fixed_dt
      close_window = renderer.render_screen(alpha, frame_time)

  finally:
    eng_audio.close()
    renderer.close()


if __name__ == "__main__":
  main()
