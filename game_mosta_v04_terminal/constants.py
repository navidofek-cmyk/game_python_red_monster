from __future__ import annotations

from enum import StrEnum
from pathlib import Path

GRID_W      = 60
GRID_H      = 18
HUD_H       = 5
TICK_MS     = 80
SAVE_FILE   = Path(__file__).resolve().parent / "save.json"
MAX_HP      = 3
BOSS_HP     = 6
JUMP_VEL    = -5
BOOST_TICKS = 50

START_COORD = (1, 2)
GOAL_COORD  = (2, 0)


class Tile(StrEnum):
    EMPTY    = " "
    PLATFORM = "="
    PLAYER   = "@"
    PATROL   = "P"
    CHASE    = "C"
    JUMPER   = "J"
    BOSS     = "$"
    ALTAR    = "#"
    TREE     = "T"
    SIGN     = "!"
    POTION   = "o"
    SPEED    = ">"
    JUMP     = "^"
    BULLET   = "-"
    WALL     = "|"


class ItemKind(StrEnum):
    POTION = "potion"
    SPEED  = "speed"
    JUMP   = "jump"


BIOMES: dict[tuple[int, int], tuple[str, str]] = {
    (0, 0): ("Snowy Peaks",    "snow"),
    (1, 0): ("Stone Ridge",    "mountain"),
    (2, 0): ("Volcano Summit", "volcano"),
    (0, 1): ("Old Forest",     "forest"),
    (1, 1): ("Crossroads",     "crossroads"),
    (2, 1): ("Deep Cave",      "cave"),
    (0, 2): ("Murky Swamp",    "swamp"),
    (1, 2): ("Home Meadow",    "meadow"),
    (2, 2): ("Sand Dunes",     "desert"),
}
