import math
from collections import defaultdict

import pyray as pr

from utils.constants import Constants

CHUNK_SIZE = 1024


class RenderTrack:
  def __init__(self):
    self.chunks: dict[tuple[int, int], pr.RenderTexture] = {}

  def unload_chunks(self):
    num_chunks = len(self.chunks)
    for i, chunk_tex in enumerate(self.chunks.values()):
      pr.begin_drawing()
      pr.clear_background(pr.BLACK)
      pr.draw_text(f"Unloading chunks... {i} / {num_chunks}", 10, 10, 20, pr.RED)
      pr.end_drawing()
      pr.unload_render_texture(chunk_tex)

  def render_chunks(self, cons: Constants, track_components: dict[list | tuple]):
    center_pts = track_components["center"]
    left_bound_pts = track_components["left"]
    right_bound_pts = track_components["right"]
    sector_lines = track_components["sectors"]
    finish_line = track_components["finish"]

    self.unload_chunks()
    self.chunks = {}
    line_thickness = 0.1 * cons.PPM  # pixels
    num_pts = len(center_pts)

    chunk_segments = defaultdict(list)
    margin = line_thickness

    all_pts = left_bound_pts + right_bound_pts
    self.grid_offset_x = min(p.x for p in all_pts) * cons.PPM - margin
    self.grid_offset_y = min(p.y for p in all_pts) * cons.PPM - margin

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

      min_cx = int((min_px - self.grid_offset_x) // CHUNK_SIZE)
      max_cx = int((max_px - self.grid_offset_x) // CHUNK_SIZE)
      min_cy = int((min_py - self.grid_offset_y) // CHUNK_SIZE)
      max_cy = int((max_py - self.grid_offset_y) // CHUNK_SIZE)

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

      min_cx = int((min_px - self.grid_offset_x) // CHUNK_SIZE)
      max_cx = int((max_px - self.grid_offset_x) // CHUNK_SIZE)
      min_cy = int((min_py - self.grid_offset_y) // CHUNK_SIZE)
      max_cy = int((max_py - self.grid_offset_y) // CHUNK_SIZE)

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

    min_cx = int((min_px - self.grid_offset_x) // CHUNK_SIZE)
    max_cx = int((max_px - self.grid_offset_x) // CHUNK_SIZE)
    min_cy = int((min_py - self.grid_offset_y) // CHUNK_SIZE)
    max_cy = int((max_py - self.grid_offset_y) // CHUNK_SIZE)

    for cx in range(min_cx, max_cx + 1):
      for cy in range(min_cy, max_cy + 1):
        chunk_finish.append((cx, cy))

    # Get all unique chunks
    active_chunk_keys = (
      set(chunk_segments.keys()) | set(chunk_sectors.keys()) | set(chunk_finish)
    )
    num_chunks = len(active_chunk_keys)

    for i, (cx, cy) in enumerate(active_chunk_keys):
      pr.begin_drawing()
      pr.clear_background(pr.BLACK)
      pr.draw_text(
        f"Generating chunks... {i} / {num_chunks} chunks", 10, 10, 20, pr.WHITE
      )
      pr.end_drawing()
      chunk_tex = pr.load_render_texture(CHUNK_SIZE, CHUNK_SIZE)

      pr.begin_texture_mode(chunk_tex)
      pr.clear_background(pr.BLANK)

      chunk_world_x = cx * CHUNK_SIZE + self.grid_offset_x
      chunk_world_y = cy * CHUNK_SIZE + self.grid_offset_y
      render_offset = pr.Vector2(-chunk_world_x, -chunk_world_y)

      # Draw pavement and boundary lines for segments in this chunk
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

        # Pavement
        pr.draw_triangle(a, b, c, pr.DARKGRAY)
        pr.draw_triangle(a, c, d, pr.DARKGRAY)

        # Boundaries
        pr.draw_line_ex(a, b, line_thickness, pr.WHITE)
        pr.draw_line_ex(d, c, line_thickness, pr.WHITE)

      # Draw sectors if they fall in this chunk
      for sector_line in chunk_sectors.get((cx, cy), []):
        pr.draw_line_ex(
          pr.vector2_add(pr.vector2_scale(sector_line[0], cons.PPM), render_offset),
          pr.vector2_add(pr.vector2_scale(sector_line[1], cons.PPM), render_offset),
          line_thickness,
          pr.WHITE,
        )

      # Draw finish line if it falls in this chunk
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
    min_cx = math.floor((cam_min_x - self.grid_offset_x) / CHUNK_SIZE)
    max_cx = math.floor((cam_max_x - self.grid_offset_x) / CHUNK_SIZE)
    min_cy = math.floor((cam_min_y - self.grid_offset_y) / CHUNK_SIZE)
    max_cy = math.floor((cam_max_y - self.grid_offset_y) / CHUNK_SIZE)

    # Draw only those coords
    for cx in range(min_cx, max_cx + 1):
      for cy in range(min_cy, max_cy + 1):
        tex = self.chunks.get((cx, cy))
        if tex is None:
          continue

        world_x = cx * CHUNK_SIZE + self.grid_offset_x
        world_y = cy * CHUNK_SIZE + self.grid_offset_y
        source_rec = pr.Rectangle(0, 0, CHUNK_SIZE, -CHUNK_SIZE)

        pr.draw_texture_rec(tex.texture, source_rec, (world_x, world_y), pr.WHITE)

  def draw_borders(self, cons: Constants, camera: pr.Camera2D):
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
    min_cx = math.floor((cam_min_x - self.grid_offset_x) / CHUNK_SIZE)
    max_cx = math.floor((cam_max_x - self.grid_offset_x) / CHUNK_SIZE)
    min_cy = math.floor((cam_min_y - self.grid_offset_y) / CHUNK_SIZE)
    max_cy = math.floor((cam_max_y - self.grid_offset_y) / CHUNK_SIZE)

    # Draw only those coords
    for cx in range(min_cx, max_cx + 1):
      for cy in range(min_cy, max_cy + 1):
        tex = self.chunks.get((cx, cy))
        if tex is None:
          continue

        world_x = cx * CHUNK_SIZE + self.grid_offset_x
        world_y = cy * CHUNK_SIZE + self.grid_offset_y
        dest_rec = pr.Rectangle(world_x, world_y, CHUNK_SIZE, CHUNK_SIZE)

        pr.draw_rectangle_lines_ex(dest_rec, 0.3 * cons.PPM, pr.PINK)

  def close(self):
    self.unload_chunks()
