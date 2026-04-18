"""Game entities: Player, Enemy, Platform, Portal, Projectile.

Python features demonstrated:
- ``typing.Protocol`` (structural typing) for the AI strategy interface
- Strategy pattern with concrete classes (PatrolStrategy, ChaseStrategy, JumperStrategy)
- ``@dataclass`` for the ``AIProfile`` configuration record
- ``functools.cache`` as a module-level memoization decorator
- ``@property`` for computed attributes
- ``match``/``case`` in ``make_strategy``
- Inheritance (``Player``, ``Enemy`` inherit ``PhysicsBody``)
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Protocol

import pygame

from constants import (
    SCREEN_W, SCREEN_H, GRAVITY, JUMP_VEL, PLAYER_SPEED,
    BULLET_SPEED, SHOOT_COOLDOWN,
    ENEMY_SIGHT_RANGE, ENEMY_JUMP_COOLDOWN,
    MAX_HP, INVINCIBILITY_FRAMES, BOOST_FRAMES,
    SPEED_BOOST_MULT, JUMP_BOOST_MULT,
    PLATFORM_COLOR, PLATFORM_SHINE,
    BULLET_COLOR, BULLET_INNER,
    PLAYER_COLOR, ENEMY_COLOR, PORTAL_COLOR, PORTAL_INNER, BLACK,
    AiType, ItemKind,
)
from items   import Inventory
from sprites import SPRITES, draw_monster


# --- Physics base -------------------------------------------------------------
class PhysicsBody:
    """Mixin providing gravity + platform collision. Subclasses own a ``rect``."""

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

    def _ground_ahead(self, direction: int, platforms: list) -> bool:
        probe_x = self.rect.right + 4 if direction > 0 else self.rect.left - 4
        probe_y = self.rect.bottom + 4
        return any(plat.rect.collidepoint(probe_x, probe_y) for plat in platforms)


# --- World objects ------------------------------------------------------------
class Platform:
    def __init__(self, x: int, y: int, w: int, h: int = 14,
                 color=PLATFORM_COLOR, shine=PLATFORM_SHINE) -> None:
        self.rect  = pygame.Rect(x, y, w, h)
        self.color = color
        self.shine = shine

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.line(surface, self.shine, self.rect.topleft, self.rect.topright, 2)


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
        pygame.draw.rect(surface, color,        self.rect,                 border_radius=4)
        pygame.draw.rect(surface, PORTAL_INNER, self.rect.inflate(-8, -8), border_radius=2)
        label = self._font.render("GOAL", True, BLACK)
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


# --- Player -------------------------------------------------------------------
@cache
def _flipped_player_sprite(facing: int) -> pygame.Surface | None:
    """Memoized: only flip the sprite once per facing direction."""
    base = SPRITES.get("player")
    if base is None:
        return None
    return pygame.transform.flip(base, facing == -1, False)


class Player(PhysicsBody):
    W, H = 40, 30

    def __init__(self, x: int, y: int) -> None:
        self.rect       = pygame.Rect(x, y, self.W, self.H)
        self.vel_y      = 0.0
        self.on_ground  = False
        self.facing     = 1
        self.projectiles: list[Projectile] = []
        self.last_shot  = -SHOOT_COOLDOWN
        self.anim_frame = 0
        self.anim_timer = 0
        self.hp         = MAX_HP
        self.iframes    = 0
        self.speed_boost_frames = 0
        self.jump_boost_frames  = 0
        self.inventory  = Inventory()

    @property
    def center(self) -> tuple[int, int]:
        return self.rect.center

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def invincible(self) -> bool:
        return self.iframes > 0

    @property
    def effective_speed(self) -> float:
        return PLAYER_SPEED * (SPEED_BOOST_MULT if self.speed_boost_frames > 0 else 1)

    @property
    def effective_jump_vel(self) -> float:
        return JUMP_VEL * (JUMP_BOOST_MULT if self.jump_boost_frames > 0 else 1)

    def take_damage(self, amount: int = 1) -> bool:
        """Apply damage if not invincible. Returns True if damage was taken."""
        if self.iframes > 0 or not self.alive:
            return False
        self.hp       = max(0, self.hp - amount)
        self.iframes  = INVINCIBILITY_FRAMES
        return True

    def heal(self, amount: int = 1) -> int:
        """Restore HP up to MAX_HP. Returns the amount actually healed."""
        before = self.hp
        self.hp = min(MAX_HP, self.hp + amount)
        return self.hp - before

    def use_item(self, kind: ItemKind) -> bool:
        """Consume an inventory item. Returns True if used."""
        if kind is ItemKind.POTION:
            if self.hp >= MAX_HP or not self.inventory.use(ItemKind.POTION):
                return False
            self.heal(1)
            return True
        if kind is ItemKind.SPEED:
            if not self.inventory.use(ItemKind.SPEED):
                return False
            self.speed_boost_frames = BOOST_FRAMES
            return True
        if kind is ItemKind.JUMP:
            if not self.inventory.use(ItemKind.JUMP):
                return False
            self.jump_boost_frames = BOOST_FRAMES
            return True
        return False  # KEY etc. — not consumable yet

    def update(self, platforms: list, allow_edges: dict[str, bool]) -> None:
        keys  = pygame.key.get_pressed()
        speed = self.effective_speed
        dx    = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -speed; self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  speed; self.facing =  1

        self.rect.x += int(dx)
        if not allow_edges.get("left",  False):
            self.rect.left  = max(0, self.rect.left)
        if not allow_edges.get("right", False):
            self.rect.right = min(SCREEN_W, self.rect.right)

        self._apply_gravity(platforms)

        if not allow_edges.get("down", False) and self.rect.bottom >= SCREEN_H:
            self.rect.bottom = SCREEN_H
            self.vel_y       = 0
            self.on_ground   = True

        self.anim_timer += 1
        if dx != 0 and self.anim_timer % 12 == 0:
            self.anim_frame = (self.anim_frame + 1) % 2

        # Tick down timers
        if self.iframes            > 0: self.iframes            -= 1
        if self.speed_boost_frames > 0: self.speed_boost_frames -= 1
        if self.jump_boost_frames  > 0: self.jump_boost_frames  -= 1

        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if not p.off_screen()]

    def jump(self) -> None:
        if self.on_ground:
            self.vel_y     = self.effective_jump_vel
            self.on_ground = False

    def shoot(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_shot >= SHOOT_COOLDOWN:
            bx = self.rect.right if self.facing == 1 else self.rect.left - 10
            self.projectiles.append(Projectile(bx, self.rect.centery - 3, self.facing))
            self.last_shot = now

    def draw(self, surface: pygame.Surface) -> None:
        # Flicker during i-frames — every 4 frames, skip drawing the body.
        if self.invincible and (self.iframes // 4) % 2 == 0:
            for p in self.projectiles:
                p.draw(surface)
            return
        img = _flipped_player_sprite(self.facing)
        if img:
            surface.blit(img, self.rect)
        else:
            draw_monster(surface, self.rect, PLAYER_COLOR, self.anim_frame)
        for p in self.projectiles:
            p.draw(surface)


# --- Enemy AI strategies ------------------------------------------------------
@dataclass(frozen=True)
class AIProfile:
    speed:     float
    can_jump:  bool
    chases:    bool


AI_PROFILES: dict[str, AIProfile] = {
    AiType.PATROL.value: AIProfile(speed=1.6, can_jump=False, chases=False),
    AiType.CHASE.value:  AIProfile(speed=2.2, can_jump=False, chases=True),
    AiType.JUMPER.value: AIProfile(speed=2.4, can_jump=True,  chases=True),
}


class EnemyAI(Protocol):
    """Structural interface for AI behaviors (Protocol = 'duck-typed interface')."""
    def decide(self, enemy: "Enemy", player: "Player", platforms: list) -> int:
        """Return +1 / -1 walking direction. Side effect: may set enemy.facing."""
        ...

    def wants_jump(self, enemy: "Enemy", player: "Player",
                   platforms: list, direction: int) -> bool:
        ...


class PatrolStrategy:
    def decide(self, enemy, player, platforms):
        if enemy.on_ground and not enemy._ground_ahead(enemy.facing, platforms):
            enemy.facing = -enemy.facing
        if enemy.rect.left  <= 0        and enemy.facing < 0: enemy.facing = 1
        if enemy.rect.right >= SCREEN_W and enemy.facing > 0: enemy.facing = -1
        return enemy.facing

    def wants_jump(self, enemy, player, platforms, direction):
        return False


class ChaseStrategy(PatrolStrategy):
    def decide(self, enemy, player, platforms):
        if enemy.sees(player):
            enemy.facing = 1 if player.rect.centerx > enemy.rect.centerx else -1
            return enemy.facing
        return super().decide(enemy, player, platforms)


class JumperStrategy(ChaseStrategy):
    def wants_jump(self, enemy, player, platforms, direction):
        if not enemy.on_ground or enemy.jump_cd > 0:
            return False
        player_above = player.rect.bottom < enemy.rect.top - 10
        gap_ahead    = not enemy._ground_ahead(direction, platforms)
        return player_above or gap_ahead


def make_strategy(ai_type: str) -> EnemyAI:
    """Factory: pick a strategy. Shows match/case for dispatch."""
    match ai_type:
        case AiType.PATROL.value: return PatrolStrategy()
        case AiType.CHASE.value:  return ChaseStrategy()
        case AiType.JUMPER.value: return JumperStrategy()
        case _:                   return PatrolStrategy()


# --- Enemy --------------------------------------------------------------------
class Enemy(PhysicsBody):
    W, H = 36, 28

    def __init__(self, x: int, y: int, ai_type: str = "patrol") -> None:
        self.rect       = pygame.Rect(x, y, self.W, self.H)
        self.vel_y      = 0.0
        self.on_ground  = False
        self.alive      = True
        self.ai_type    = ai_type
        self.profile    = AI_PROFILES.get(ai_type, AI_PROFILES["patrol"])
        self.strategy   = make_strategy(ai_type)
        self.facing     = 1
        self.jump_cd    = 0
        self.anim_frame = 0
        self.anim_timer = 0

    @property
    def speed(self) -> float:
        return self.profile.speed

    @property
    def can_jump(self) -> bool:
        return self.profile.can_jump

    @property
    def chase(self) -> bool:
        return self.profile.chases

    def sees(self, player: "Player") -> bool:
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        return abs(dx) < ENEMY_SIGHT_RANGE and abs(dy) < ENEMY_SIGHT_RANGE

    _sees_player = sees  # legacy alias used by older tests

    def update(self, player: "Player", platforms: list) -> None:
        if not self.alive:
            return
        direction = self.strategy.decide(self, player, platforms)
        self.facing = direction
        self.rect.x += int(self.speed * direction)
        self.rect.left  = max(0,        self.rect.left)
        self.rect.right = min(SCREEN_W, self.rect.right)

        if self.strategy.wants_jump(self, player, platforms, direction):
            self.vel_y     = JUMP_VEL * 0.85
            self.on_ground = False
            self.jump_cd   = ENEMY_JUMP_COOLDOWN

        self._apply_gravity(platforms)

        if self.rect.bottom >= SCREEN_H:
            self.rect.bottom = SCREEN_H
            self.vel_y       = 0
            self.on_ground   = True

        if self.jump_cd > 0:
            self.jump_cd -= 1

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


# --- Boss ---------------------------------------------------------------------
class BossPhase(str):
    """Plain string labels so they're easy to show in the HUD."""
    CALM = "CALM"
    HUNT = "HUNT"
    RAGE = "RAGE"


