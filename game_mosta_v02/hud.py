import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    PLAYER_COLOR, ENEMY_COLOR, PORTAL_COLOR,
    TEXT_COLOR, HINT_COLOR, DIM_COLOR, BLACK,
)
from sprites import SPRITES, draw_monster
from world   import AREAS, GRID_W, GRID_H, GOAL_COORD


def _draw_overlay(surface: pygame.Surface, alpha: int = 200) -> None:
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


def _blit_centered(surface: pygame.Surface, rendered: pygame.Surface, y: int) -> None:
    surface.blit(rendered, (SCREEN_W // 2 - rendered.get_width() // 2, y))


def _draw_end_screen(surface, big_font, small_font,
                     title, title_color, lines, alpha=200):
    _draw_overlay(surface, alpha)
    _blit_centered(surface, big_font.render(title, True, title_color), 200)
    for i, (text, color) in enumerate(lines):
        _blit_centered(surface, small_font.render(text, True, color), 280 + i * 50)


def draw_hud(surface: pygame.Surface, font: pygame.font.Font,
             score: int, area_name: str) -> None:
    surface.blit(font.render(f"Score: {score}", True, TEXT_COLOR), (10, 10))
    lbl = font.render(area_name, True, TEXT_COLOR)
    surface.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 10))
    hint = font.render("←→ move  ↑/W jump  F shoot", True, HINT_COLOR)
    surface.blit(hint, (SCREEN_W - hint.get_width() - 10, 10))


def draw_area_banner(surface, font, area_name: str, timer: int) -> None:
    alpha = min(255, timer * 4)
    rendered = font.render(f"Entering: {area_name}", True, TEXT_COLOR)
    banner = pygame.Surface((rendered.get_width() + 24, rendered.get_height() + 12),
                            pygame.SRCALPHA)
    banner.fill((0, 0, 0, min(160, alpha)))
    banner.blit(rendered, (12, 6))
    banner.set_alpha(alpha)
    surface.blit(banner, (SCREEN_W // 2 - banner.get_width() // 2, 44))


def draw_minimap(surface, font, current, visited: set) -> None:
    cell = 22
    pad  = 6
    w    = GRID_W * cell + 2 * pad
    h    = GRID_H * cell + 2 * pad
    x0   = SCREEN_W - w - 10
    y0   = SCREEN_H - h - 10

    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    surface.blit(bg, (x0, y0))

    for (cx, cy), defn in AREAS.items():
        rx = x0 + pad + cx * cell
        ry = y0 + pad + cy * cell
        if (cx, cy) == current:
            color = PLAYER_COLOR
        elif (cx, cy) == GOAL_COORD:
            color = PORTAL_COLOR
        elif (cx, cy) in visited:
            color = (140, 140, 160)
        else:
            color = (60, 60, 75)
        pygame.draw.rect(surface, color, (rx + 1, ry + 1, cell - 2, cell - 2))


def draw_welcome(surface, big_font, small_font):
    _draw_overlay(surface, 200)
    _blit_centered(surface, big_font.render("Journey of Mosta", True, PLAYER_COLOR), 130)
    _blit_centered(surface, small_font.render(
        "Your peaceful meadow is lost in shadow. Climb through swamp,", True, TEXT_COLOR), 220)
    _blit_centered(surface, small_font.render(
        "forest, caves and mountains to reach the Volcano Altar.", True, TEXT_COLOR), 250)
    _blit_centered(surface, small_font.render(
        "Beware the red monsters — they patrol, chase and jump.", True, DIM_COLOR), 290)
    _blit_centered(surface, small_font.render(
        "←→ move   ↑/W jump   F shoot   Press any key to begin", True, HINT_COLOR), 350)
    preview = pygame.Rect(SCREEN_W // 2 - 20, 400, 40, 30)
    img = SPRITES.get("player")
    if img:
        surface.blit(img, preview)
    else:
        draw_monster(surface, preview, PLAYER_COLOR)


def draw_game_over(surface, big_font, small_font, score, area_name):
    _draw_end_screen(surface, big_font, small_font,
                     "GAME OVER", ENEMY_COLOR,
                     [(f"Score: {score}   |   Fell in: {area_name}", TEXT_COLOR),
                      ("R = restart   |   ESC = quit",               DIM_COLOR)])


def draw_victory(surface, big_font, small_font, score):
    _draw_end_screen(surface, big_font, small_font,
                     "YOU REACHED THE ALTAR!", PORTAL_COLOR,
                     [(f"Final score: {score}",            TEXT_COLOR),
                      ("R = play again   |   ESC = quit", DIM_COLOR)])
