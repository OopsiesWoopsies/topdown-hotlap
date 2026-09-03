import math

from game.car.tire import Tire
from game.constants import Constants


class Axle:
  def __init__(
    self,
    cons: Constants,
    local_pos: tuple[float, float],
    distance_to_cg: float,
    track_width: float,
    angle_rad: float,
    tire_width: float,
    tire_mass: float,
    tire_load: float,
    powered: bool,
    config: dict[str, any],
  ):
    self.cons = cons

    self.local_pos = local_pos
    self.prev_local_pos = local_pos
    self.distance_to_cg = distance_to_cg
    self.track_width = track_width
    self.half_track_width = track_width / 2
    self.axle_width = 0.05
    tire_radius = 0.35

    forward = (math.cos(angle_rad), math.sin(angle_rad))
    right = (-math.sin(angle_rad), math.cos(angle_rad))

    left_tire_pos = (
      self.local_pos[0] - right[0] * self.half_track_width,
      self.local_pos[1] - right[1] * self.half_track_width,
    )
    right_tire_pos = (
      self.local_pos[0] + right[0] * self.half_track_width,
      self.local_pos[1] + right[1] * self.half_track_width,
    )

    forward_offset = (forward[0] * tire_radius, forward[1] * tire_radius)
    right_offset = (right[0] * tire_width, right[1] * tire_width)
    l_outer_corners = [
      (
        left_tire_pos[0] + forward_offset[0] - right_offset[0],
        left_tire_pos[1] + forward_offset[1] - right_offset[1],
      ),
      (
        left_tire_pos[0] - forward_offset[0] - right_offset[0],
        left_tire_pos[1] - forward_offset[1] - right_offset[1],
      ),
    ]
    r_outer_corners = [
      (
        right_tire_pos[0] + forward_offset[0] + right_offset[0],
        right_tire_pos[1] + forward_offset[1] + right_offset[1],
      ),
      (
        right_tire_pos[0] - forward_offset[0] + right_offset[0],
        right_tire_pos[1] - forward_offset[1] + right_offset[1],
      ),
    ]

    self.left_tire = Tire(
      cons,
      left_tire_pos,
      tire_width,
      tire_radius,
      tire_mass,
      tire_load,
      (distance_to_cg, track_width / 2),
      l_outer_corners,
      powered,
      config,
    )
    self.right_tire = Tire(
      cons,
      right_tire_pos,
      tire_width,
      tire_radius,
      tire_mass,
      tire_load,
      (distance_to_cg, -track_width / 2),
      r_outer_corners,
      powered,
      config,
    )

  def get_load(self) -> float:
    return self.left_tire.load + self.right_tire.load

  def update_position(
    self,
    car_pos: tuple[float, float],
    forward: tuple[float, float],
    right: tuple[float, float],
    angle_rad: float,
    steer_rad: float,
  ):
    self.prev_local_pos = self.local_pos
    self.local_pos = (
      car_pos[0] + forward[0] * self.distance_to_cg,
      car_pos[1] + forward[1] * self.distance_to_cg,
    )

    self.left_tire.update_position(-1, self.local_pos, right, self.half_track_width)
    self.left_tire.update_outer_corners(-1, angle_rad, steer_rad)
    self.right_tire.update_position(1, self.local_pos, right, self.half_track_width)
    self.right_tire.update_outer_corners(1, angle_rad, steer_rad)
