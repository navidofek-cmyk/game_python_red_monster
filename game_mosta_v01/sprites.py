import os
import pygame
from constants import BLACK, PLAYER_COLOR, ENEMY_COLOR

SPRITES: dict = {}


def load_sprites(player_w: int, player_h: int, enemy_w: int, enemy_h: int) -> None:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mosta.png")
    raw  = pygame.image.load(path).convert_alpha()
    raw.set_colorkey(raw.get_at((0, 0))[:3])

    SPRITES["player"] = pygame.transform.scale(raw, (player_w, player_h))

    enemy_img = pygame.transform.scale(raw, (enemy_w, enemy_h)).copy()
    tint = pygame.Surface((enemy_w, enemy_h), pygame.SRCALPHA)
    tint.fill((255, 60, 60, 255))
    enemy_img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    SPRITES["enemy"] = enemy_img


def draw_monster(surface: pygame.Surface, rect: pygame.Rect,
                 color: tuple, frame: int = 0) -> None:
    """Fallback rectangle monster when sprite is unavailable."""
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
