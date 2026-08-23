import math

import pyray as pr

from game.car.tire import Tire
from game.constants import PIXELS_PER_METER


def catmull_rom(
  p0: pr.Vector2, p1: pr.Vector2, p2: pr.Vector2, p3: pr.Vector2, t: float
) -> pr.Vector2:
  t2 = t**2
  t3 = t2 * t

  x = 0.5 * (
    2 * p1.x
    + (-p0.x + p2.x) * t
    + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2
    + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3
  )

  y = 0.5 * (
    2 * p1.y
    + (-p0.y + p2.y) * t
    + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2
    + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3
  )

  return pr.Vector2(x, y)


def closest_point_on_segment(p, a, b):
  ab = pr.vector2_subtract(b, a)
  ab_len_sq = pr.vector2_length_sqr(ab)

  if ab_len_sq == 0:
    return a

  ap = pr.vector2_subtract(p, a)

  t = pr.vector2_dot_product(ab, ap) / ab_len_sq
  t = max(0.0, min(1.0, t))

  return pr.vector2_add(a, pr.vector2_scale(ab, t))


def segments_intersect(
  p1: pr.Vector2, p2: pr.Vector2, p3: pr.Vector2, p4: pr.Vector2
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

  def ccw(A: pr.Vector2, B: pr.Vector2, C: pr.Vector2) -> bool:
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

  return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


class Track:
  def __init__(self):
    # Track size
    self.width = 17  # m
    self.half_width = self.width / 2.0  # m
    line_thickness = 0.1 * PIXELS_PER_METER  # pixels

    # Track vars
    self.curr_sector = 1
    self.start_lap = False

    # Track points
    self.center_line_pts = [
      pr.Vector2(0, 0),
      pr.Vector2(-50, 0),
      pr.Vector2(-100, 0),
      pr.Vector2(-100, 50),
      pr.Vector2(-100, 100),
      pr.Vector2(-50, 100),
      pr.Vector2(0, 100),
      pr.Vector2(0, 50),
    ]  # Dictates the main path of the track
    num_pts = len(self.center_line_pts)
    sector_index = num_pts / 3
    self.finish_index = 1
    self.sector_indexes = []
    self.sector_lines = []

    for i in range(1, 3):
      self.sector_indexes.append(int((sector_index * i + self.finish_index) % num_pts))

    # Track precision points that help smoothen the track out (the following arrays includes precision points)
    self.mpp = 1  # meters per point (approx)
    self.center_pts = []
    self.left_bound_pts = []
    self.right_bound_pts = []
    self.render_left_bound_pts = []
    self.render_right_bound_pts = []

    for i in range(num_pts):  # Adds precision to center line
      cen_p0 = self.center_line_pts[i - 1]
      cen_p1 = self.center_line_pts[i]
      cen_p2 = self.center_line_pts[(i + 1) % num_pts]
      cen_p3 = self.center_line_pts[(i + 2) % num_pts]

      precision = round(
        pr.vector2_length(pr.vector2_subtract(cen_p2, cen_p1)) / self.mpp
      )

      for n in range(precision):
        self.center_pts.append(
          catmull_rom(cen_p0, cen_p1, cen_p2, cen_p3, n / precision)
        )

    num_pts = len(self.center_pts)
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for i in range(num_pts):  # Adds left and right boundary points
      prev_cen_pt = self.center_pts[i - 1]
      next_cen_pt = self.center_pts[(i + 1) % num_pts]
      direction = pr.vector2_normalize(pr.vector2_subtract(next_cen_pt, prev_cen_pt))
      normal = pr.Vector2(-direction.y, direction.x)

      cen_pt = self.center_pts[i]
      self.left_bound_pts.append(
        pr.vector2_add(cen_pt, pr.vector2_scale(normal, self.half_width))
      )
      self.right_bound_pts.append(
        pr.vector2_subtract(cen_pt, pr.vector2_scale(normal, self.half_width))
      )
      # Calculate points for texture coordinates
      min_x = min(min_x, self.left_bound_pts[i].x, self.right_bound_pts[i].x)
      max_x = max(max_x, self.left_bound_pts[i].x, self.right_bound_pts[i].x)
      min_y = min(min_y, self.left_bound_pts[i].y, self.right_bound_pts[i].y)
      max_y = max(max_y, self.left_bound_pts[i].y, self.right_bound_pts[i].y)

    min_x *= PIXELS_PER_METER
    max_x *= PIXELS_PER_METER
    min_y *= PIXELS_PER_METER
    max_y *= PIXELS_PER_METER

    padding = 10  # pixels
    self.render_offset = pr.Vector2(
      -min_x + padding,
      -min_y + padding,
    )
    self.render_position = pr.Vector2(
      min_x - padding,
      min_y - padding,
    )
    texture_width = int(max_x - min_x + padding * 2)
    texture_height = int(max_y - min_y + padding * 2)

    self.render_texture = pr.load_render_texture(texture_width, texture_height)

    pr.begin_texture_mode(self.render_texture)
    num_pts = len(self.center_pts)
    for i in range(num_pts):
      left_pt_1 = self.add_v2_render_offset(
        pr.vector2_scale(self.left_bound_pts[i], PIXELS_PER_METER)
      )
      left_pt_2 = self.add_v2_render_offset(
        pr.vector2_scale(self.left_bound_pts[(i + 1) % num_pts], PIXELS_PER_METER)
      )
      right_pt_1 = self.add_v2_render_offset(
        pr.vector2_scale(self.right_bound_pts[i], PIXELS_PER_METER)
      )
      right_pt_2 = self.add_v2_render_offset(
        pr.vector2_scale(self.right_bound_pts[(i + 1) % num_pts], PIXELS_PER_METER)
      )

      pr.draw_line_ex(left_pt_1, left_pt_2, line_thickness, pr.WHITE)
      pr.draw_line_ex(right_pt_1, right_pt_2, line_thickness, pr.WHITE)

    for i in range(len(self.left_bound_pts)):
      j = (i + 1) % len(self.left_bound_pts)

      a = self.add_v2_render_offset(
        pr.vector2_scale(self.left_bound_pts[i], PIXELS_PER_METER)
      )
      b = self.add_v2_render_offset(
        pr.vector2_scale(self.left_bound_pts[j], PIXELS_PER_METER)
      )
      c = self.add_v2_render_offset(
        pr.vector2_scale(self.right_bound_pts[j], PIXELS_PER_METER)
      )
      d = self.add_v2_render_offset(
        pr.vector2_scale(self.right_bound_pts[i], PIXELS_PER_METER)
      )

      pr.draw_triangle(a, b, c, pr.DARKGRAY)
      pr.draw_triangle(a, c, d, pr.DARKGRAY)

    # Sectors
    for i in self.sector_indexes:
      self.sector_lines.append(self.get_timing_line(i))
      pr.draw_line_ex(
        self.add_v2_render_offset(
          pr.vector2_scale(self.sector_lines[-1][0], PIXELS_PER_METER)
        ),
        self.add_v2_render_offset(
          pr.vector2_scale(self.sector_lines[-1][1], PIXELS_PER_METER)
        ),
        line_thickness,
        pr.WHITE,
      )

    # Finish line
    self.finish_line = self.get_timing_line(self.finish_index)
    pr.draw_line_ex(
      self.add_v2_render_offset(
        pr.vector2_scale(self.finish_line[0], PIXELS_PER_METER)
      ),
      self.add_v2_render_offset(
        pr.vector2_scale(self.finish_line[1], PIXELS_PER_METER)
      ),
      line_thickness,
      pr.RED,
    )

    pr.end_texture_mode()

  def add_v2_render_offset(self, position: pr.Vector2) -> pr.Vector2:
    return pr.vector2_add(position, self.render_offset)

  def get_timing_line(self, index: int):
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
    self, last_index: int, position: pr.Vector2, index_offset: int
  ):
    closest = None
    closest_dist_sq = float("inf")

    num_pts = len(self.center_pts)
    start = last_index - index_offset
    end = last_index + index_offset + 1

    for i in range(start, end):
      i %= num_pts
      j = (i + 1) % num_pts

      point = closest_point_on_segment(position, self.center_pts[i], self.center_pts[j])

      dx = position.x - point.x
      dy = position.y - point.y

      dist_sq = dx * dx + dy * dy

      if dist_sq < closest_dist_sq:
        closest_dist_sq = dist_sq
        closest = point
        last_index = i

    return closest, last_index

  def is_point_on_track(self, last_index: int, position: pr.Vector2, index_offset: int):
    point, index = self.closest_track_point(last_index, position, index_offset)

    num_pts = len(self.center_pts)
    j = (index + 1) % num_pts

    a = self.center_pts[index]
    b = self.center_pts[j]

    direction = pr.vector2_normalize(pr.vector2_subtract(b, a))
    normal = pr.Vector2(-direction.y, direction.x)
    offset = pr.vector2_subtract(position, point)
    lateral_distance = pr.vector2_dot_product(offset, normal)

    return abs(lateral_distance) <= self.half_width, index

  def check_sectors(self, prev_pos: pr.Vector2, curr_pos: pr.Vector2) -> int:
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
      tuple: True if tire is on track and the track index respectively
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

  def draw(self):
    src_rec = pr.Rectangle(
      0,
      0,
      float(self.render_texture.texture.width),
      -float(self.render_texture.texture.height),
    )
    pr.draw_texture_rec(
      self.render_texture.texture,
      src_rec,
      self.render_position,
      pr.WHITE,
    )
