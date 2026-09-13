# Comments are based off of starting position (0, 0) and a starting rotation of 0 deg
# Make sure points are >= 10m apart to avoid boundary loops if turning and points don't create a jagged inner corner
# Add more points in between if jagged to smoothen it out
tracks: list[dict[str, str | int | tuple[int, int]]] = [
  # Small square
  {
    "name": "Small Square",
    "finish": 8,
    "length": 378.94,
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
  # Long straights + 2 turns
  {
    "name": "Speed Lanes",
    "finish": 3,
    "length": 3210.37,
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
  {
    "name": "Half Pipe",
    "finish": 2,
    "length": 2542.57,
    "track": (
      # Main straight
      (-550, 0),
      (-500, 0),
      (0, 0),  # Finish line
      (500, 0),
      (550, 0),
      # T1 (up -> right)
      (576, 1),
      (590, 5),  # Apex 1/2
      (600, 15),  # Apex 2/2
      (604, 30),
      (605, 45),
      # Short straight
      (605, 65),
      (605, 115),
      # T2 (right -> down)
      (604, 135),
      (600, 150),
      # Connector
      (590, 160),  # Apex 1/2
      (558, 160),  # Apex 2/2
      # T3 (down -> left)
      (548, 150),
      (544, 135),
      (543, 115),
      # T4 (left -> down)
      (543, 80),
      (542, 63),
      (535, 50),  # Apex
      (523, 44),
      # Back straight
      (508, 43),
      (497, 43),
      (-493, 43),
      (-508, 43),
      # T5 (down -> right)
      (-523, 44),
      (-535, 50),  # Apex
      (-542, 63),
      # T6 (right -> down)
      (-543, 80),
      (-543, 115),
      (-544, 135),
      (-548, 150),
      # Connector
      (-558, 160),  # Apex 1/2
      (-590, 160),  # Apex 2/2
      # T7 (down -> left)
      (-600, 150),
      (-604, 135),
      # Short straight
      (-605, 115),
      (-605, 65),
      # T8 (left -> up)
      (-605, 45),
      (-604, 30),
      (-600, 15),  # Apex 1/2
      (-590, 5),  # Apex 2/2
      (-576, 1),
    ),
  },
]
