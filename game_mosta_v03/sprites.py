"""Sprite loading and decorative shape drawing.

Python features demonstrated:
- ``pathlib.Path`` for filesystem paths (OS-agnostic)
- Decorator-based registry (``@register("tree")``) to map names to drawers
- ``Callable`` type hint for the registry's value type
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pygame

from constants import BLACK, TREE_TRUNK, TREE_LEAVES

SPRITES: dict[str, pygame.Surface] = {}

DecorDrawer = Callable[[pygame.Surface, int, int], None]
_DECOR_REGISTRY: dict[str, DecorDrawer] = {}


def register(name: str) -> Callable[[DecorDrawer], DecorDrawer]:
    """Decorator factory: register a function under a string key."""
    def _decorate(fn: DecorDrawer) -> DecorDrawer:
        _DECOR_REGISTRY[name] = fn
        return fn
    return _decorate


def load_sprites(player_w: int, player_h: int, enemy_w: int, enemy_h: int) -> None:
    path = Path(__file__).resolve().parent / "mosta.png"
    raw  = pygame.image.load(str(path)).convert_alpha()
    raw.set_colorkey(raw.get_at((0, 0))[:3])

    SPRITES["player"] = pygame.transform.scale(raw, (player_w, player_h))

    enemy_img = pygame.transform.scale(raw, (enemy_w, enemy_h)).copy()
    tint = pygame.Surface((enemy_w, enemy_h), pygame.SRCALPHA)
    tint.fill((255, 60, 60, 255))
    enemy_img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    SPRITES["enemy"] = enemy_img


def draw_monster(surface: pygame.Surface, rect: pygame.Rect,
                 color: tuple, frame: int = 0) -> None:
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    pygame.draw.rect(surface, color, (x, y + h // 4, w, h // 2))
    eye_size = max(3, w // 8)
    eye_y    = y + h // 4 + 3
    pygame.draw.rect(surface, BLACK, (x + w // 4 - eye_size // 2,     eye_y, eye_size, eye_size))
    pygame.draw.rect(surface, BLACK, (x + 3 * w // 4 - eye_size // 2, eye_y, eye_size, eye_size))
    leg_w   = max(3, w // 10)
    leg_h   = h // 5
    leg_y   = y + h // 4 + h // 2
    offsets = [0, leg_h // 2, 0, leg_h // 2] if frame % 2 == 0 else [leg_h // 2, 0, leg_h // 2, 0]
    for i in range(4):
        leg_x = x + (i + 1) * w // 5 - leg_w // 2
        pygame.draw.rect(surface, BLACK, (leg_x, leg_y + offsets[i], leg_w, leg_h - offsets[i]))


@register("tree")
def _draw_tree(surface: pygame.Surface, x: int, y: int) -> None:
    trunk = pygame.Rect(x - 12, y - 90, 24, 90)
    pygame.draw.rect(surface, TREE_TRUNK, trunk)
    for cx, cy, r in ((x, y - 110, 40), (x - 30, y - 90, 32),
                      (x + 30, y - 90, 32), (x, y - 140, 30)):
        pygame.draw.circle(surface, TREE_LEAVES, (cx, cy), r)


@register("altar")
def _draw_altar(surface: pygame.Surface, x: int, y: int) -> None:
    base = pygame.Rect(x - 40, y - 10, 80, 10)
    pygame.draw.rect(surface, (180, 180, 190), base)
    pygame.draw.rect(surface, (230, 230, 240), base, 2)
    for cx in (x - 28, x + 28):
        pygame.draw.circle(surface, (255, 220, 100), (cx, y - 16), 5)


@register("sign")
def _draw_sign(surface: pygame.Surface, x: int, y: int) -> None:
    post  = pygame.Rect(x - 3, y - 40, 6, 40)
    board = pygame.Rect(x - 26, y - 55, 52, 22)
    pygame.draw.rect(surface, TREE_TRUNK, post)
    pygame.draw.rect(surface, (200, 170, 120), board)
    pygame.draw.rect(surface, (90, 60, 30), board, 2)
    font  = pygame.font.SysFont("monospace", 11, bold=True)
    label = font.render("HOME", True, (60, 40, 20))
    surface.blit(label, (board.centerx - label.get_width() // 2,
                         board.centery - label.get_height() // 2))


# Legacy export kept for tests/callers that use the dict directly.
DECOR_DRAWERS = _DECOR_REGISTRY


def draw_decor(surface: pygame.Surface, decor: list) -> None:
    for kind, x, y in decor:
        if drawer := _DECOR_REGISTRY.get(kind):
            drawer(surface, x, y)
