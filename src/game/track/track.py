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


class Track:
  def __init__(self):
    self.precision = 50
    self.width = 17 * PIXELS_PER_METER  # m
    self.center_line_pts = [
      pr.Vector2(-500, 0),
      pr.Vector2(-1000, 0),
      pr.Vector2(-1000, 500),
      pr.Vector2(-1000, 1000),
      pr.Vector2(-500, 1000),
      pr.Vector2(0, 1000),
    ]
    self.left_bound = []
    self.right_bound = []

    self.center_pts = []
    self.left_bound_pts = []
    self.right_bound_pts = []

    num_pts = len(self.center_line_pts)
    half_width = self.width / 2.0
    for i in range(num_pts):
      self.center_line_pts[i] = pr.vector2_scale(
        self.center_line_pts[i], PIXELS_PER_METER
      )

    for i in range(num_pts):
      prev_cen_pt = self.center_line_pts[i - 1]
      next_cen_pt = self.center_line_pts[(i + 1) % num_pts]
      direction = pr.vector2_subtract(next_cen_pt, prev_cen_pt)
      direction = pr.vector2_normalize(direction)
      normal = pr.vector2_scale(pr.Vector2(-direction.y, direction.x), half_width)

      cen_pt = self.center_line_pts[i]
      self.left_bound.append(pr.vector2_add(cen_pt, normal))
      self.right_bound.append(pr.vector2_subtract(cen_pt, normal))

    for i in range(num_pts):
      cen_p0 = self.center_line_pts[i - 1]
      cen_p1 = self.center_line_pts[i]
      cen_p2 = self.center_line_pts[(i + 1) % num_pts]
      cen_p3 = self.center_line_pts[(i + 2) % num_pts]

      left_p0 = self.left_bound[i - 1]
      left_p1 = self.left_bound[i]
      left_p2 = self.left_bound[(i + 1) % num_pts]
      left_p3 = self.left_bound[(i + 2) % num_pts]

      right_p0 = self.right_bound[i - 1]
      right_p1 = self.right_bound[i]
      right_p2 = self.right_bound[(i + 1) % num_pts]
      right_p3 = self.right_bound[(i + 2) % num_pts]

      for n in range(self.precision):
        self.center_pts.append(
          catmull_rom(cen_p0, cen_p1, cen_p2, cen_p3, n / self.precision)
        )
        self.left_bound_pts.append(
          catmull_rom(left_p0, left_p1, left_p2, left_p3, n / self.precision)
        )
        self.right_bound_pts.append(
          catmull_rom(right_p0, right_p1, right_p2, right_p3, n / self.precision)
        )

  def draw(self):
    num_pts = len(self.center_pts)
    thickness = 0.1 * PIXELS_PER_METER
    for i in range(num_pts):
      cen_pt_1 = self.center_pts[i]
      cen_pt_2 = self.center_pts[(i + 1) % num_pts]
      left_pt_1 = self.left_bound_pts[i]
      left_pt_2 = self.left_bound_pts[(i + 1) % num_pts]
      right_pt_1 = self.right_bound_pts[i]
      right_pt_2 = self.right_bound_pts[(i + 1) % num_pts]

      pr.draw_line_v(cen_pt_1, cen_pt_2, pr.RED)
      pr.draw_line_ex(left_pt_1, left_pt_2, thickness, pr.WHITE)
      pr.draw_line_ex(right_pt_1, right_pt_2, thickness, pr.WHITE)

    for i in range(len(self.left_bound_pts)):
      j = (i + 1) % len(self.left_bound_pts)

      a = self.left_bound_pts[i]
      b = self.left_bound_pts[j]
      c = self.right_bound_pts[j]
      d = self.right_bound_pts[i]

      pr.draw_triangle(a, b, c, pr.DARKGRAY)
      pr.draw_triangle(a, c, d, pr.DARKGRAY)
