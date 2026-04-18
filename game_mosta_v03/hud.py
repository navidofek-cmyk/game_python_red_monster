import pygame
from constants import (
    SCREEN_W, SCREEN_H, MAX_HP,
    PLAYER_COLOR, ENEMY_COLOR, PORTAL_COLOR,
    TEXT_COLOR, HINT_COLOR, DIM_COLOR, BLACK,
    ItemKind, ITEM_HOTKEYS,
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


def _heart_shape(surface, cx, cy, r, color):
    pygame.draw.circle(surface, color, (cx - r // 2, cy - r // 4), r // 2)
    pygame.draw.circle(surface, color, (cx + r // 2, cy - r // 4), r // 2)
    pygame.draw.polygon(surface, color, [
        (cx - r, cy - r // 8), (cx + r, cy - r // 8), (cx, cy + r)
    ])


def draw_hp(surface, font, hp: int) -> None:
    x0, y0 = 10, 40
    for i in range(MAX_HP):
        color = (220, 40, 60) if i < hp else (70, 30, 40)
        _heart_shape(surface, x0 + 18 + i * 26, y0 + 10, 9, color)


_ITEM_ICON_COLORS: dict[ItemKind, tuple] = {
    ItemKind.POTION: (220, 60,  90),
    ItemKind.SPEED:  (80,  200, 255),
    ItemKind.JUMP:   (255, 210, 80),
    ItemKind.KEY:    (240, 230, 130),
}


def draw_inventory(surface, font, inventory, player) -> None:
    x0, y0 = 10, 70
    cell = 28
    for i, kind in enumerate(ITEM_HOTKEYS):
        cx = x0 + i * (cell + 4)
        rect = pygame.Rect(cx, y0, cell, cell)
        pygame.draw.rect(surface, (30, 30, 40), rect, border_radius=4)
        pygame.draw.rect(surface, _ITEM_ICON_COLORS[kind], rect.inflate(-6, -6),
                         border_radius=3)
        count = inventory.count(kind)
        label = font.render(f"{i+1}:{count}", True, TEXT_COLOR)
        surface.blit(label, (cx + 2, y0 + cell + 1))

    # Active boost indicators
    info_y = y0 + cell + 18
    if player.speed_boost_frames > 0:
        surface.blit(font.render(f"SPEED {player.speed_boost_frames // 60 + 1}s",
                                 True, (80, 200, 255)), (x0, info_y))
        info_y += 16
    if player.jump_boost_frames > 0:
        surface.blit(font.render(f"JUMP {player.jump_boost_frames // 60 + 1}s",
                                 True, (255, 210, 80)), (x0, info_y))


def draw_welcome(surface, big_font, small_font):
    _draw_overlay(surface, 200)
    _blit_centered(surface, big_font.render("Journey of Mosta", True, PLAYER_COLOR), 110)
    _blit_centered(surface, small_font.render(
        "Your peaceful meadow is lost in shadow. Climb through swamp,", True, TEXT_COLOR), 200)
    _blit_centered(surface, small_font.render(
        "forest, caves and mountains to reach the Volcano Altar.", True, TEXT_COLOR), 230)
    _blit_centered(surface, small_font.render(
        "Beware the red monsters — they patrol, chase and jump.", True, DIM_COLOR), 270)
    _blit_centered(surface, small_font.render(
        "You have 3 HP — pick up potions to heal.", True, DIM_COLOR), 300)
    _blit_centered(surface, small_font.render(
        "←→ move   ↑/W jump   F shoot   1=potion  2=speed  3=jump", True, HINT_COLOR), 350)
    _blit_centered(surface, small_font.render(
        "Press any key to begin", True, HINT_COLOR), 380)
    preview = pygame.Rect(SCREEN_W // 2 - 20, 420, 40, 30)
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
