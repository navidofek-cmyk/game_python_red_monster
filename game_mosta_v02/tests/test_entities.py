"""Tests for entities.py — AI strategies and Player behavior."""
import pygame
import pytest

from entities import (
    Platform, Enemy, Player, Projectile,
    AI_PROFILES, make_strategy,
    PatrolStrategy, ChaseStrategy, JumperStrategy,
)
from constants import SCREEN_W, SCREEN_H, ENEMY_SIGHT_RANGE, AiType


@pytest.fixture
def floor():
    return [Platform(0, SCREEN_H - 20, SCREEN_W)]


@pytest.fixture
def narrow_platform():
    return [Platform(100, 400, 120)]


@pytest.mark.parametrize("ai_type", [AiType.PATROL, AiType.CHASE, AiType.JUMPER])
def test_ai_profile_exists_for_each_type(ai_type):
    assert ai_type.value in AI_PROFILES


@pytest.mark.parametrize("ai_type,expected_cls", [
    (AiType.PATROL.value, PatrolStrategy),
    (AiType.CHASE.value,  ChaseStrategy),
    (AiType.JUMPER.value, JumperStrategy),
    ("unknown",           PatrolStrategy),  # fallback
])
def test_make_strategy_returns_expected(ai_type, expected_cls):
    assert isinstance(make_strategy(ai_type), expected_cls)


def test_patrol_enemy_flips_at_platform_edge(narrow_platform):
    enemy = Enemy(150, 400 - Enemy.H, "patrol")
    enemy.on_ground = True
    enemy.facing    = 1
    enemy.rect.right = 100 + 120
    player = Player(400, 400)
    enemy.update(player, narrow_platform)
    assert enemy.facing == -1


def test_chase_enemy_moves_toward_player(floor):
    enemy = Enemy(400, SCREEN_H - 50, "chase")
    player = Player(600, SCREEN_H - 50)
    start_x = enemy.rect.x
    enemy.update(player, floor)
    assert enemy.rect.x > start_x


@pytest.mark.parametrize("dx,visible", [
    (50,  True),
    (ENEMY_SIGHT_RANGE - 5, True),
    (ENEMY_SIGHT_RANGE + 5, False),
    (1000, False),
])
def test_enemy_sight_range(dx, visible):
    enemy = Enemy(100, 300, "chase")
    player = Player(100 + dx, 300)
    assert enemy.sees(player) is visible


def test_jumper_jumps_when_player_above(floor):
    enemy  = Enemy(400, SCREEN_H - 50, "jumper")
    enemy.on_ground = True
    player = Player(420, 100)
    enemy.update(player, floor)
    assert enemy.vel_y < 0  # jumping up


def test_dead_enemy_does_not_update(floor):
    enemy = Enemy(400, SCREEN_H - 50, "chase")
    enemy.alive = False
    start = enemy.rect.copy()
    enemy.update(Player(600, SCREEN_H - 50), floor)
    assert enemy.rect == start


@pytest.mark.parametrize("x,direction,off", [
    (-20,         -1, True),
    (SCREEN_W + 10, 1, True),
    (400,           1, False),
])
def test_projectile_off_screen(x, direction, off):
    assert Projectile(x, 100, direction).off_screen() is off


def test_player_jump_requires_ground():
    player = Player(100, 100)
    player.on_ground = False
    player.jump()
    assert player.vel_y == 0.0

    player.on_ground = True
    player.jump()
    assert player.vel_y < 0


def test_player_shoot_respects_cooldown():
    player = Player(100, 100)
    player.shoot()
    player.shoot()  # immediately again
    assert len(player.projectiles) == 1


def test_player_blocked_at_edge_when_no_neighbor(floor):
    player = Player(-5, SCREEN_H - 50)
    player.update(floor, {"left": False, "right": False, "up": False, "down": False})
    assert player.rect.left >= 0


def test_player_can_exit_edge_when_neighbor_allowed(floor):
    player = Player(SCREEN_W - 10, SCREEN_H - 50)
    # Simulate several frames pressing right via direct x manipulation:
    player.rect.x = SCREEN_W + 5
    player.update(floor, {"left": False, "right": True, "up": False, "down": False})
    # Right edge should NOT be clamped when neighbor allowed.
    assert player.rect.left > SCREEN_W or player.rect.right > SCREEN_W


def test_enemy_properties_reflect_profile():
    jumper = Enemy(0, 0, "jumper")
    chaser = Enemy(0, 0, "chase")
    assert jumper.can_jump is True
    assert chaser.can_jump is False
    assert chaser.chase is True
