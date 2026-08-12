import pyray as pr

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


class Track:
  def __init__(self):
    # Track size
    self.width = 17 * PIXELS_PER_METER  # m
    self.half_width = self.width / 2.0

    # Track vars
    self.last_closest_index = 0

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

    # Track precision points that help smoothen the track out (the following arrays includes precision points)
    self.mpp = 10  # meters per point (approx)
    self.center_pts = []
    self.left_bound_pts = []
    self.right_bound_pts = []

    # Point calculations
    num_pts = len(self.center_line_pts)
    for i in range(num_pts):  # Scales points to size
      self.center_line_pts[i] = pr.vector2_scale(
        self.center_line_pts[i], PIXELS_PER_METER
      )

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
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
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

    padding = 10
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
    thickness = 0.1 * PIXELS_PER_METER
    for i in range(num_pts):
      left_pt_1 = pr.vector2_add(self.left_bound_pts[i], self.render_offset)
      left_pt_2 = pr.vector2_add(
        self.left_bound_pts[(i + 1) % num_pts], self.render_offset
      )
      right_pt_1 = pr.vector2_add(self.right_bound_pts[i], self.render_offset)
      right_pt_2 = pr.vector2_add(
        self.right_bound_pts[(i + 1) % num_pts], self.render_offset
      )

      pr.draw_line_ex(left_pt_1, left_pt_2, thickness, pr.WHITE)
      pr.draw_line_ex(right_pt_1, right_pt_2, thickness, pr.WHITE)

    for i in range(len(self.left_bound_pts)):
      j = (i + 1) % len(self.left_bound_pts)

      a = pr.vector2_add(self.left_bound_pts[i], self.render_offset)
      b = pr.vector2_add(self.left_bound_pts[j], self.render_offset)
      c = pr.vector2_add(self.right_bound_pts[j], self.render_offset)
      d = pr.vector2_add(self.right_bound_pts[i], self.render_offset)

      pr.draw_triangle(a, b, c, pr.DARKGRAY)
      pr.draw_triangle(a, c, d, pr.DARKGRAY)
    pr.end_texture_mode()

  def closest_track_point(self, position: pr.Vector2, index_offset: int):
    closest = None
    closest_dist_sq = float("inf")

    num_pts = len(self.center_pts)
    start = self.last_closest_index - index_offset
    end = self.last_closest_index + index_offset + 1

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
        self.last_closest_index = i

    return closest, self.last_closest_index

  def is_point_on_track(self, position: pr.Vector2, index_offset: int):
    point, index = self.closest_track_point(position, index_offset)

    num_pts = len(self.center_pts)
    j = (index + 1) % num_pts

    a = self.center_pts[index]
    b = self.center_pts[j]

    direction = pr.vector2_normalize(pr.vector2_subtract(b, a))
    normal = pr.Vector2(-direction.y, direction.x)
    offset = pr.vector2_subtract(position, point)
    lateral_distance = pr.vector2_dot_product(offset, normal)

    return abs(lateral_distance) <= self.half_width

  def draw(self):
    pr.draw_texture(
      self.render_texture.texture,
      int(self.render_position.x),
      int(self.render_position.y),
      pr.WHITE,
    )
