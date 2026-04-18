"""Procedural area generator.

Given a seed, produces a full ``dict[Coord, AreaDef]`` world that matches
the same shape as the hand-crafted ``world.AREAS``. Using the same seed
always yields the same world (reproducibility = makes bugs debuggable and
makes it possible to "share" a run by exchanging the seed number).

Python features demonstrated:
- ``random.Random(seed)`` for a seeded, isolated RNG (no global state)
- Module-level strategies expressed as small helper functions
- Generators + comprehensions
- Type aliases and ``@dataclass`` reuse from ``world.py``
"""
from __future__ import annotations

import random
from typing import Callable

from constants import SCREEN_W, SCREEN_H, AiType, ItemKind
from world     import (
    AreaDef, PlatformSpec, EnemySpawn, Decoration, ItemSpawn,
    Coord, Direction, GRID_W, GRID_H, START_COORD, GOAL_COORD, in_bounds,
)

# Biome assignment is kept stable so the "story shape" stays the same: even
# a random world still progresses meadow -> forest/swamp -> cave -> volcano.
BIOME_MAP: dict[Coord, str] = {
    (0, 0): "snow",      (1, 0): "mountain",  (2, 0): "volcano",
    (0, 1): "forest",    (1, 1): "crossroads", (2, 1): "cave",
    (0, 2): "swamp",     (1, 2): "meadow",    (2, 2): "desert",
}

AREA_NAMES: dict[Coord, str] = {
    (0, 0): "Snowy Peaks",  (1, 0): "Stone Ridge", (2, 0): "Volcano Summit",
    (0, 1): "Old Forest",   (1, 1): "Crossroads",  (2, 1): "Deep Cave",
    (0, 2): "Murky Swamp",  (1, 2): "Home Meadow", (2, 2): "Sand Dunes",
}


def _neighbor_exists(coord: Coord, direction: Direction) -> bool:
    dx, dy = direction.delta
    return in_bounds((coord[0] + dx, coord[1] + dy))


def _random_floor(rng: random.Random, has_down: bool) -> list[PlatformSpec]:
    """Build the ground. If down-neighbor exists, leaves a pit in the middle."""
    if not has_down:
        return [PlatformSpec(0, 570, SCREEN_W)]
    pit_w    = rng.randint(80, 140)
    pit_left = rng.randint(260, SCREEN_W - pit_w - 260)
    return [
        PlatformSpec(0,              570, pit_left),
        PlatformSpec(pit_left + pit_w, 570, SCREEN_W - pit_left - pit_w),
    ]


def _row_platforms(rng: random.Random, y: int, count: int,
                   min_w: int = 90, max_w: int = 180) -> list[PlatformSpec]:
    """Place ``count`` platforms on a horizontal row at height ``y``."""
    slot = SCREEN_W // count
    out  = []
    for i in range(count):
        w = rng.randint(min_w, max_w)
        x = i * slot + rng.randint(10, max(11, slot - w - 10))
        out.append(PlatformSpec(x, y + rng.randint(-10, 10), w))
    return out


def _place_enemies(rng: random.Random, platforms: list[PlatformSpec],
                   count: int) -> list[EnemySpawn]:
    ai_pool = [AiType.PATROL, AiType.CHASE, AiType.JUMPER]
    spawns  = []
    # Skip the very first (floor) platform for variety; spawn on random others.
    targets = [p for p in platforms if p.y < 560]
    if not targets:
        targets = platforms
    for _ in range(count):
        plat = rng.choice(targets)
        x    = plat.x + rng.randint(10, max(11, plat.w - 40))
        y    = plat.y - 4
        ai   = rng.choice(ai_pool)
        spawns.append(EnemySpawn(x, y, ai))
    return spawns


def _place_items(rng: random.Random, platforms: list[PlatformSpec],
                 count: int) -> list[ItemSpawn]:
    kinds   = [ItemKind.POTION, ItemKind.SPEED, ItemKind.JUMP]
    targets = [p for p in platforms if p.y < 560]
    if not targets:
        targets = platforms
    spawns = []
    for _ in range(count):
        plat = rng.choice(targets)
        x    = plat.x + rng.randint(15, max(16, plat.w - 15))
        y    = plat.y
        spawns.append(ItemSpawn(x, y, rng.choice(kinds)))
    return spawns


def generate_area(coord: Coord, rng: random.Random) -> AreaDef:
    has_up   = _neighbor_exists(coord, Direction.UP)
    has_down = _neighbor_exists(coord, Direction.DOWN)

    platforms: list[PlatformSpec] = []
    platforms.extend(_random_floor(rng, has_down))
    platforms.extend(_row_platforms(rng, 470, 3))
    platforms.extend(_row_platforms(rng, 320, 3))
    if has_up:
        # A high platform near the top so the player can jump up a level.
        platforms.append(PlatformSpec(
            rng.randint(200, SCREEN_W - 400), 150, rng.randint(160, 220)))

    enemies = _place_enemies(rng, platforms, rng.randint(2, 4))
    # Start area keeps enemy count at 0 for a gentle opening.
    if coord == START_COORD:
        enemies = []
    items   = _place_items(rng, platforms, rng.randint(1, 2))

    decor: list[Decoration] = []
    if coord == GOAL_COORD:
        decor.append(Decoration("altar", 400, 170))
    elif coord == START_COORD:
        decor.append(Decoration("sign", 120, 570))
    elif BIOME_MAP[coord] == "forest":
        decor.append(Decoration("tree", rng.randint(100, SCREEN_W - 100), 570))

    return AreaDef(
        biome     = BIOME_MAP[coord],
        name      = AREA_NAMES[coord] + "*",  # star marks procgen
        platforms = tuple(platforms),
        enemies   = tuple(enemies),
        decor     = tuple(decor),
        items     = tuple(items),
    )


def generate_world(seed: int) -> dict[Coord, AreaDef]:
    rng   = random.Random(seed)
    world = {}
    for y in range(GRID_H):
        for x in range(GRID_W):
            world[(x, y)] = generate_area((x, y), rng)
    return world
