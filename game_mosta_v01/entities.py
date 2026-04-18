import pygame
from constants import (
    SCREEN_W, SCREEN_H, GRAVITY, JUMP_VEL, PLAYER_SPEED,
    BULLET_SPEED, SHOOT_COOLDOWN,
    PLATFORM_COLOR, PLATFORM_SHINE,
    BULLET_COLOR, BULLET_INNER,
    PLAYER_COLOR, ENEMY_COLOR, PORTAL_COLOR, PORTAL_INNER, BLACK,
)
from sprites import SPRITES, draw_monster


class PhysicsBody:
    """Shared gravity + platform collision for Player and Enemy."""

    def _apply_gravity(self, platforms: list) -> None:
        self.vel_y    += GRAVITY
        self.rect.y   += int(self.vel_y)
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel_y > 0:
                    self.rect.bottom = plat.rect.top
                    self.vel_y       = 0
                    self.on_ground   = True
                elif self.vel_y < 0:
                    self.rect.top = plat.rect.bottom
                    self.vel_y    = 1
        if self.rect.bottom >= SCREEN_H:
            self.rect.bottom = SCREEN_H
            self.vel_y       = 0
            self.on_ground   = True


class Platform:
    def __init__(self, x: int, y: int, w: int, h: int = 14) -> None:
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PLATFORM_COLOR, self.rect)
        pygame.draw.line(surface, PLATFORM_SHINE, self.rect.topleft, self.rect.topright, 2)


class Portal:
    W, H = 30, 50

    def __init__(self, x: int, y: int) -> None:
        self.rect  = pygame.Rect(x - self.W // 2, y - self.H, self.W, self.H)
        self.timer = 0
        self._font = pygame.font.SysFont("monospace", 11, bold=True)

    def update(self) -> None:
        self.timer += 1

    def draw(self, surface: pygame.Surface) -> None:
        pulse  = abs((self.timer % 60) - 30) / 30
        factor = 0.6 + 0.4 * pulse
        color  = tuple(int(c * factor) for c in PORTAL_COLOR)
        pygame.draw.rect(surface, color,        self.rect,                   border_radius=4)
        pygame.draw.rect(surface, PORTAL_INNER, self.rect.inflate(-8, -8),   border_radius=2)
        label = self._font.render("EXIT", True, BLACK)
        surface.blit(label, (self.rect.centerx - label.get_width()  // 2,
                              self.rect.centery - label.get_height() // 2))


class Projectile:
    def __init__(self, x: int, y: int, direction: int) -> None:
        self.rect      = pygame.Rect(x, y, 10, 5)
        self.direction = direction

    def update(self) -> None:
        self.rect.x += BULLET_SPEED * self.direction

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, BULLET_COLOR, self.rect)
        pygame.draw.rect(surface, BULLET_INNER, self.rect.inflate(-4, -2))

    def off_screen(self) -> bool:
        return self.rect.right < 0 or self.rect.left > SCREEN_W


class Player(PhysicsBody):
    W, H = 40, 30

    def __init__(self, x: int, y: int) -> None:
        self.rect        = pygame.Rect(x, y, self.W, self.H)
        self.vel_y       = 0.0
        self.on_ground   = False
        self.facing      = 1
        self.projectiles: list = []
        self.last_shot   = 0
        self.anim_frame  = 0
        self.anim_timer  = 0
        self._sprite_cache: dict = {}

    def update(self, platforms: list) -> None:
        keys = pygame.key.get_pressed()
        dx   = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -PLAYER_SPEED; self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  PLAYER_SPEED; self.facing =  1

        self.rect.x    += dx
        self.rect.left  = max(0,        self.rect.left)
        self.rect.right = min(SCREEN_W, self.rect.right)

        self._apply_gravity(platforms)

        self.anim_timer += 1
        if dx != 0 and self.anim_timer % 12 == 0:
            self.anim_frame = (self.anim_frame + 1) % 2

        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if not p.off_screen()]

    def jump(self) -> None:
        if self.on_ground:
            self.vel_y     = JUMP_VEL
            self.on_ground = False

    def shoot(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_shot >= SHOOT_COOLDOWN:
            bx = self.rect.right if self.facing == 1 else self.rect.left - 10
            self.projectiles.append(Projectile(bx, self.rect.centery - 3, self.facing))
            self.last_shot = now

    def _get_sprite(self) -> pygame.Surface | None:
        base = SPRITES.get("player")
        if base is None:
            return None
        if self.facing not in self._sprite_cache:
            self._sprite_cache[self.facing] = pygame.transform.flip(base, self.facing == -1, False)
        return self._sprite_cache[self.facing]

    def draw(self, surface: pygame.Surface) -> None:
        img = self._get_sprite()
        if img:
            surface.blit(img, self.rect)
        else:
            draw_monster(surface, self.rect, PLAYER_COLOR, self.anim_frame)
        for p in self.projectiles:
            p.draw(surface)


class Enemy(PhysicsBody):
    W, H = 36, 28

    def __init__(self, x: int, y: int, speed: float) -> None:
        self.rect       = pygame.Rect(x, y, self.W, self.H)
        self.vel_y      = 0.0
        self.on_ground  = False
        self.alive      = True
        self.speed      = speed
        self.anim_frame = 0
        self.anim_timer = 0

    def update(self, player: Player, platforms: list) -> None:
        if not self.alive:
            return
        self.rect.x += self.speed if player.rect.centerx > self.rect.centerx else -self.speed
        self._apply_gravity(platforms)
        self.anim_timer += 1
        if self.anim_timer % 10 == 0:
            self.anim_frame = (self.anim_frame + 1) % 2

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        img = SPRITES.get("enemy")
        if img:
            surface.blit(img, self.rect)
        else:
            draw_monster(surface, self.rect, ENEMY_COLOR, self.anim_frame)
