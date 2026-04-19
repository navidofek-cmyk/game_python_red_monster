"""Game state dataclass, tick logic, and player actions."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from constants import (
    BOOST_TICKS, GOAL_COORD, GRID_H, GRID_W, JUMP_VEL, MAX_HP, START_COORD,
)
from entities import Boss, Player, apply_gravity, is_platform_at, move_enemy, on_ground
from world import Area, generate_world


@dataclass
class Game:
    world:         dict            = field(default_factory=dict)
    coord:         tuple[int, int] = START_COORD
    player:        Player          = field(default_factory=Player)
    boss:          Boss | None     = None
    boss_defeated: bool            = False
    portal_active: bool            = False
    visited:       set             = field(default_factory=lambda: {START_COORD})
    collected:     set             = field(default_factory=set)
    score:         int             = 0
    seed:          int             = 0
    status:        str             = "Welcome!"
    show_help:     bool            = False
    paused:        bool            = False


def _spawn_boss_if_goal(game: Game) -> None:
    game.boss = None
    game.portal_active = False
    if game.coord == GOAL_COORD:
        if game.boss_defeated:
            game.portal_active = True
        else:
            game.boss = Boss(x=GRID_W // 2, y=4)


def new_game(seed: int | None = None) -> Game:
    seed  = seed if seed is not None else random.randint(1, 10_000_000)
    world = generate_world(seed)
    game  = Game(world=world, seed=seed)
    _spawn_boss_if_goal(game)
    return game


def enter_area(game: Game, coord: tuple[int, int], enter_from: str) -> None:
    game.coord = coord
    game.visited.add(coord)
    if enter_from == "right":
        game.player.x, game.player.y = GRID_W - 2, 2
    elif enter_from == "left":
        game.player.x, game.player.y = 1, 2
    elif enter_from == "down":
        game.player.x, game.player.y = GRID_W // 2, GRID_H - 2
    elif enter_from == "up":
        game.player.x, game.player.y = GRID_W // 2, 1
    game.player.vy = 0
    game.player.bullets.clear()
    area = game.world[coord]
    for it in area.items:
        uid_key = (tuple(it["uid"][0]), it["uid"][1])
        if uid_key in game.collected:
            it["alive"] = False
    _spawn_boss_if_goal(game)


def try_transition(game: Game) -> None:
    x, y = game.player.x, game.player.y
    cx, cy = game.coord
    direction = None
    if x < 0:         direction = "left"
    elif x >= GRID_W: direction = "right"
    elif y < 0:       direction = "up"
    elif y >= GRID_H: direction = "down"
    if direction is None:
        return
    deltas   = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
    opposite = {"left": "right", "right": "left", "up": "down", "down": "up"}
    dx, dy   = deltas[direction]
    new_coord = (cx + dx, cy + dy)
    if not (0 <= new_coord[0] < 3 and 0 <= new_coord[1] < 3):
        game.player.x = max(0, min(GRID_W - 1, x))
        game.player.y = max(0, min(GRID_H - 1, y))
        return
    enter_area(game, new_coord, opposite[direction])


# --- Tick ---------------------------------------------------------------------

def tick(game: Game) -> None:
    if game.paused or not game.player.alive:
        return
    area = game.world[game.coord]

    apply_gravity(area, game.player)

    new_bullets = []
    for (bx, by, bd) in game.player.bullets:
        nx = bx + bd
        if 0 <= nx < GRID_W:
            hit = False
            for e in area.enemies:
                if e["alive"] and e["x"] == nx and e["y"] == by:
                    e["alive"] = False
                    game.score += 5
                    hit = True
                    break
            if game.boss and game.boss.alive and \
               game.boss.x - 1 <= nx <= game.boss.x + 1 and \
               game.boss.y - 1 <= by <= game.boss.y + 1:
                if game.boss.take_damage(1):
                    game.score += 10
                hit = True
            if not hit:
                new_bullets.append((nx, by, bd))
    game.player.bullets = new_bullets

    for e in area.enemies:
        move_enemy(area, e, game.player)
        if e["alive"] and e["x"] == game.player.x and e["y"] == game.player.y:
            if game.player.iframes == 0:
                game.player.hp -= 1
                game.player.iframes = 12

    if game.boss and game.boss.alive:
        speed = 2 if game.boss.phase == "RAGE" else 1
        for _ in range(speed):
            if game.player.x > game.boss.x:
                game.boss.x = min(GRID_W - 1, game.boss.x + 1)
            elif game.player.x < game.boss.x:
                game.boss.x = max(0, game.boss.x - 1)
        if not is_platform_at(area, game.boss.x, game.boss.y + 1):
            game.boss.y = min(GRID_H - 1, game.boss.y + 1)
        if abs(game.boss.x - game.player.x) <= 1 and \
           abs(game.boss.y - game.player.y) <= 1:
            if game.player.iframes == 0:
                game.player.hp -= 1
                game.player.iframes = 14
        if game.boss.iframes > 0:
            game.boss.iframes -= 1
    elif game.boss and not game.boss.alive:
        game.score += 100
        game.boss_defeated = True
        _spawn_boss_if_goal(game)
        game.status = "Boss defeated! Reach the altar."

    if game.portal_active:
        for d in area.decor:
            if d["kind"] == "altar" and d["x"] == game.player.x and \
               d["y"] >= game.player.y - 1:
                game.status = "VICTORY"

    for it in area.items:
        if not it["alive"]:
            continue
        if it["x"] == game.player.x and it["y"] == game.player.y:
            it["alive"] = False
            game.player.inventory[it["kind"]] = \
                game.player.inventory.get(it["kind"], 0) + 1
            game.collected.add((tuple(it["uid"][0]), it["uid"][1]))
            game.score += 2
            game.status = f"Picked up {it['kind']}"

    if game.player.iframes    > 0: game.player.iframes    -= 1
    if game.player.speed_left > 0: game.player.speed_left -= 1
    if game.player.jump_left  > 0: game.player.jump_left  -= 1

    try_transition(game)


# --- Actions ------------------------------------------------------------------

def move_player(game: Game, dx: int) -> None:
    game.player.facing = 1 if dx > 0 else -1
    steps = 2 if game.player.speed_left > 0 else 1
    for _ in range(steps):
        game.player.x += dx
        try_transition(game)


def jump(game: Game) -> None:
    area = game.world[game.coord]
    if on_ground(area, game.player):
        boost = -1 if game.player.jump_left > 0 else 0
        game.player.vy = JUMP_VEL + boost
        game.player.y -= 1


def shoot(game: Game) -> None:
    bx = game.player.x + game.player.facing
    game.player.bullets.append((bx, game.player.y, game.player.facing))


def use_item(game: Game, kind: str) -> None:
    inv = game.player.inventory
    if inv.get(kind, 0) <= 0:
        game.status = f"No {kind} in inventory."
        return
    if kind == "potion":
        if game.player.hp >= MAX_HP:
            game.status = "HP full."
            return
        game.player.hp += 1
        inv[kind] -= 1
        game.status = "Healed."
    elif kind == "speed":
        game.player.speed_left = BOOST_TICKS
        inv[kind] -= 1
        game.status = "Speed boost!"
    elif kind == "jump":
        game.player.jump_left = BOOST_TICKS
        inv[kind] -= 1
        game.status = "Jump boost!"
