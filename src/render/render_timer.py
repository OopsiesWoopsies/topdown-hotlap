import pyray as pr

from game.track.timer import Timer


class RenderTimer:
  def __init__(self, timer: Timer):
    self.timer = timer

    self.background = pr.Rectangle(-10, -10, 300, 240)

  def draw(self, x: int, y: int):
    pr.draw_rectangle_rounded(self.background, 0.3, 10, (0, 0, 0, 120))
    pr.draw_text(
      self.timer.curr_lap_time.str_format,
      x,
      y,
      30,
      pr.RED if self.timer.lap_timer_stopped else pr.WHITE,
    )
    pr.draw_text(self.timer.prev_lap_time.str_format, x, y + 70, 20, pr.WHITE)
    pr.draw_text("Best Lap & Sectors", x, y + 135, 20, pr.RED)
    pr.draw_text(self.timer.best_lap_time.str_format, x, y + 160, 20, pr.WHITE)

    for i in range(3):
      pr.draw_text(
        self.timer.sector_times[i].str_format, x + 100 * i, y + 30, 20, pr.WHITE
      )
      pr.draw_text(
        self.timer.prev_sector_times[i].str_format, x + 100 * i, y + 90, 20, pr.WHITE
      )
      pr.draw_text(
        self.timer.best_sector_times[i].str_format, x + 100 * i, y + 180, 20, pr.WHITE
      )
