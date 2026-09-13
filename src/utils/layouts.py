# Comments are based off of starting position (0, 0) and a starting rotation of 0 deg
# Make sure points are >= 10m apart to avoid boundary loops if turning and points don't create a jagged inner corner
# Add more points in between if jagged to smoothen it out
tracks: list[dict[str, str | int | tuple[int, int]]] = [
  # Small square  (Track 1)
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
  # Long straights + 2 turns (Track 2)
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
  # Like a stubby table (Track 3)
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
  # Chicanes (Track 4)
  {
    "name": "Chicane City",
    "finish": 1,
    "length": 1196.33,
    "track": (
      # Main straight
      (-54, 0),
      (0, 0),
      (16, 0),
      # T1, chicane entrance (up -> right)
      (36, 0),
      (43, 3),
      (46, 8),
      (46, 16),
      # T2, chicane exit (right -> up)
      (46, 24),
      (49, 29),
      (57, 33),
      # T3, hairpin (up -> down)
      (85, 36),
      (92, 42),
      (94, 50),
      (92, 58),
      (85, 65),
      (78, 67),
      (71, 66),
      # Straight
      (55, 62),
      (38, 61),
      (28, 61),
      (-9, 61),
      # T4, chicane entrance (down -> right)
      (-27, 61),
      (-33, 64),
      (-37, 70),
      (-36, 81),
      # T5, chicane exit (right -> down)
      (-36, 87),
      (-39, 93),
      (-44, 97),
      (-51, 98),
      # T6 (down -> SW)
      (-62, 97),
      (-84, 90),
      # Straight
      (-98, 79),
      (-126, 46),
      # T7, chicance entrance (SW -> up)
      (-136, 34),
      (-139, 29),
      (-140, 24),
      (-138, 18),
      (-130, 12),
      (-123, 11),
      # T8, chicane exit into mini hairpin (up -> SW)
      (-115, 12),
      (-109, 12),
      (-101, 9),
      (-94, 0),
      (-94, -8),
      (-102, -19),
      (-122, -31),
      # T9, wide hairpin (SW -> NW)
      (-134, -43),
      (-139, -54),
      (-137, -74),
      # Straight
      (-127, -90),
      (47, -124),
      # T10, chicane entrance (NW -> right)
      (55, -121),
      (58, -116),
      (58, -108),
      # T11, chicane exit (right -> up)
      (58, -100),
      (61, -95),
      (66, -92),
      # T12, wide hairpin (up -> SW)
      (74, -90),
      (80, -86),
      (86, -76),
      (86, -49),
      (79, -39),
      (65, -32),
      (47, -33),
      (25, -43),
      # T13
      (-1, -72),
      (-21, -85),
      # T14, chicane entrance (SW -> right)
      (-32, -87),
      (-39, -83),
      (-42, -76),
      (-42, -68),
      # T15, chicane exit (right -> down)
      (-43, -60),
      (-48, -54),
      # T16, wide hairpin (down -> up)
      (-61, -50),
      (-67, -45),
      (-71, -38),
      (-72, -32),
      (-72, -16),
      (-71, -9),
      (-68, -4),
      (-62, -1),
    ),
  },
]
