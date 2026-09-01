import time

import pyray as pr


def ms_to_str(ms: int, lap_time: bool = False) -> str:
  """Convert seconds to a readable time, MM:SS.MS.

  Args:
    seconds: Seconds including the decimals to calculate for milliseconds.

  Returns:
    str: A string that reads: MM:SS.MS or SS.MS (if MM is 0), where minutes does not convert to hours and milliseconds reads up to the thousandths place.
  """
  seconds = ms // 1000
  ms %= 1000
  minutes = seconds // 60
  seconds %= 60
  if minutes == 0 and not lap_time:
    return f"{seconds:02}.{ms:03}"
  return f"{minutes:02}:{seconds:02}.{ms:03}"


class RaceTime:
  def __init__(self, ms: float, str_format: str):
    self.ms = ms
    self.str_format = str_format

  def update_time(self, ms: float, lap_time: bool = False):
    self.ms = ms
    self.str_format = ms_to_str(ms, lap_time)


class Timer:
  def __init__(self):
    # All in ms unless stated otherwise
    self.start_lap_time = 0.0  # s
    self.start_sector_time = 0.0  # s

    self.sector_times = [RaceTime(0, "00.000") for _ in range(3)]
    self.prev_sector_times = [RaceTime(0, "00.000") for _ in range(3)]
    self.best_sector_times = [
      RaceTime(float("inf"), "00.000") for _ in range(3)
    ]  # Get this from storage

    self.curr_lap_time = RaceTime(0, "00:00.000")
    self.prev_lap_time = RaceTime(0, "00:00.000")
    self.best_lap_time = RaceTime(float("inf"), "00:00.000")  # Get this from storage

    self.lap_timer_stopped = True

  def start_lap_timer(self):
    self.start_lap_time = time.perf_counter()
    self.start_sector_time = time.perf_counter()
    self.sector_times = [RaceTime(0, "00.000") for _ in range(3)]
    self.lap_timer_stopped = False

  def get_elapsed_time(self, start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000)

  def stop_lap_timer(self):
    self.curr_lap_time.update_time(self.get_elapsed_time(self.start_lap_time), True)
    self.lap_timer_stopped = True

  def set_lap_time(self):
    self.prev_lap_time.update_time(self.get_elapsed_time(self.start_lap_time), True)
    self.start_lap_time = time.perf_counter()
    if self.best_lap_time.ms > self.prev_lap_time.ms:
      self.best_lap_time.update_time(self.prev_lap_time.ms, True)

    for i in range(3):
      self.prev_sector_times[i].update_time(self.sector_times[i].ms)
      self.sector_times[i] = RaceTime(0, "00.000")

  def set_sector_time(self, sector: int):
    sector_i = sector - 1
    self.sector_times[sector_i].update_time(
      self.get_elapsed_time(self.start_sector_time)
    )
    self.start_sector_time = time.perf_counter()
    if self.best_sector_times[sector_i].ms > self.sector_times[sector_i].ms:
      self.best_sector_times[sector_i].update_time(self.sector_times[sector_i].ms)

  def draw_timer(self, x: int, y: int):
    if self.lap_timer_stopped:
      total_time = self.curr_lap_time.str_format
    else:
      total_time = self.get_elapsed_time(self.start_lap_time)
      total_time = ms_to_str(round(total_time), True)

    pr.draw_rectangle_rounded(pr.Rectangle(-10, -10, 300, 240), 0.3, 10, (0, 0, 0, 120))
    pr.draw_text(total_time, x, y, 30, pr.WHITE)
    pr.draw_text(self.prev_lap_time.str_format, x, y + 70, 20, pr.WHITE)
    pr.draw_text("Best Lap & Sectors", x, y + 135, 20, pr.RED)
    pr.draw_text(self.best_lap_time.str_format, x, y + 160, 20, pr.WHITE)

    for i in range(3):
      pr.draw_text(self.sector_times[i].str_format, x + 100 * i, y + 30, 20, pr.WHITE)
      pr.draw_text(
        self.prev_sector_times[i].str_format, x + 100 * i, y + 90, 20, pr.WHITE
      )
      pr.draw_text(
        self.best_sector_times[i].str_format, x + 100 * i, y + 180, 20, pr.WHITE
      )