@dataclass(frozen=True)
class BossProfile:
    max_hp:    int
    speed:     float
    phase_hp:  tuple[int, int]  # (phase2_threshold, phase3_threshold)


BOSS_PROFILE = BossProfile(max_hp=8, speed=1.8, phase_hp=(5, 2))
BOSS_IFRAMES = 20


class Boss(PhysicsBody):
    """The final adversary at the Volcano Altar.

    Scales with remaining HP:
      - CALM: patrols slowly.
      - HUNT: chases the player at normal speed.
      - RAGE: chases fast and jumps aggressively.
    """
    W, H = 60, 50

    def __init__(self, x: int, y: int, profile: BossProfile = BOSS_PROFILE) -> None:
        self.rect      = pygame.Rect(x - self.W // 2, y - self.H, self.W, self.H)
        self.vel_y     = 0.0
        self.on_ground = False
        self.profile   = profile
        self.max_hp    = profile.max_hp
        self.hp        = profile.max_hp
        self.facing    = -1
        self.iframes   = 0
        self.jump_cd   = 0
        self._patrol   = PatrolStrategy()
        self._chase    = ChaseStrategy()
        self._jumper   = JumperStrategy()

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def speed(self) -> float:  # satisfies PatrolStrategy's "enemy.speed"
        scale = {BossPhase.CALM: 0.8, BossPhase.HUNT: 1.2, BossPhase.RAGE: 1.5}
        return self.profile.speed * scale[self.phase]

    @property
    def can_jump(self) -> bool:  # for parity with Enemy
        return True

    @property
    def jump_cd_attr(self) -> int:
        return self.jump_cd

    @property
    def phase(self) -> str:
        p2, p3 = self.profile.phase_hp
        if self.hp <= p3: return BossPhase.RAGE
        if self.hp <= p2: return BossPhase.HUNT
        return BossPhase.CALM

    def _strategy_for_phase(self):
        match self.phase:
            case BossPhase.CALM: return self._patrol
            case BossPhase.HUNT: return self._chase
            case BossPhase.RAGE: return self._jumper

    def sees(self, player: "Player") -> bool:  # boss always sees the player
        return True

    def _ground_ahead(self, direction: int, platforms: list) -> bool:
        return super()._ground_ahead(direction, platforms)

    def take_damage(self, amount: int = 1) -> bool:
        if self.iframes > 0 or not self.alive:
            return False
        self.hp       = max(0, self.hp - amount)
        self.iframes  = BOSS_IFRAMES
        return True

    def update(self, player: "Player", platforms: list) -> None:
        if not self.alive:
            return
        strategy  = self._strategy_for_phase()
        direction = strategy.decide(self, player, platforms)
        self.facing = direction
        self.rect.x += int(self.speed * direction)
        self.rect.left  = max(0,        self.rect.left)
        self.rect.right = min(SCREEN_W, self.rect.right)

        if strategy.wants_jump(self, player, platforms, direction):
            self.vel_y     = JUMP_VEL * 0.95
            self.on_ground = False
            self.jump_cd   = ENEMY_JUMP_COOLDOWN

        self._apply_gravity(platforms)
        if self.rect.bottom >= SCREEN_H:
            self.rect.bottom = SCREEN_H
            self.vel_y       = 0
            self.on_ground   = True

        if self.jump_cd > 0: self.jump_cd -= 1
        if self.iframes > 0: self.iframes -= 1

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        # Tinted by phase
        tint = {BossPhase.CALM: (200, 90, 60),
                BossPhase.HUNT: (230, 60, 40),
                BossPhase.RAGE: (255, 30, 30)}[self.phase]
        # Flash white during i-frames
        color = (255, 255, 255) if self.iframes > 0 else tint
        img = SPRITES.get("enemy")
        if img:
            scaled = pygame.transform.scale(img, (self.W, self.H))
            if self.facing == 1:
                scaled = pygame.transform.flip(scaled, True, False)
            surface.blit(scaled, self.rect)
            # phase outline
            pygame.draw.rect(surface, color, self.rect, 3, border_radius=6)
        else:
            draw_monster(surface, self.rect, color, 0)
