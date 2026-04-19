from __future__ import annotations

import random
from dataclasses import dataclass, field

from constants import BIOMES, GOAL_COORD, GRID_H, GRID_W, START_COORD


@dataclass
class Area:
    coord:     tuple[int, int]
    platforms: list[tuple[int, int, int]] = field(default_factory=list)  # (x, y, w)
    enemies:   list[dict]                 = field(default_factory=list)
    items:     list[dict]                 = field(default_factory=list)
    decor:     list[dict]                 = field(default_factory=list)
    name:      str                        = ""
    biome:     str                        = ""

    @property
    def floor_y(self) -> int:
        return GRID_H - 1


def _neighbor_exists(coord: tuple[int, int], dx: int, dy: int) -> bool:
    nx, ny = coord[0] + dx, coord[1] + dy
    return 0 <= nx < 3 and 0 <= ny < 3


def generate_area(coord: tuple[int, int], rng: random.Random) -> Area:
    name, biome = BIOMES[coord]
    has_down = _neighbor_exists(coord, 0, 1)
    has_up   = _neighbor_exists(coord, 0, -1)

    platforms: list[tuple[int, int, int]] = []
    if has_down:
        left_w = rng.randint(15, 25)
        platforms.append((0, GRID_H - 1, left_w))
        platforms.append((left_w + 8, GRID_H - 1, GRID_W - left_w - 8))
    else:
        platforms.append((0, GRID_H - 1, GRID_W))

    for y in (GRID_H - 6, GRID_H - 11):
        x = rng.randint(2, 8)
        while x < GRID_W - 6:
            w = rng.randint(5, 12)
            platforms.append((x, y, w))
            x += w + rng.randint(3, 8)

    if has_up:
        platforms.append((GRID_W // 2 - 7, 2, 14))

    enemies: list[dict] = []
    if coord != START_COORD:
        for _ in range(rng.randint(1, 3)):
            targets = [p for p in platforms if p[1] < GRID_H - 1]
            plat = rng.choice(targets or platforms)
            ex = plat[0] + rng.randint(1, max(2, plat[2] - 2))
            ey = plat[1] - 1
            ai = rng.choice(("patrol", "chase", "jumper"))
            enemies.append({"x": ex, "y": ey, "ai": ai, "alive": True})

    items: list[dict] = []
    for i in range(rng.randint(0, 2) + (1 if coord == START_COORD else 0)):
        targets = [p for p in platforms if p[1] < GRID_H - 1]
        plat = rng.choice(targets or platforms)
        ix = plat[0] + rng.randint(1, max(2, plat[2] - 2))
        iy = plat[1] - 1
        kind = rng.choice(("potion", "speed", "jump"))
        items.append({"x": ix, "y": iy, "kind": kind, "alive": True,
                      "uid": [list(coord), i]})

    decor: list[dict] = []
    if coord == GOAL_COORD:
        decor.append({"kind": "altar", "x": GRID_W // 2, "y": 2})
    if coord == START_COORD:
        decor.append({"kind": "sign", "x": 3, "y": GRID_H - 2})
    if biome == "forest":
        decor.append({"kind": "tree", "x": rng.randint(5, GRID_W - 5),
                      "y": GRID_H - 2})

    return Area(coord=coord, platforms=platforms, enemies=enemies,
                items=items, decor=decor, name=name, biome=biome)


def generate_world(seed: int) -> dict[tuple[int, int], Area]:
    rng = random.Random(seed)
    return {coord: generate_area(coord, rng) for coord in BIOMES}
