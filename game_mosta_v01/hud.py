import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    PLAYER_COLOR, ENEMY_COLOR, PORTAL_COLOR,
    TEXT_COLOR, HINT_COLOR, DIM_COLOR, BLACK,
)
from sprites import SPRITES, draw_monster


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
             score: int, level: int) -> None:
    surface.blit(font.render(f"Score: {score}", True, TEXT_COLOR), (10, 10))
    lbl = font.render(f"Level: {level}", True, TEXT_COLOR)
    surface.blit(lbl, (SCREEN_W // 2 - lbl.get_width() // 2, 10))
    hint = font.render("← → move   W/↑ jump   F shoot", True, HINT_COLOR)
    surface.blit(hint, (SCREEN_W - hint.get_width() - 10, 10))


def draw_welcome(surface, big_font, small_font):
    _draw_overlay(surface, 180)
    _blit_centered(surface, big_font.render("Welcome back, Ivan!", True, PLAYER_COLOR), 190)
    _blit_centered(surface, small_font.render(
        "arrow / WASD = move   W / ↑ = jump   F = shoot", True, TEXT_COLOR), 270)
    _blit_centered(surface, small_font.render(
        "Reach the EXIT portal to advance  |  Press any key to start", True, DIM_COLOR), 310)
    preview = pygame.Rect(SCREEN_W // 2 - 20, 370, 40, 30)
    img = SPRITES.get("player")
    if img:
        surface.blit(img, preview)
    else:
        draw_monster(surface, preview, PLAYER_COLOR)


def draw_level_banner(surface, big_font, small_font, level):
    _draw_end_screen(surface, big_font, small_font,
                     f"LEVEL  {level}", PORTAL_COLOR,
                     [("Kill all enemies, then reach the EXIT portal", TEXT_COLOR)],
                     alpha=160)


def draw_game_over(surface, big_font, small_font, score, level):
    _draw_end_screen(surface, big_font, small_font,
                     "GAME OVER", ENEMY_COLOR,
                     [(f"Score: {score}   |   Reached level {level}", TEXT_COLOR),
                      ("R = restart from level 1   |   ESC = quit",   DIM_COLOR)])


def draw_victory(surface, big_font, small_font, score):
    _draw_end_screen(surface, big_font, small_font,
                     "YOU WIN!", PORTAL_COLOR,
                     [(f"Final score: {score}",            TEXT_COLOR),
                      ("R = play again   |   ESC = quit", DIM_COLOR)])
