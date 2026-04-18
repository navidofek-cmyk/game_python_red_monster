"""Main game loop.

Python features demonstrated:
- ``contextlib.contextmanager`` for pygame setup/teardown
- ``@dataclass`` with ``field(default_factory=...)`` for mutable defaults
- ``match``/``case`` for event and state dispatch
- Function decomposition: each state has its own tick function
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

import pygame

from constants import (
    SCREEN_W, SCREEN_H, FPS, FPS as _FPS,
    GameState, PLAYING, GAMEOVER, VICTORY, WELCOME,
    ItemKind, ITEM_HOTKEYS,
)
from sprites  import load_sprites, draw_decor
from entities import Platform, Portal, Player, Enemy
from items    import Item
from world    import (
    AREAS, START_COORD, GOAL_COORD, Direction,
    neighbor, edge_direction, spawn_area,
)
from hud import (
    draw_hud, draw_welcome, draw_area_banner,
    draw_game_over, draw_victory, draw_minimap,
    draw_hp, draw_inventory,
)

AREA_BANNER_FRAMES = int(_FPS * 1.5)

ITEM_HOTKEY_MAP: dict[int, ItemKind] = {
    pygame.K_1: ITEM_HOTKEYS[0],
    pygame.K_2: ITEM_HOTKEYS[1],
    pygame.K_3: ITEM_HOTKEYS[2],
    pygame.K_4: ITEM_HOTKEYS[3],
}


@dataclass
class GameWorld:
    coord:      tuple[int, int]
    player:     Player
    platforms:  list           = field(default_factory=list)
    enemies:    list           = field(default_factory=list)
    bg_color:   tuple          = (0, 0, 0)
    decor:      list           = field(default_factory=list)
    items:      list           = field(default_factory=list)
    portal:     Portal | None  = None
    visited:    set            = field(default_factory=set)
    collected:  set            = field(default_factory=set)
    score:      int            = 0
    area_timer: int            = AREA_BANNER_FRAMES

    def allow_edges(self) -> dict[str, bool]:
        return {d.value: neighbor(self.coord, d) is not None for d in Direction}


def _load_area(coord, player=None, entry_from=None, collected=None):
    platforms, enemies, bg_color, decor, items = spawn_area(
        coord, Platform, Enemy, Item,
        entry_from=entry_from, player=player, collected=collected)
    portal = None
    if coord == GOAL_COORD:
        for kind, dx, dy in decor:
            if kind == "altar":
                portal = Portal(dx, dy)
                break
    return platforms, enemies, bg_color, decor, items, portal


def new_world() -> GameWorld:
    player = Player(80, SCREEN_H - 100)
    plats, enemies, bg, decor, items, portal = _load_area(START_COORD, collected=set())
    return GameWorld(
        coord=START_COORD, player=player,
        platforms=plats, enemies=enemies, bg_color=bg,
        decor=decor, items=items, portal=portal,
        visited={START_COORD}, collected=set(),
    )


def transition(gw: GameWorld, direction: str) -> None:
    new_coord = neighbor(gw.coord, direction)
    if new_coord is None:
        return
    entry_from = Direction(direction).opposite.value
    plats, enemies, bg, decor, items, portal = _load_area(
        new_coord, player=gw.player, entry_from=entry_from, collected=gw.collected)
    gw.coord      = new_coord
    gw.platforms  = plats
    gw.enemies    = enemies
    gw.bg_color   = bg
    gw.decor      = decor
    gw.items      = items
    gw.portal     = portal
    gw.visited.add(new_coord)
    gw.area_timer = AREA_BANNER_FRAMES


@contextmanager
def pygame_session(title: str, size: tuple[int, int]) -> Iterator[pygame.Surface]:
    """Context manager: guarantees pygame.quit() on exit."""
    pygame.init()
    try:
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption(title)
        yield screen
    finally:
        pygame.quit()


def _pickup_items(gw: GameWorld) -> None:
    for it in gw.items:
        if it.alive and gw.player.rect.colliderect(it.rect):
            it.alive = False
            gw.player.inventory.add(it.kind)
            gw.collected.add(it.uid)
            gw.score += 2
    gw.items = [it for it in gw.items if it.alive]


def _tick_playing(gw: GameWorld) -> GameState | None:
    gw.player.update(gw.platforms, gw.allow_edges())

    if (direction := edge_direction(gw.player.rect)) and gw.allow_edges().get(direction):
        transition(gw, direction)

    _pickup_items(gw)

    for enemy in gw.enemies:
        enemy.update(gw.player, gw.platforms)
        for bullet in gw.player.projectiles[:]:
            if enemy.alive and bullet.rect.colliderect(enemy.rect):
                enemy.alive = False
                gw.player.projectiles.remove(bullet)
                gw.score += 5
        if enemy.alive and gw.player.rect.colliderect(enemy.rect):
            gw.player.take_damage(1)
            if not gw.player.alive:
                return GAMEOVER

    if gw.portal is not None:
        gw.portal.update()
        if gw.player.rect.colliderect(gw.portal.rect):
            gw.score += 50
            return VICTORY

    if gw.area_timer > 0:
        gw.area_timer -= 1
    return None


def _handle_key(event, state: GameState, gw: GameWorld) -> tuple[GameState, GameWorld]:
    match state:
        case GameState.WELCOME:
            return GameState.PLAYING, gw
        case GameState.PLAYING:
            if event.key in (pygame.K_UP, pygame.K_w):
                gw.player.jump()
            elif event.key == pygame.K_f:
                gw.player.shoot()
            elif (kind := ITEM_HOTKEY_MAP.get(event.key)) is not None:
                gw.player.use_item(kind)
            return state, gw
        case GameState.GAMEOVER | GameState.VICTORY:
            if event.key == pygame.K_r:
                return GameState.PLAYING, new_world()
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            return state, gw
    return state, gw


def _render(screen, gw: GameWorld, state: GameState,
            big_font, small_font, tiny_font) -> None:
    screen.fill(gw.bg_color)
    for plat in gw.platforms:
        plat.draw(screen)
    draw_decor(screen, gw.decor)
    for it in gw.items:
        it.draw(screen)
    if gw.portal is not None:
        gw.portal.draw(screen)

    if state != GameState.WELCOME:
        for enemy in gw.enemies:
            enemy.draw(screen)
        gw.player.draw(screen)
        draw_hud(screen, small_font, gw.score, AREAS[gw.coord].name)
        draw_hp(screen, small_font, gw.player.hp)
        draw_inventory(screen, tiny_font, gw.player.inventory, gw.player)
        draw_minimap(screen, tiny_font, gw.coord, gw.visited)
        if gw.area_timer > 0 and state == GameState.PLAYING:
            draw_area_banner(screen, small_font,
                             AREAS[gw.coord].name, gw.area_timer)

    match state:
        case GameState.WELCOME:
            for enemy in gw.enemies:
                enemy.draw(screen)
            gw.player.draw(screen)
            draw_welcome(screen, big_font, small_font)
        case GameState.GAMEOVER:
            draw_game_over(screen, big_font, small_font,
                           gw.score, AREAS[gw.coord].name)
        case GameState.VICTORY:
            draw_victory(screen, big_font, small_font, gw.score)


def main() -> None:
    with pygame_session("Red Monster – Journey of Mosta", (SCREEN_W, SCREEN_H)) as screen:
        clock = pygame.time.Clock()
        load_sprites(Player.W, Player.H, Enemy.W, Enemy.H)

        big_font   = pygame.font.SysFont("monospace", 44, bold=True)
        small_font = pygame.font.SysFont("monospace", 20)
        tiny_font  = pygame.font.SysFont("monospace", 14, bold=True)

        gw    = new_world()
        state = GameState.WELCOME

        while True:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    state, gw = _handle_key(event, state, gw)

            if state == GameState.PLAYING:
                if (next_state := _tick_playing(gw)) is not None:
                    state = next_state

            _render(screen, gw, state, big_font, small_font, tiny_font)
            pygame.display.flip()


if __name__ == "__main__":
    main()
