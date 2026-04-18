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
from entities import Platform, Portal, Player, Enemy, Boss
from items    import Item
from world    import (
    AREAS, START_COORD, GOAL_COORD, Direction,
    neighbor, edge_direction, spawn_area,
)
from hud import (
    draw_hud, draw_welcome, draw_area_banner,
    draw_game_over, draw_victory, draw_minimap,
    draw_hp, draw_inventory, draw_save_toast,
    draw_boss_hp, draw_help_overlay,
)
from save import (
    has_save, save_game, load_game, apply_save, delete_save,
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
    boss:       Boss | None    = None
    boss_defeated: bool        = False
    visited:    set            = field(default_factory=set)
    collected:  set            = field(default_factory=set)
    score:      int            = 0
    area_timer: int            = AREA_BANNER_FRAMES
    save_toast: int            = 0
    show_help:  bool           = False

    def allow_edges(self) -> dict[str, bool]:
        return {d.value: neighbor(self.coord, d) is not None for d in Direction}


def _load_area(coord, player=None, entry_from=None, collected=None,
               boss_defeated: bool = False):
    platforms, enemies, bg_color, decor, items = spawn_area(
        coord, Platform, Enemy, Item,
        entry_from=entry_from, player=player, collected=collected)
    portal = None
    boss   = None
    if coord == GOAL_COORD:
        for kind, dx, dy in decor:
            if kind == "altar":
                if boss_defeated:
                    portal = Portal(dx, dy)
                else:
                    boss = Boss(dx, dy)
                break
    return platforms, enemies, bg_color, decor, items, portal, boss


def new_world() -> GameWorld:
    player = Player(80, SCREEN_H - 100)
    plats, enemies, bg, decor, items, portal, boss = _load_area(
        START_COORD, collected=set())
    return GameWorld(
        coord=START_COORD, player=player,
        platforms=plats, enemies=enemies, bg_color=bg,
        decor=decor, items=items, portal=portal, boss=boss,
        visited={START_COORD}, collected=set(),
    )


def _refresh_area(gw: GameWorld, boss_defeated: bool = False) -> None:
    """Re-spawn the current area (used after loading a save)."""
    plats, enemies, bg, decor, items, portal, boss = _load_area(
        gw.coord, collected=gw.collected, boss_defeated=boss_defeated)
    gw.platforms = plats
    gw.enemies   = enemies
    gw.bg_color  = bg
    gw.decor     = decor
    gw.items     = items
    gw.portal    = portal
    gw.boss      = boss
    gw.area_timer = AREA_BANNER_FRAMES


def load_saved_world() -> GameWorld | None:
    """Try to build a GameWorld from a save file. Returns None if no save."""
    data = load_game()
    if data is None:
        return None
    gw = new_world()
    apply_save(data, gw)
    _refresh_area(gw, boss_defeated=gw.boss_defeated)
    return gw


def transition(gw: GameWorld, direction: str) -> None:
    new_coord = neighbor(gw.coord, direction)
    if new_coord is None:
        return
    entry_from = Direction(direction).opposite.value
    plats, enemies, bg, decor, items, portal, boss = _load_area(
        new_coord, player=gw.player, entry_from=entry_from,
        collected=gw.collected, boss_defeated=gw.boss_defeated)
    gw.coord      = new_coord
    gw.platforms  = plats
    gw.enemies    = enemies
    gw.bg_color   = bg
    gw.decor      = decor
    gw.items      = items
    gw.portal     = portal
    gw.boss       = boss
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

    if gw.boss is not None:
        gw.boss.update(gw.player, gw.platforms)
        for bullet in gw.player.projectiles[:]:
            if gw.boss.alive and bullet.rect.colliderect(gw.boss.rect):
                gw.player.projectiles.remove(bullet)
                if gw.boss.take_damage(1):
                    gw.score += 10
        if gw.boss.alive and gw.player.rect.colliderect(gw.boss.rect):
            gw.player.take_damage(1)
            if not gw.player.alive:
                return GAMEOVER
        if not gw.boss.alive:
            gw.score += 100
            gw.boss_defeated = True
            _refresh_area(gw, boss_defeated=True)
            # Skip rest of tick; on next tick player can reach the portal.

    if gw.portal is not None:
        gw.portal.update()
        if gw.player.rect.colliderect(gw.portal.rect):
            gw.score += 50
            delete_save()
            return VICTORY

    if gw.area_timer > 0:
        gw.area_timer -= 1
    if gw.save_toast > 0:
        gw.save_toast -= 1
    return None


SAVE_TOAST_FRAMES = 90


def _handle_key(event, state: GameState, gw: GameWorld) -> tuple[GameState, GameWorld]:
    match state:
        case GameState.WELCOME:
            if event.key == pygame.K_c and (loaded := load_saved_world()) is not None:
                return GameState.PLAYING, loaded
            return GameState.PLAYING, gw
        case GameState.PLAYING:
            if event.key in (pygame.K_UP, pygame.K_w):
                gw.player.jump()
            elif event.key == pygame.K_f:
                gw.player.shoot()
            elif event.key == pygame.K_s:
                save_game(gw)
                gw.save_toast = SAVE_TOAST_FRAMES
            elif event.key == pygame.K_h:
                gw.show_help = not gw.show_help
            elif (kind := ITEM_HOTKEY_MAP.get(event.key)) is not None:
                gw.player.use_item(kind)
            return state, gw
        case GameState.GAMEOVER | GameState.VICTORY:
            if event.key == pygame.K_r:
                return GameState.PLAYING, new_world()
            if event.key == pygame.K_c and (loaded := load_saved_world()) is not None:
                return GameState.PLAYING, loaded
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
    if gw.boss is not None:
        gw.boss.draw(screen)

    if state != GameState.WELCOME:
        for enemy in gw.enemies:
            enemy.draw(screen)
        gw.player.draw(screen)
        draw_hud(screen, small_font, gw.score, AREAS[gw.coord].name)
        draw_hp(screen, small_font, gw.player.hp)
        draw_inventory(screen, tiny_font, gw.player.inventory, gw.player)
        draw_minimap(screen, tiny_font, gw.coord, gw.visited)
        if gw.boss is not None and gw.boss.alive:
            draw_boss_hp(screen, small_font, gw.boss)
        if gw.area_timer > 0 and state == GameState.PLAYING:
            draw_area_banner(screen, small_font,
                             AREAS[gw.coord].name, gw.area_timer)
        if gw.save_toast > 0:
            draw_save_toast(screen, small_font, gw.save_toast)
        if gw.show_help and state == GameState.PLAYING:
            draw_help_overlay(screen, small_font)

    match state:
        case GameState.WELCOME:
            for enemy in gw.enemies:
                enemy.draw(screen)
            gw.player.draw(screen)
            draw_welcome(screen, big_font, small_font, has_save=has_save())
        case GameState.GAMEOVER:
            draw_game_over(screen, big_font, small_font,
                           gw.score, AREAS[gw.coord].name, has_save=has_save())
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
