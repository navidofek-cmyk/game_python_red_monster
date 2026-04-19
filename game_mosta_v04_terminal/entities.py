"""Player, Boss, physics helpers, enemy AI."""
from __future__ import annotations

from dataclasses import dataclass, field

from constants import BOSS_HP, GRID_H, GRID_W, MAX_HP
from world import Area


@dataclass
class Player:
    x:          int  = 5
    y:          int  = GRID_H - 2
    vy:         int  = 0
    hp:         int  = MAX_HP
    facing:     int  = 1
    iframes:    int  = 0
    speed_left: int  = 0
    jump_left:  int  = 0
    inventory:  dict = field(default_factory=lambda: {"potion": 0, "speed": 0, "jump": 0})
    bullets:    list = field(default_factory=list)  # [(x, y, dx)]

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass
class Boss:
    x:       int
    y:       int
    hp:      int = BOSS_HP
    max_hp:  int = BOSS_HP
    iframes: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def phase(self) -> str:
        if self.hp <= 2: return "RAGE"
        if self.hp <= 4: return "HUNT"
        return "CALM"

    def take_damage(self, n: int = 1) -> bool:
        if self.iframes > 0 or not self.alive:
            return False
        self.hp      = max(0, self.hp - n)
        self.iframes = 4
        return True


# --- Physics ------------------------------------------------------------------

def is_platform_at(area: Area, x: int, y: int) -> bool:
    for (px, py, pw) in area.platforms:
        if py == y and px <= x < px + pw:
            return True
    return False


def platform_top_at(area: Area, x: int, y: int) -> int | None:
    best: int | None = None
    for (px, py, pw) in area.platforms:
        if px <= x < px + pw and py >= y and (best is None or py < best):
            best = py
    return best


def apply_gravity(area: Area, player: Player) -> None:
    player.vy += 1
    step = 1 if player.vy > 0 else -1
    for _ in range(abs(player.vy)):
        nxt = player.y + step
        if step > 0 and is_platform_at(area, player.x, nxt):
            player.vy = 0
            return
        if nxt < 0:
            player.vy = 0
            return
        if nxt >= GRID_H:
            player.y = GRID_H - 1
            player.vy = 0
            return
        player.y = nxt
    if is_platform_at(area, player.x, player.y + 1):
        player.vy = 0


def on_ground(area: Area, player: Player) -> bool:
    return is_platform_at(area, player.x, player.y + 1)


# --- Enemy AI -----------------------------------------------------------------

def move_enemy(area: Area, enemy: dict, player: Player) -> None:
    if not enemy["alive"]:
        return
    ai = enemy["ai"]
    ex, ey = enemy["x"], enemy["y"]

    if not is_platform_at(area, ex, ey + 1) and ey + 1 < GRID_H:
        enemy["y"] = ey + 1
        return

    def has_ground(nx: int) -> bool:
        return is_platform_at(area, nx, ey + 1) or ey + 1 >= GRID_H

    def blocked(nx: int) -> bool:
        return is_platform_at(area, nx, ey)

    if ai == "patrol":
        direction = enemy.get("dir", 1)
        next_x = ex + direction
        if not has_ground(next_x) or blocked(next_x) or not (0 <= next_x < GRID_W):
            direction = -direction
            next_x = ex + direction
        enemy["dir"] = direction
        enemy["x"] = max(0, min(GRID_W - 1, next_x))

    elif ai == "chase":
        if abs(player.x - ex) < 30 and abs(player.y - ey) < 8:
            direction = 1 if player.x > ex else -1
            next_x = ex + direction
            if has_ground(next_x) and not blocked(next_x) and 0 <= next_x < GRID_W:
                enemy["x"] = next_x

    elif ai == "jumper":
        if abs(player.x - ex) < 25:
            direction = 1 if player.x > ex else -1
            next_x = ex + direction
            if not blocked(next_x) and 0 <= next_x < GRID_W:
                enemy["x"] = next_x
