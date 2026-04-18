"""Game constants + enums.

Python features demonstrated in this file:
- ``typing.Final`` for immutable configuration values
- ``enum.Enum`` and ``enum.StrEnum`` for type-safe state/direction constants
- ``typing.NamedTuple`` for a lightweight immutable record (BiomePalette)
- Dictionary literal with ``NamedTuple`` values as a data table
"""
from __future__ import annotations

from enum import Enum, StrEnum
from typing import Final, NamedTuple

# --- Screen / physics tuning (Final = "do not reassign") ----------------------
SCREEN_W: Final[int] = 800
SCREEN_H: Final[int] = 600
FPS: Final[int]      = 60

GRAVITY:        Final[float] = 0.5
JUMP_VEL:       Final[int]   = -13
PLAYER_SPEED:   Final[int]   = 4
BULLET_SPEED:   Final[int]   = 8
SHOOT_COOLDOWN: Final[int]   = 300
BANNER_FRAMES:  Final[int]   = FPS * 2

ENEMY_SIGHT_RANGE:   Final[int] = 320
ENEMY_JUMP_COOLDOWN: Final[int] = 45

# --- Color constants (plain tuples; pygame accepts any (r, g, b) tuple) -------
BLACK          = (0,   0,   0)
PLATFORM_COLOR = (70,  80,  100)
PLATFORM_SHINE = (100, 115, 140)
PLAYER_COLOR   = (255, 120, 80)
ENEMY_COLOR    = (220, 40,  40)
BULLET_COLOR   = (255, 230, 50)
BULLET_INNER   = (255, 255, 200)
TEXT_COLOR     = (240, 240, 240)
PORTAL_COLOR   = (80,  255, 180)
PORTAL_INNER   = (200, 255, 230)
HINT_COLOR     = (120, 130, 150)
DIM_COLOR      = (160, 170, 200)
TREE_TRUNK     = (90,  55,  30)
TREE_LEAVES    = (40,  130, 55)


# --- Enums: type-safe, explicit set of allowed values -------------------------
class GameState(StrEnum):
    """Finite state of the main loop. ``StrEnum`` lets us compare to strings."""
    WELCOME  = "welcome"
    PLAYING  = "playing"
    GAMEOVER = "gameover"
    VICTORY  = "victory"


class AiType(StrEnum):
    """Supported enemy AI strategies."""
    PATROL = "patrol"
    CHASE  = "chase"
    JUMPER = "jumper"


# --- NamedTuple: a tiny, immutable record with named fields -------------------
class BiomePalette(NamedTuple):
    """Color palette per biome. Immutable, indexable, iterable."""
    bg:       tuple[int, int, int]
    platform: tuple[int, int, int]
    shine:    tuple[int, int, int]


BIOMES: Final[dict[str, BiomePalette]] = {
    "meadow":     BiomePalette((70,  140, 90),  (95,  65,  40),  (130, 95,  60)),
    "swamp":      BiomePalette((50,  60,  35),  (60,  70,  45),  (90,  100, 70)),
    "desert":     BiomePalette((210, 175, 105), (165, 125, 70),  (200, 160, 100)),
    "forest":     BiomePalette((25,  80,  40),  (75,  55,  35),  (110, 85,  55)),
    "crossroads": BiomePalette((80,  80,  90),  (120, 120, 130), (160, 160, 170)),
    "cave":       BiomePalette((20,  20,  35),  (70,  80,  100), (100, 115, 140)),
    "snow":       BiomePalette((220, 235, 250), (180, 200, 220), (230, 240, 255)),
    "mountain":   BiomePalette((95,  100, 120), (130, 130, 150), (180, 180, 200)),
    "volcano":    BiomePalette((60,  20,  20),  (100, 40,  30),  (200, 70,  40)),
}


# Backwards-compatible string aliases so modules can still import WELCOME etc.
WELCOME  = GameState.WELCOME
PLAYING  = GameState.PLAYING
GAMEOVER = GameState.GAMEOVER
VICTORY  = GameState.VICTORY
BANNER   = "banner"  # kept for legacy imports; no longer a primary state
