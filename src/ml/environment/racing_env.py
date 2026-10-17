import math

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from game.car.car_body import Car
from game.track.physics_track import PhysicsTrack
from input.control import Control


def _wrap_angle(angle: float) -> float:
  return (angle + math.pi) % (2 * math.pi) - math.pi


def _get_track_offset(
  position: tuple[float, float], track_point: tuple[float, float], track_heading: float
) -> float:
  x_comp = position[0] - track_point[0]
  y_comp = position[1] - track_point[1]

  return -x_comp * math.sin(track_heading) + y_comp * math.cos(track_heading)


class RacingEnv(gym.Env):
  def __init__(self):
    super().__init__()

    self.action_space = spaces.Box(
      low=np.array([-1.0, -1.0, -1.0], dtype=np.float32),
      high=np.array([1.0, 1.0, 1.0], dtype=np.float32),
      dtype=np.float32,
    )

    self.action_interval = 0.05
    self.physics_dt = 1.0 / 360.0
    self.max_episode_steps = 5000
    self.episode_steps = 0
    self.episode_progress_points = 0

    self.observation_space = spaces.Box(
      low=-1.0, high=1.0, shape=(16,), dtype=np.float32
    )

    # Related vars
    self.ctrls = Control()
    self.car = Car((0.0, 0.0), 0.0, (5.6, 2.0))
    self.car_last_index = 0
    self.physics_track = PhysicsTrack()

    self.throttle_pressed = False
    self.brake_pressed = False

    self.steer_request = 0.0
    self.throttle_amt = 0.0
    self.brake_amt = 0.0

    self.prev_shift_req = 0

  def _get_track_point_and_heading(
    self, position: tuple[float, float], last_index: int
  ) -> tuple[tuple[float, float], int, float]:
    index_offset = (
      math.ceil(self.car.speed * self.action_interval / self.physics_track.MPP) + 2
    )

    point, index = self.physics_track.closest_track_point(
      last_index, position, index_offset
    )
    pts = self.physics_track.center_pts
    next_pt = pts[(index + 1) % len(pts)]

    dx = next_pt[0] - pts[index][0]
    dy = next_pt[1] - pts[index][1]

    heading = math.atan2(dy, dx)
    return point, index, heading

  def _process_action(
    self, action: np.ndarray
  ) -> tuple[float, dict[str, float | bool]]:
    steering = float(np.clip(action[0], -1.0, 1.0))
    longitudinal = float(np.clip(action[1], -1.0, 1.0))
    shift_value = float(np.clip(action[2], -1.0, 1.0))

    self.steer_request = steering

    self.throttle_pressed = longitudinal > 0.1
    self.brake_pressed = longitudinal < -0.1

    shift_request = 1 if shift_value > 0.5 else -1 if shift_value < -0.5 else 0

    inputs = {
      "throttle": self.throttle_amt,
      "brake": self.brake_amt,
      "shift_up": (shift_request == 1 and self.prev_shift_req != 1),
      "shift_down": (shift_request == -1 and self.prev_shift_req != -1),
    }
    self.prev_shift_req = shift_request

    return steering, inputs

  def _update_control_state(self, dt: float) -> None:
    if self.throttle_pressed:
      self.brake_amt = 0.0
      self.throttle_amt += self.ctrls.add_throttle * dt
    else:
      self.throttle_amt -= self.ctrls.sub_throttle * dt

    if self.brake_pressed:
      self.throttle_amt = 0.0
      self.brake_amt += self.ctrls.add_brake * dt
    else:
      self.brake_amt -= self.ctrls.sub_brake * dt

    self.throttle_amt = float(np.clip(self.throttle_amt, 0.0, 1.0))
    self.brake_amt = float(np.clip(self.brake_amt, 0.0, 1.0))

  def _get_observation(self):
    # Get vals for the observation
    front_sa = (
      self.car.front_tires[0].slip_angle + self.car.front_tires[1].slip_angle
    ) / 2
    rear_sa = (
      self.car.rear_tires[0].slip_angle + self.car.rear_tires[1].slip_angle
    ) / 2
    front_sr = (
      self.car.front_tires[0].slip_ratio + self.car.front_tires[1].slip_ratio
    ) / 2
    rear_sr = (
      self.car.rear_tires[0].slip_ratio + self.car.rear_tires[1].slip_ratio
    ) / 2

    track_point, track_index, track_heading = self._get_track_point_and_heading(
      self.car.pos, self.car_last_index
    )
    self.car_last_index = track_index
    offset_norm = (
      _get_track_offset(self.car.pos, track_point, track_heading)
      / self.physics_track.half_width
    )
    heading_err = _wrap_angle(self.car.angle_rad - track_heading) / math.pi

    target_lookaheads = [
      0.5 * self.car.speed,
      1.0 * self.car.speed,
      2.0 * self.car.speed,
    ]  # m
    lookaheads = []
    pts = self.physics_track.center_pts

    for lookahead in target_lookaheads:
      accum = 0.0  # m
      index = self.car_last_index

      while accum < lookahead:
        next_index = (index + 1) % len(pts)
        x_comp = pts[next_index][0] - pts[index][0]
        y_comp = pts[next_index][1] - pts[index][1]

        dist = (x_comp * x_comp + y_comp * y_comp) ** 0.5
        accum += dist

        index = next_index

      x_comp = pts[index][0] - pts[index - 1][0]
      y_comp = pts[index][1] - pts[index - 1][1]
      lookaheads.append(math.atan2(y_comp, x_comp))

    engine = self.car.engine
    rpm_norm = engine.rpm / engine.redline
    num_gears = len(engine.gear_ratios)
    gear_norm = 2.0 * engine.gear / (num_gears - 1) - 1.0

    # init observation
    observation = np.array(
      [
        self.car.speed / 100.0,
        self.car.local_velo[1] / 20.0,
        self.car.yaw_rate / 2,
        self.car.steer_angle / self.car.max_steer_angle,
        offset_norm,
        heading_err,
        _wrap_angle(lookaheads[0] - self.car.angle_rad) / math.pi,
        _wrap_angle(lookaheads[1] - self.car.angle_rad) / math.pi,
        _wrap_angle(lookaheads[2] - self.car.angle_rad) / math.pi,
        self.throttle_amt - self.brake_amt,
        front_sa / 1.5,
        rear_sa / 1.5,
        front_sr / 2.0,
        rear_sr / 2.0,
        rpm_norm,
        gear_norm,
      ],
      dtype=np.float32,
    )

    return np.clip(observation, -1.0, 1.0)

  def step(self, action):
    action = np.asarray(action, dtype=np.float32)
    old_index = self.car_last_index
    steer, inputs = self._process_action(action)

    remaining = self.action_interval
    sector = 0

    while remaining > 1e-9:
      dt = min(self.physics_dt, remaining)
      self._update_control_state(dt)

      inputs["throttle"] = self.throttle_amt
      inputs["brake"] = self.brake_amt

      sector = self.car.update(
        self.physics_track,
        dt,
        inputs,
        steer,
      )

      inputs["shift_up"] = False
      inputs["shift_down"] = False

      remaining -= dt

    self.episode_steps += 1
    observation = self._get_observation()

    # Reward
    num_pts = len(self.physics_track.center_pts)
    new_index = self.car_last_index
    index_delta = new_index - old_index

    if index_delta < -(num_pts // 2):
      index_delta += num_pts
    elif index_delta > num_pts // 2:
      index_delta -= num_pts

    self.episode_progress_points += index_delta
    progress_points = index_delta

    max_progress = (
      math.ceil(self.car.speed * self.action_interval / self.physics_track.MPP) + 2
    )
    progress_points = min(progress_points, max_progress)

    progress_m = progress_points * self.physics_track.MPP
    reward = float(progress_m)

    # Punish and terminate if off track
    terminated = bool(self.car.off_track)

    if terminated:
      reward -= 50.0

    truncated = self.episode_steps >= self.max_episode_steps
    total_points = self.episode_progress_points

    info = {
      "sector": sector,
      "progress_m": progress_m,
      "off_track": terminated,
      "completed_laps": total_points // num_pts,
      "track_progress_pct": (total_points % num_pts) / num_pts * 100,
      "net_progress_m": total_points * self.physics_track.MPP,
    }

    return observation, reward, terminated, truncated, info

  def reset(self, *, seed=None, options=None):
    super().reset(seed=seed)

    pts = self.physics_track.center_pts
    start = pts[0]
    next_pt = pts[1]

    angle = math.degrees(
      math.atan2(
        next_pt[1] - start[1],
        next_pt[0] - start[0],
      )
    )

    self.car = Car(start, angle, (5.6, 2.0))
    self.car_last_index = 0

    self.throttle_pressed = False
    self.brake_pressed = False
    self.steer_request = 0.0
    self.throttle_amt = 0.0
    self.brake_amt = 0.0
    self.prev_shift_req = 0

    self.episode_steps = 0
    self.episode_progress_points = 0

    return self._get_observation(), {}
