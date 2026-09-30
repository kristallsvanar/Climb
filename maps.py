"""Map data. To make a new map, copy CASTLE_1 and edit the platform list.

Each platform is:  (rise, column, pattern[, dart_side])
  rise    - how many blocks higher than the PREVIOUS platform
  column  - left-most column (the castle interior is columns 2..17)
  pattern - one character per block:
              =  stone ledge (you can jump up through it)
              B  bouncy block
              ^  stone ledge with a spike on top
  dart_side - optional "L" or "R": a dart trap in that wall fires across the platform

The Level checks every jump when the game loads and raises a clear error if a jump is
impossible, so a map you edit can never be secretly unbeatable.
"""
from settings import COLS

FLOOR = "=" * 16        # a full-width rest ledge (also catches you if you fall)

# ---- Section A: the dungeon entrance (gentle, wide ledges) ----
SECTION_A = [
    (2, 3, "======"), (2, 10, "====="), (2, 3, "====="), (1, 9, "===="), (2, 14, "==="),
    (2, 8, "====="), (2, 3, "===="), (3, 6, "====="), (1, 12, "===="), (3, 2, FLOOR),
]

# ---- Section B: first spikes, first bouncy blocks, first darts ----
SECTION_B = [
    (2, 3, "==^^==="), (2, 12, "====="), (2, 6, "====="), (2, 2, "=B=="), (5, 8, "====="),
    (2, 4, "==^^===="), (2, 13, "====", "R"), (2, 6, "======"), (3, 3, "====="),
    (1, 10, "=====", "L"), (2, 4, "===="), (3, 2, FLOOR),
]

# ---- Section C: bounce towers ----
SECTION_C = [
    (2, 3, "=B==="), (6, 9, "===="), (2, 14, "===B"), (7, 9, "====="), (2, 3, "==^^===="),
    (2, 12, "=====", "R"), (3, 6, "======"), (2, 2, "==B=="), (6, 9, "=====", "L"),
    (2, 4, "====="), (2, 10, "==^^=="), (3, 3, "======"), (1, 11, "====", "R"), (3, 2, FLOOR),
]

# ---- Section D: the hard climb (everything at once) ----
SECTION_D = [
    (2, 3, "==^^==="), (2, 12, "===", "L"), (2, 6, "===="), (2, 2, "=B==="), (7, 7, "====="),
    (2, 13, "===B", "R"), (6, 6, "======"), (2, 13, "==="), (2, 7, "=====", "R"),
    (3, 2, "=B=="), (7, 7, "====="), (2, 3, "==^^===="), (2, 12, "====", "L"),
    (2, 6, "====="), (2, 12, "==="), (2, 5, "===="), (2, 10, "==="), (2, 4, "=====", "R"),
    (3, 2, FLOOR),
]


def mirror(section):
    """Flip a section left <-> right so the climb feels different the second time."""
    out = []
    for rise, col, pattern, *dart in section:
        entry = (rise, COLS - (col + len(pattern)), pattern[::-1])
        if dart:
            entry += ({"L": "R", "R": "L"}[dart[0]],)
        out.append(entry)
    return out


CASTLE_1 = {
    "name": "The Cramped Castle",
    "platforms": (SECTION_A + SECTION_B + SECTION_C + SECTION_D
                  + mirror(SECTION_B) + mirror(SECTION_C) + mirror(SECTION_D)),
    "speed_boosts": 8,      # random speed power-ups spread through the castle
    "hearts": 1,            # never more than one heart in the castle
}
