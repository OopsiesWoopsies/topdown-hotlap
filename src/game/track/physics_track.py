import math

import pyray as pr

from game.car.tire import Tire

# Comments are based off of starting position (0, 0) and a starting rotation of 180 deg
# Make sure points are >= 10m apart to avoid boundary loops if turning and points don't create a jagged inner corner
# Add more points in between if jagged to smoothen it out
tracks = [
  {
    "finish": 8,
    "track": (
      # Bottom straight (going right)
      (0, 90),
      (0, 70),
      (0, 55),
      (0, 45),
      (0, 30),
      (0, 10),
      # Main straight (going up)
      (-10, 0),
      (-30, 0),
      (-45, 0),  # finish line
      (-55, 0),
      (-70, 0),
      (-90, 0),
      # Top straight (going Left)
      (-100, 10),
      (-100, 30),
      (-100, 45),
      (-100, 55),
      (-100, 70),
      (-100, 90),
      # Left straight (going down)
      (-90, 100),
      (-70, 100),
      (-55, 100),
      (-45, 100),
      (-30, 100),
      (-10, 100),
    ),
  },
  {
    "finish": 3,
    "track": (
      # Main straight (up)
      (750, 0),
      (720, 0),
      (680, 0),
      (0, 0),  # Finish line
      (-680, 0),
      (-720, 0),
      (-750, 0),
      # Top hairpin (up -> left -> down)
      (-775, 5),
      (-790, 15),
      (-790, 30),
      (-775, 40),
      # Straight 2 (down)
      (-750, 30),
      (-720, 30),
      (-680, 30),
      (0, 30),
      (680, 30),
      (720, 30),
      (750, 30),
      # Bottom hairpin (down -> right -> up)
      (775, 25),
      (790, 15),
      (790, 0),
      (775, -10),
    ),
  },
]


def catmull_rom(
  p0: tuple[float, float],
  p1: tuple[float, float],
  p2: tuple[float, float],
  p3: tuple[float, float],
  t: float,
) -> tuple[float, float]:

  alpha = 0.5

  def tj(
    ti: float,
    pa: tuple[float, float],
    pb: tuple[float, float],
  ) -> float:
    dx = pb[0] - pa[0]
    dy = pb[1] - pa[1]
    return ti + (dx * dx + dy * dy) ** (alpha * 0.5)

  t0 = 0.0
  t1 = tj(t0, p0, p1)
  t2 = tj(t1, p1, p2)
  t3 = tj(t2, p2, p3)

  tt = t1 + t * (t2 - t1)

  A1_x = (t1 - tt) / (t1 - t0) * p0[0] + (tt - t0) / (t1 - t0) * p1[0]
  A1_y = (t1 - tt) / (t1 - t0) * p0[1] + (tt - t0) / (t1 - t0) * p1[1]

  A2_x = (t2 - tt) / (t2 - t1) * p1[0] + (tt - t1) / (t2 - t1) * p2[0]
  A2_y = (t2 - tt) / (t2 - t1) * p1[1] + (tt - t1) / (t2 - t1) * p2[1]

  A3_x = (t3 - tt) / (t3 - t2) * p2[0] + (tt - t2) / (t3 - t2) * p3[0]
  A3_y = (t3 - tt) / (t3 - t2) * p2[1] + (tt - t2) / (t3 - t2) * p3[1]

  B1_x = (t2 - tt) / (t2 - t0) * A1_x + (tt - t0) / (t2 - t0) * A2_x
  B1_y = (t2 - tt) / (t2 - t0) * A1_y + (tt - t0) / (t2 - t0) * A2_y

  B2_x = (t3 - tt) / (t3 - t1) * A2_x + (tt - t1) / (t3 - t1) * A3_x
  B2_y = (t3 - tt) / (t3 - t1) * A2_y + (tt - t1) / (t3 - t1) * A3_y

  C_x = (t2 - tt) / (t2 - t1) * B1_x + (tt - t1) / (t2 - t1) * B2_x
  C_y = (t2 - tt) / (t2 - t1) * B1_y + (tt - t1) / (t2 - t1) * B2_y

  return C_x, C_y


