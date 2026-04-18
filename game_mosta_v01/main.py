import pygame
import sys

from constants import (
    SCREEN_W, SCREEN_H, FPS, BANNER_FRAMES,
    WELCOME, BANNER, PLAYING, GAMEOVER, VICTORY,
)
from sprites  import load_sprites
from entities import Platform, Portal, Player, Enemy
from levels   import LEVEL_DEFS, spawn_level
from hud      import draw_hud, draw_welcome, draw_level_banner, draw_game_over, draw_victory


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Red Monster – Platform Shooter")
    clock = pygame.time.Clock()

    load_sprites(Player.W, Player.H, Enemy.W, Enemy.H)
    big_font   = pygame.font.SysFont("monospace", 44, bold=True)
    small_font = pygame.font.SysFont("monospace", 20)

    level_idx     = 0
    score         = 0
    portal_active = False
    banner_timer  = 0
    platforms, player, enemies, portal, bg_color = spawn_level(
        level_idx, Platform, Player, Enemy, Portal)
    state = WELCOME

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if state == WELCOME:
                    state        = BANNER
                    banner_timer = BANNER_FRAMES

                elif state == PLAYING:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        player.jump()
                    if event.key == pygame.K_f:
                        player.shoot()

                elif state in (GAMEOVER, VICTORY):
                    if event.key == pygame.K_r:
                        level_idx     = 0
                        score         = 0
                        portal_active = False
                        platforms, player, enemies, portal, bg_color = spawn_level(
                            level_idx, Platform, Player, Enemy, Portal)
                        state        = BANNER
                        banner_timer = BANNER_FRAMES
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

        if state == BANNER:
            banner_timer -= 1
            if banner_timer <= 0:
                state = PLAYING

        elif state == PLAYING:
            player.update(platforms)

            if not portal_active and not any(e.alive for e in enemies):
                portal_active = True

            if portal_active:
                portal.update()
                if player.rect.colliderect(portal.rect):
                    score     += 20
                    level_idx += 1
                    if level_idx >= len(LEVEL_DEFS):
                        state = VICTORY
                    else:
                        portal_active = False
                        platforms, player, enemies, portal, bg_color = spawn_level(
                            level_idx, Platform, Player, Enemy, Portal)
                        state        = BANNER
                        banner_timer = BANNER_FRAMES

            for enemy in enemies:
                enemy.update(player, platforms)
                for bullet in player.projectiles[:]:
                    if enemy.alive and bullet.rect.colliderect(enemy.rect):
                        enemy.alive = False
                        player.projectiles.remove(bullet)
                        score += 1
                if enemy.alive and player.rect.colliderect(enemy.rect):
                    state = GAMEOVER

        screen.fill(bg_color)
        for plat in platforms:
            plat.draw(screen)

        if portal_active and state in (PLAYING, BANNER):
            portal.draw(screen)

        if state != WELCOME:
            for enemy in enemies:
                enemy.draw(screen)
            player.draw(screen)
            draw_hud(screen, small_font, score, level_idx + 1)

        if state == WELCOME:
            for enemy in enemies:
                enemy.draw(screen)
            player.draw(screen)
            draw_welcome(screen, big_font, small_font)
        elif state == BANNER:
            draw_level_banner(screen, big_font, small_font, level_idx + 1)
        elif state == GAMEOVER:
            draw_game_over(screen, big_font, small_font, score, level_idx + 1)
        elif state == VICTORY:
            draw_victory(screen, big_font, small_font, score)

        pygame.display.flip()


if __name__ == "__main__":
    main()
