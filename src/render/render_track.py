import math
from collections import defaultdict

import pyray as pr

from game.constants import Constants

CHUNK_SIZE = 1024


class RenderTrack:
  def __init__(self):
    self.chunks: dict[tuple[int, int], pr.RenderTexture] = {}

  def render_chunks(
    self,
    cons: Constants,
    center_pts: list[tuple[float, float]],
    left_bound_pts: list[pr.Vector2],
    right_bound_pts: list[pr.Vector2],
    sector_lines: list[tuple[float, float]],
    finish_line: tuple[float, float],
  ):
    self.chunks = {}
    line_thickness = 0.1 * cons.PPM  # pixels
    num_pts = len(center_pts)

    chunk_segments = defaultdict(list)
    margin = line_thickness

    for i in range(num_pts):
      j = (i + 1) % num_pts

      # Get the 4 corners of this track segment
      p1, p2 = left_bound_pts[i], left_bound_pts[j]
      p3, p4 = right_bound_pts[j], right_bound_pts[i]

      # Find the min/max pixel bounds for this segment and add margin
      min_px = min(p1.x, p2.x, p3.x, p4.x) * cons.PPM - margin
      max_px = max(p1.x, p2.x, p3.x, p4.x) * cons.PPM + margin
      min_py = min(p1.y, p2.y, p3.y, p4.y) * cons.PPM - margin
      max_py = max(p1.y, p2.y, p3.y, p4.y) * cons.PPM + margin

      min_cx, max_cx = int(min_px // CHUNK_SIZE), int(max_px // CHUNK_SIZE)
      min_cy, max_cy = int(min_py // CHUNK_SIZE), int(max_py // CHUNK_SIZE)

      for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
          chunk_segments[(cx, cy)].append(i)

    chunk_sectors = defaultdict(list)
    for sector_line in sector_lines:
      # Find the min/max pixel bounds for the sector line and add margin
      sector_line1 = sector_line[0]
      sector_line2 = sector_line[1]
      min_px = min(sector_line1[0], sector_line2[0]) * cons.PPM - margin
      max_px = max(sector_line1[0], sector_line2[0]) * cons.PPM + margin
      min_py = min(sector_line1[1], sector_line2[1]) * cons.PPM - margin
      max_py = max(sector_line1[1], sector_line2[1]) * cons.PPM + margin

      min_cx, max_cx = int(min_px // CHUNK_SIZE), int(max_px // CHUNK_SIZE)
      min_cy, max_cy = int(min_py // CHUNK_SIZE), int(max_py // CHUNK_SIZE)

      for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
          chunk_sectors[(cx, cy)].append(sector_line)

    chunk_finish = []
    # Find the min/max pixel bounds for the finish line and add margin
    finish_line1 = finish_line[0]
    finish_line2 = finish_line[1]
    min_px = min(finish_line1[0], finish_line2[0]) * cons.PPM - margin
    max_px = max(finish_line1[0], finish_line2[0]) * cons.PPM + margin
    min_py = min(finish_line1[1], finish_line2[1]) * cons.PPM - margin
    max_py = max(finish_line1[1], finish_line2[1]) * cons.PPM + margin

    min_cx, max_cx = int(min_px // CHUNK_SIZE), int(max_px // CHUNK_SIZE)
    min_cy, max_cy = int(min_py // CHUNK_SIZE), int(max_py // CHUNK_SIZE)

    for cx in range(min_cx, max_cx + 1):
      for cy in range(min_cy, max_cy + 1):
        chunk_finish.append((cx, cy))

    # Get all unique chunks
    active_chunk_keys = (
      set(chunk_segments.keys()) | set(chunk_sectors.keys()) | set(chunk_finish)
    )
    num_chunks = len(active_chunk_keys)

    for idx, (cx, cy) in enumerate(active_chunk_keys):
      pr.begin_drawing()
      pr.clear_background(pr.BLACK)
      pr.draw_text(
        f"Generating chunks... {idx} / {num_chunks} chunks", 10, 10, 20, pr.WHITE
      )
      pr.end_drawing()
      chunk_tex = pr.load_render_texture(CHUNK_SIZE, CHUNK_SIZE)

      pr.begin_texture_mode(chunk_tex)
      pr.clear_background(pr.BLANK)

      render_offset = pr.Vector2(-cx * CHUNK_SIZE, -cy * CHUNK_SIZE)

      # Draw pavement and boundary lines ONLY for segments in this chunk
      for i in chunk_segments.get((cx, cy), []):
        j = (i + 1) % num_pts

        a = pr.vector2_add(pr.vector2_scale(left_bound_pts[i], cons.PPM), render_offset)
        b = pr.vector2_add(pr.vector2_scale(left_bound_pts[j], cons.PPM), render_offset)
        c = pr.vector2_add(
          pr.vector2_scale(right_bound_pts[j], cons.PPM), render_offset
        )
        d = pr.vector2_add(
          pr.vector2_scale(right_bound_pts[i], cons.PPM), render_offset
        )

        # Pavement (Will work perfectly if uncommented now)
        pr.draw_triangle(a, b, c, pr.DARKGRAY)
        pr.draw_triangle(a, c, d, pr.DARKGRAY)

        # Boundaries
        pr.draw_line_ex(a, b, line_thickness, pr.WHITE)
        pr.draw_line_ex(d, c, line_thickness, pr.WHITE)

      # Draw Sectors ONLY if they fall in this chunk
      for sector_line in chunk_sectors.get((cx, cy), []):
        pr.draw_line_ex(
          pr.vector2_add(pr.vector2_scale(sector_line[0], cons.PPM), render_offset),
          pr.vector2_add(pr.vector2_scale(sector_line[1], cons.PPM), render_offset),
          line_thickness,
          pr.WHITE,
        )

      # Draw Finish line ONLY if it falls in this chunk
      if (cx, cy) in chunk_finish:
        pr.draw_line_ex(
          pr.vector2_add(pr.vector2_scale(finish_line[0], cons.PPM), render_offset),
          pr.vector2_add(pr.vector2_scale(finish_line[1], cons.PPM), render_offset),
          line_thickness,
          pr.RED,
        )

      pr.end_texture_mode()
      self.chunks[(cx, cy)] = chunk_tex
    print(len(center_pts))

  def draw(self, camera: pr.Camera2D):
    screen_w = pr.get_screen_width()
    screen_h = pr.get_screen_height()

    p1 = pr.get_screen_to_world_2d(pr.Vector2(0, 0), camera)
    p2 = pr.get_screen_to_world_2d(pr.Vector2(screen_w, 0), camera)
    p3 = pr.get_screen_to_world_2d(pr.Vector2(0, screen_h), camera)
    p4 = pr.get_screen_to_world_2d(pr.Vector2(screen_w, screen_h), camera)

    cam_min_x = min(p1.x, p2.x, p3.x, p4.x)
    cam_max_x = max(p1.x, p2.x, p3.x, p4.x)
    cam_min_y = min(p1.y, p2.y, p3.y, p4.y)
    cam_max_y = max(p1.y, p2.y, p3.y, p4.y)

    # Get bounding chunk coords
    min_cx = math.floor(cam_min_x / CHUNK_SIZE)
    max_cx = math.floor(cam_max_x / CHUNK_SIZE)

    min_cy = math.floor(cam_min_y / CHUNK_SIZE)
    max_cy = math.floor(cam_max_y / CHUNK_SIZE)

    # Draw only those coords
    for cx in range(min_cx, max_cx + 1):
      for cy in range(min_cy, max_cy + 1):
        tex = self.chunks.get((cx, cy))
        if tex is None:
          continue

        world_x = cx * CHUNK_SIZE
        world_y = cy * CHUNK_SIZE
        source_rec = pr.Rectangle(0, 0, CHUNK_SIZE, -CHUNK_SIZE)
        dest_rec = pr.Rectangle(world_x, world_y, CHUNK_SIZE, CHUNK_SIZE)

        pr.draw_texture_pro(
          tex.texture, source_rec, dest_rec, pr.Vector2(0, 0), 0.0, pr.WHITE
        )

  def close(self):
    for chunk_tex in self.chunks.values():
      pr.unload_render_texture(chunk_tex)