def closest_point_on_segment(
  p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> tuple[float, float]:
  a_x, a_y = a
  b_x, b_y = b
  p_x, p_y = p

  ab_x = b_x - a_x
  ab_y = b_y - a_y

  if ab_x == 0 and ab_y == 0:
    return a

  ap_x = p_x - a_x
  ap_y = p_y - a_y

  dot_ap_ab = ap_x * ab_x + ap_y * ab_y
  dot_ab_ab = ab_x * ab_x + ab_y * ab_y
  t = dot_ap_ab / dot_ab_ab
  if t < 0.0:
    t = 0.0
  elif t > 1.0:
    t = 1.0

  return (a_x + t * ab_x, a_y + t * ab_y)


def segments_intersect(
  p1: tuple[float, float],
  p2: tuple[float, float],
  p3: tuple[float, float],
  p4: tuple[float, float],
) -> bool:
  """Checks if line segment p1-p2 intersects with line segment p3-p4.

  Args:
    p1: point 1 of the first segment.
    p2: point 2 of the first segment.
    p3: point 1 of the second segment.
    p4: point 2 of the second segment.

  Returns:
    True if any part of either segment intersects the other.
  """

  def ccw(
    A: tuple[float, float], B: tuple[float, float], C: tuple[float, float]
  ) -> bool:
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

  return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


class PhysicsTrack:
  def __init__(self):
    # Track size
    self.width = 17  # m
    self.half_width = self.width / 2.0  # m

    # In-game Track vars
    self.curr_sector = 1
    self.start_lap = False

    # Render Track Vars
    self.render_position = (0, 0)

    # Track points
    self.track_selection = 1
    self.center_line_pts = tracks[self.track_selection][
      "track"
    ]  # Dictates the main path of the track

    self.finish_index = tracks[self.track_selection]["finish"]
    self.finish_line = self.get_timing_line(self.finish_index)
    self.sector_indexes = []
    self.sector_lines = []

    self.mpp = 0.25  # meters per point (approx)
    self.center_pts: list[tuple[float, float]] = []
    self.left_bound_pts: list[pr.Vector2] = []
    self.right_bound_pts: list[pr.Vector2] = []
    self.normal_segments = []

    self.render_texture = None
    self.create_track()

  def create_track(self):
    self.center_line_pts = tracks[self.track_selection]["track"]
    num_pts = len(self.center_line_pts)
    sector_index = num_pts // 3

    self.finish_index = tracks[self.track_selection]["finish"]
    self.sector_indexes = [
      int((sector_index * i + self.finish_index) % num_pts) for i in range(1, 3)
    ]
    self.sector_lines = []

    # Track precision points that help smoothen the track out (the following arrays includes precision points)
    self.center_pts = []
    self.left_bound_pts: list[pr.Vector2] = []
    self.right_bound_pts: list[pr.Vector2] = []
    self.normal_segments = []

    for i in range(num_pts):  # Adds precision to center line
      cen_p0 = self.center_line_pts[i - 1]
      cen_p1 = self.center_line_pts[i]
      cen_p2 = self.center_line_pts[(i + 1) % num_pts]
      cen_p3 = self.center_line_pts[(i + 2) % num_pts]

      cen_p1_x, cen_p1_y = cen_p1
      cen_p2_x, cen_p2_y = cen_p2

      precision = max(
        1,
        round(
          ((cen_p2_x - cen_p1_x) ** 2 + (cen_p2_y - cen_p1_y) ** 2) ** 0.5 / self.mpp
        ),
      )

      for n in range(precision):
        self.center_pts.append(
          catmull_rom(cen_p0, cen_p1, cen_p2, cen_p3, n / precision)
        )

    num_pts = len(self.center_pts)
    for i in range(num_pts):  # Adds left and right boundary points
      j = (i + 1) % num_pts
      a = self.center_pts[i]
      b = self.center_pts[j]

      direction = pr.vector2_normalize(pr.vector2_subtract(b, a))
      self.normal_segments.append((-direction.y, direction.x))
      prev_cen_pt = self.center_pts[i - 1]
      next_cen_pt = self.center_pts[j]
      direction = pr.vector2_normalize(pr.vector2_subtract(next_cen_pt, prev_cen_pt))
      normal = pr.Vector2(-direction.y, direction.x)

      cen_pt = self.center_pts[i]
      self.left_bound_pts.append(
        pr.vector2_add(cen_pt, pr.vector2_scale(normal, self.half_width))
      )
      self.right_bound_pts.append(
        pr.vector2_subtract(cen_pt, pr.vector2_scale(normal, self.half_width))
      )

    # Sector lines and Finish line
    self.sector_lines = [self.get_timing_line(i) for i in self.sector_indexes]
    self.finish_line = self.get_timing_line(self.finish_index)

    # Convert Vector2s to tuples
    self.sector_lines = [
      ((pt1.x, pt1.y), (pt2.x, pt2.y)) for pt1, pt2 in self.sector_lines
    ]
    self.finish_line = (
      (self.finish_line[0].x, self.finish_line[0].y),
      (self.finish_line[1].x, self.finish_line[1].y),
    )

  def get_timing_line(self, index: int) -> tuple[pr.Vector2, pr.Vector2]:
    num_pts = len(self.center_line_pts)
    prev_pt = self.center_line_pts[index - 1]
    next_pt = self.center_line_pts[(index + 1) % num_pts]

    direction = pr.vector2_normalize(pr.vector2_subtract(next_pt, prev_pt))
    normal = pr.Vector2(-direction.y, direction.x)
    center = self.center_line_pts[index]

    right = pr.vector2_add(center, pr.vector2_scale(normal, self.half_width))
    left = pr.vector2_subtract(center, pr.vector2_scale(normal, self.half_width))

    return left, right

  def closest_track_point(
    self, last_index: int, position: tuple[float, float], index_offset: int
  ) -> tuple[tuple[float, float], int]:
    closest = None
    closest_dist_sq = float("inf")

    num_pts = len(self.center_pts)
    start = last_index - index_offset
    end = last_index + index_offset + 1

    for i in range(start, end):
      i %= num_pts
      j = (i + 1) % num_pts

      pt_x, pt_y = closest_point_on_segment(
        position, self.center_pts[i], self.center_pts[j]
      )

      dx = position[0] - pt_x
      dy = position[1] - pt_y

      dist_sq = dx * dx + dy * dy

      if dist_sq < closest_dist_sq:
        closest_dist_sq = dist_sq
        closest = (pt_x, pt_y)
        last_index = i

    return closest, last_index

  def is_point_on_track(
    self, last_index: int, position: tuple[float, float], index_offset: int
  ) -> tuple[bool, int]:
    (pt_x, pt_y), index = self.closest_track_point(last_index, position, index_offset)
    pos_x, pos_y = position
    dist = math.hypot(pos_x - pt_x, pos_y - pt_y)

    return dist <= self.half_width, index

  def check_sectors(
    self, prev_pos: tuple[float, float], curr_pos: tuple[float, float]
  ) -> int:
    left_pt, right_pt = self.finish_line
    if not self.start_lap:
      if segments_intersect(prev_pos, curr_pos, left_pt, right_pt):
        self.start_lap = True
        return 0
      return -1
    if self.curr_sector < 3:
      left_pt, right_pt = self.sector_lines[self.curr_sector - 1]
      is_finish_line = False
    else:
      is_finish_line = True

    if segments_intersect(prev_pos, curr_pos, left_pt, right_pt):
      if not is_finish_line:
        self.curr_sector += 1
        return self.curr_sector

      else:
        self.curr_sector = 1
        return self.curr_sector
    return -1

  def check_bounds(self, dt: float, car_speed: float, tire: Tire) -> bool:
    """Checks if the tire are within track boundaries (white lines).

    Args:
      dt: Delta time. Used to calculate the index offset.
      car_speed: Speed of car.
      tire: A tire.

    Returns:
      bool: True if tire is on track and the track index respectively
    """
    margin = 2
    index_offset = math.ceil(car_speed / self.mpp * dt) + margin
    tire_on_track = False
    new_track_indices = []

    for i in range(2):
      point_on_track, track_index = self.is_point_on_track(
        tire.track_indices[i], tire.outer_corners[i], index_offset
      )
      new_track_indices.append(track_index)
      if point_on_track:
        tire_on_track = True

    return tire_on_track, new_track_indices

  def stop_lap(self):
    self.start_lap = False
    self.curr_sector = 1
