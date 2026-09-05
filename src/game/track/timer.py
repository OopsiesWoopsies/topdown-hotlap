import time


def sec_to_str(sec: float, is_lap_time: bool = False) -> str:
  """Convert seconds to a readable time, MM:SS.MS.

  Args:
    seconds: Seconds including the decimals to calculate for milliseconds.

  Returns:
    str: A string that reads: MM:SS.MS or SS.MS (if MM is 0), where minutes does not convert to hours and milliseconds reads up to the thousandths place.
  """
  ms = int((sec * 1000) % 1000)
  minutes = int(sec / 60)
  sec = int(sec % 60)
  if minutes == 0 and not is_lap_time:
    return f"{sec:02}.{ms:03}"
  return f"{minutes:02}:{sec:02}.{ms:03}"


class RaceTime:
  def __init__(self, sec: float = 0.0, str_format: str = "00:00.000"):
    self.sec = sec
    self.str_format = str_format

  def update_time(self, sec: float, is_lap_time: bool = False):
    self.sec = sec
    self.str_format = sec_to_str(sec, is_lap_time)


class Timer:
  def __init__(self, is_human: bool):
    self.sector_times = [RaceTime(0.0, "00.000") for _ in range(3)]
    self.prev_sector_times = [RaceTime(0.0, "00.000") for _ in range(3)]
    self.best_sector_times = [
      RaceTime(float("inf"), "00.000") for _ in range(3)
    ]  # Get this from storage

    self.curr_lap_time = RaceTime()
    self.curr_sector_time = 0.0

    self.prev_lap_time = RaceTime()
    self.best_lap_time = RaceTime(float("inf"), "00:00.000")  # Get this from storage

    self.lap_timer_stopped = True

    # Lap validation
    self.is_human = is_human
    self.valid_lap = True
    self.world_timer = 0.0

  def start_lap_timer(self):
    self.curr_lap_time = RaceTime()
    self.curr_sector_time = 0.0
    self.sector_times = [RaceTime(0.0, "00.000") for _ in range(3)]
    self.lap_timer_stopped = False
    self.valid_lap = True

    if self.is_human:
      self.world_timer = time.perf_counter()

  def update_timer(self, dt: float):
    self.curr_lap_time.update_time(self.curr_lap_time.sec + dt, is_lap_time=True)
    self.curr_sector_time += dt

  def stop_lap_timer(self):
    self.lap_timer_stopped = True

  def set_lap_time(self):
    self.prev_lap_time = self.curr_lap_time
    self.curr_lap_time = RaceTime()
    self.curr_sector_time = 0.0
    self.valid_lap = True

    if self.is_human:
      self.world_timer = time.perf_counter()
      real_time_ratio = (
        (time.perf_counter() - self.world_timer) * 1000 / self.prev_lap_time.sec
      )
      if self.prev_lap_time.sec != 0.0 and real_time_ratio > 1.10:
        print("lap invalidated for desynced time")  # Draw this
        self.valid_lap = False

    if self.valid_lap and self.best_lap_time.sec > self.prev_lap_time.sec:
      self.best_lap_time.update_time(self.prev_lap_time.sec, is_lap_time=True)

    for i in range(3):
      self.prev_sector_times[i].update_time(self.sector_times[i].sec)
      self.sector_times[i] = RaceTime(0.0, "00.000")

  def set_sector_time(self, sector: int):
    sector_i = sector - 1
    self.sector_times[sector_i].update_time(self.curr_sector_time)
    self.curr_sector_time = 0.0
    if self.best_sector_times[sector_i].sec > self.sector_times[sector_i].sec:
      self.best_sector_times[sector_i].update_time(self.sector_times[sector_i].sec)
