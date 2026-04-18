"""World map: a 3x3 grid of connected areas.

Python features demonstrated:
- ``enum.Enum`` with behavior (``Direction.opposite``, ``Direction.delta``)
- ``@dataclass(frozen=True)`` for immutable value objects
- ``typing.TypedDict`` would work too; we use dataclasses here for methods
- ``itertools.product`` to generate grid coords
- ``collections.deque`` for a breadth-first-search
- Module-level data definition vs. derivation (``AREAS`` + ``neighbor``)
- ``match``/``case`` pattern matching

Grid layout (col, row):
    (0,0) snow      (1,0) mountain   (2,0) volcano/GOAL
    (0,1) forest    (1,1) crossroads (2,1) cave
    (0,2) swamp     (1,2) START      (2,2) desert
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import product
from typing import Iterable

from constants import SCREEN_W, SCREEN_H, BIOMES, AiType, BiomePalette, ItemKind

Coord = tuple[int, int]

GRID_W, GRID_H = 3, 3
START_COORD: Coord = (1, 2)
GOAL_COORD:  Coord = (2, 0)


class Direction(Enum):
    """Cardinal directions. Each member carries a delta and opposite."""
    LEFT  = "left"
    RIGHT = "right"
    UP    = "up"
    DOWN  = "down"

    @property
    def delta(self) -> Coord:
        # match/case (3.10+) — exhaustive, readable branching
        match self:
            case Direction.LEFT:  return (-1,  0)
            case Direction.RIGHT: return ( 1,  0)
            case Direction.UP:    return ( 0, -1)
            case Direction.DOWN:  return ( 0,  1)

    @property
    def opposite(self) -> "Direction":
        return {
            Direction.LEFT:  Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
            Direction.UP:    Direction.DOWN,
            Direction.DOWN:  Direction.UP,
        }[self]


# Legacy string-keyed maps kept for backwards-compat with tests/imports
DELTA    = {d.value: d.delta    for d in Direction}
OPPOSITE = {d.value: d.opposite.value for d in Direction}


# --- Dataclasses: immutable, readable, auto __init__/__repr__/__eq__ ----------
@dataclass(frozen=True)
class PlatformSpec:
    x: int
    y: int
    w: int
    h: int = 14


@dataclass(frozen=True)
class EnemySpawn:
    x: int
    y: int
    ai: AiType


@dataclass(frozen=True)
class Decoration:
    kind: str
    x: int
    y: int


@dataclass(frozen=True)
class ItemSpawn:
    x:    int
    y:    int
    kind: ItemKind


@dataclass(frozen=True)
class AreaDef:
    biome:     str
    name:      str
    platforms: tuple[PlatformSpec, ...]
    enemies:   tuple[EnemySpawn, ...]  = ()
    decor:     tuple[Decoration, ...]  = ()
    items:     tuple[ItemSpawn, ...]   = ()

    @property
    def palette(self) -> BiomePalette:
        return BIOMES[self.biome]


def _plats(*tuples) -> tuple[PlatformSpec, ...]:
    """Small helper: turn positional (x, y, w) tuples into PlatformSpec."""
    return tuple(PlatformSpec(*t) for t in tuples)


def _enemies(*tuples) -> tuple[EnemySpawn, ...]:
    return tuple(EnemySpawn(x, y, AiType(a)) for (x, y, a) in tuples)


def _items(*tuples) -> tuple[ItemSpawn, ...]:
    return tuple(ItemSpawn(x, y, ItemKind(k)) for (x, y, k) in tuples)


AREAS: dict[Coord, AreaDef] = {}  # populated below; mutable (procgen can swap it)

_CLASSIC_AREAS: dict[Coord, AreaDef] = {
    (0, 0): AreaDef(
        biome="snow", name="Snowy Peaks",
        platforms=_plats(
            (0,   570, 350), (450, 570, 350),
            (100, 460, 150), (350, 400, 120), (560, 460, 150),
            (200, 300, 150), (470, 280, 180),
        ),
        enemies=_enemies((600, 440, "patrol"), (300, 280, "chase")),
        items=_items((410, 400, "potion")),
    ),
    (1, 0): AreaDef(
        biome="mountain", name="Stone Ridge",
        platforms=_plats(
            (0,   570, 360), (460, 570, 340),
            (100, 470, 140), (300, 400, 130), (520, 470, 160),
            (180, 300, 130), (440, 270, 160), (650, 300, 120),
        ),
        enemies=_enemies((150, 440, "patrol"), (540, 440, "jumper"),
                         (460, 240, "chase")),
        items=_items((710, 300, "speed")),
    ),
    (2, 0): AreaDef(
        biome="volcano", name="Volcano Summit",
        platforms=_plats(
            (0,   570, 400), (500, 570, 300),
            (120, 460, 160), (370, 420, 150), (580, 460, 200),
            (200, 310, 180), (470, 280, 200),
            (330, 170, 140),
        ),
        enemies=_enemies((150, 540, "patrol"), (620, 540, "jumper"),
                         (260, 280, "chase"),  (530, 250, "jumper")),
        decor=(Decoration("altar", 400, 170),),
        items=_items((260, 310, "potion"), (670, 460, "jump")),
    ),
    (0, 1): AreaDef(
        biome="forest", name="Old Forest",
        platforms=_plats(
            (0,   570, 200), (280, 570, 520),
            (120, 470, 130), (330, 440, 140), (550, 470, 160),
            (200, 330, 130), (420, 300, 150), (630, 340, 140),
            (280, 150, 200),
        ),
        enemies=_enemies((400, 410, "patrol"), (640, 310, "chase")),
        decor=(Decoration("tree", 680, 570),),
        items=_items((380, 150, "speed")),
    ),
    (1, 1): AreaDef(
        biome="crossroads", name="Crossroads",
        platforms=_plats(
            (0,   570, 340), (460, 570, 340),
            (80,  470, 150), (280, 430, 150), (500, 470, 150), (680, 430, 120),
            (180, 320, 150), (420, 290, 150), (620, 320, 150),
            (300, 140, 200),
        ),
        enemies=_enemies((120, 440, "patrol"), (530, 440, "jumper"),
                         (440, 260, "chase")),
        items=_items((400, 140, "jump"), (740, 430, "potion")),
    ),
    (2, 1): AreaDef(
        biome="cave", name="Deep Cave",
        platforms=_plats(
            (0,   570, 400), (480, 570, 320),
            (100, 480, 130), (320, 440, 140), (550, 470, 150),
            (200, 340, 130), (430, 300, 140), (630, 340, 120),
            (250, 140, 180),
        ),
        enemies=_enemies((160, 450, "patrol"), (570, 440, "jumper"),
                         (470, 270, "chase")),
        items=_items((330, 140, "speed"), (160, 480, "potion")),
    ),
    (0, 2): AreaDef(
        biome="swamp", name="Murky Swamp",
        platforms=_plats(
            (0,   570, 800),
            (80,  470, 150), (300, 430, 150), (540, 470, 150),
            (200, 320, 140), (450, 290, 160), (660, 340, 120),
            (200, 140, 200),
        ),
        enemies=_enemies((400, 540, "patrol"), (600, 300, "chase")),
        items=_items((260, 140, "potion")),
    ),
    (1, 2): AreaDef(
        biome="meadow", name="Home Meadow",
        platforms=_plats(
            (0,   570, 800),
            (100, 470, 150), (320, 440, 150), (540, 470, 150),
            (220, 330, 140), (450, 300, 160), (660, 340, 120),
            (300, 140, 200),
        ),
        decor=(Decoration("sign", 120, 570),),
        items=_items((530, 300, "potion"), (400, 140, "jump")),
    ),
    (2, 2): AreaDef(
        biome="desert", name="Sand Dunes",
        platforms=_plats(
            (0,   570, 800),
            (80,  480, 140), (300, 450, 150), (520, 470, 160),
            (150, 340, 140), (400, 310, 150), (630, 340, 130),
            (250, 150, 200),
        ),
        enemies=_enemies((500, 540, "patrol"), (400, 280, "jumper")),
        items=_items((470, 310, "speed")),
    ),
}

# Populate AREAS with the classic content by default.
AREAS.update(_CLASSIC_AREAS)


def use_classic_world() -> None:
    """Reset AREAS to the hand-crafted layout."""
    AREAS.clear()
    AREAS.update(_CLASSIC_AREAS)


def use_procgen_world(seed: int) -> None:
    """Replace AREAS with a seed-generated set of areas."""
    from procgen import generate_world
    AREAS.clear()
    AREAS.update(generate_world(seed))


# --- Grid utilities -----------------------------------------------------------
def all_coords() -> Iterable[Coord]:
    """Generator of all valid (col, row) pairs using itertools.product."""
    yield from product(range(GRID_W), range(GRID_H))


def in_bounds(coord: Coord) -> bool:
    x, y = coord
    return 0 <= x < GRID_W and 0 <= y < GRID_H


def neighbor(coord: Coord, direction) -> Coord | None:
    """Accepts ``Direction`` enum or its string value."""
    d = direction if isinstance(direction, Direction) else Direction(direction)
    dx, dy = d.delta
    nxt: Coord = (coord[0] + dx, coord[1] + dy)
    return nxt if in_bounds(nxt) and nxt in AREAS else None


def reachable_from(start: Coord) -> set[Coord]:
    """Breadth-first search over the area graph (uses collections.deque)."""
    seen: set[Coord] = {start}
    q: deque[Coord] = deque([start])
    while q:
        cur = q.popleft()
        for d in Direction:
            nxt = neighbor(cur, d)
            if nxt is not None and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def edge_direction(player_rect) -> str | None:
    """Return the direction string the player crossed, or None."""
    if player_rect.right  < 0:         return Direction.LEFT.value
    if player_rect.left   > SCREEN_W:  return Direction.RIGHT.value
    if player_rect.bottom < 0:         return Direction.UP.value
    if player_rect.top    > SCREEN_H:  return Direction.DOWN.value
    return None


def spawn_position(enter_from: str) -> Coord:
    """Walrus-operator + match/case example."""
    margin = 40
    match enter_from:
        case "right": return (SCREEN_W - margin, 100)
        case "left":  return (margin,            100)
        case "down":  return (SCREEN_W // 2,     SCREEN_H - 80)
        case "up":    return (SCREEN_W // 2,     20)
        case _:       return (80, SCREEN_H - 80)


def spawn_area(coord: Coord, Platform, Enemy, Item=None,
               entry_from: str | None = None, player=None,
               collected: set[tuple] | None = None):
    """Instantiate platforms, enemies, and pickup items for an area.

    ``collected`` is a set of (coord, item_index) tuples that have already
    been picked up in this run — those items are skipped.
    """
    defn      = AREAS[coord]
    palette   = defn.palette
    platforms = [Platform(p.x, p.y, p.w, p.h,
                          color=palette.platform, shine=palette.shine)
                 for p in defn.platforms]
    enemies   = [Enemy(e.x, e.y, e.ai.value) for e in defn.enemies]
    decor     = [(d.kind, d.x, d.y) for d in defn.decor]

    items: list = []
    if Item is not None:
        collected = collected or set()
        for idx, spec in enumerate(defn.items):
            if (coord, idx) in collected:
                continue
            it      = Item(spec.x, spec.y, spec.kind)
            it.uid  = (coord, idx)
            items.append(it)

    if player is not None and entry_from is not None:
        px, py = spawn_position(entry_from)
        player.rect.x      = px - player.rect.width  // 2
        player.rect.y      = py - player.rect.height
        player.vel_y       = 0
        player.projectiles = []

    return platforms, enemies, palette.bg, decor, items
