# Comments are based off of starting position (0, 0) and a starting rotation of 0 deg
# Make sure points are >= 10m apart to avoid boundary loops if turning and points don't create a jagged inner corner
# Add more points in between if jagged to smoothen it out
tracks: dict[str, str | int | tuple[int, int]] = [
  {  # Small square
    "name": "Small Square",
    "finish": 8,
    "track": (
      # Bottom straight (going right)
      (0, -90),
      (0, -70),
      (0, -55),
      (0, -45),
      (0, -30),
      (0, -10),
      # Main straight (going up)
      (10, 0),
      (30, 0),
      (45, 0),  # finish line
      (55, 0),
      (70, 0),
      (90, 0),
      # Top straight (going Left)
      (100, -10),
      (100, -30),
      (100, -45),
      (100, -55),
      (100, -70),
      (100, -90),
      # Left straight (going down)
      (90, -100),
      (70, -100),
      (55, -100),
      (45, -100),
      (30, -100),
      (10, -100),
    ),
  },
  {  # Long straights + 2 turns
    "name": "Speed Lanes",
    "finish": 3,
    "track": (
      # Main straight (up)
      (-750, 0),
      (-720, 0),
      (-680, 0),
      (0, 0),  # Finish line
      (680, 0),
      (720, 0),
      (750, 0),
      # T1, Top hairpin (up -> right -> down)
      (775, 5),
      (790, 15),  # Apex 1/2
      (790, 30),  # Apex 2/2
      (775, 40),
      # Straight 2 (down)
      (750, 30),
      (720, 30),
      (680, 30),
      (0, 30),
      (-680, 30),
      (-720, 30),
      (-750, 30),
      # T2, Bottom hairpin (down -> left -> up)
      (-775, 25),
      (-790, 15),  # Apex 1/2
      (-790, 0),  # Apex 2/2
      (-775, -10),
    ),
  },
  {  # Half pipe
    "name": "Half Pipe",
    "finish": 2,
    "track": (
      (
        # Main straight (up)
        (-550, 0),
        (-500, 0),
        (0, 0),  # Finish line
        (500, 0),
        (550, 0),
        # T1, 90 deg (right)
        (570, 0),
        # (586, 10),
        (580, 25),
        # (610, 40),
        (590, 70),
        # Straight (right)
        (630, 100),
        (630, 200),
        (630, 220),
        (630, 210),
      )
    ),
  },
]
