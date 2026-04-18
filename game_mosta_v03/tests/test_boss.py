"""Tests for the Boss class."""
import pytest

from constants import SCREEN_H, SCREEN_W
from entities  import Boss, BossProfile, BossPhase, Platform, Player


@pytest.fixture
def floor():
    return [Platform(0, SCREEN_H - 20, SCREEN_W)]


@pytest.fixture
def boss():
    return Boss(400, SCREEN_H - 20)


def test_boss_starts_with_full_hp(boss):
    assert boss.hp == boss.max_hp
    assert boss.alive
    assert boss.phase == BossPhase.CALM


def test_boss_take_damage_reduces_hp(boss):
    assert boss.take_damage(1) is True
    assert boss.hp == boss.max_hp - 1


def test_boss_iframes_block_damage(boss):
    assert boss.take_damage(1) is True
    assert boss.take_damage(1) is False   # blocked by i-frames
    assert boss.hp == boss.max_hp - 1


def test_boss_dies_when_hp_zero(boss):
    while boss.alive:
        boss.iframes = 0
        boss.take_damage(1)
    assert not boss.alive
    assert boss.take_damage(1) is False


@pytest.mark.parametrize("hp,expected_phase", [
    (8, BossPhase.CALM),
    (5, BossPhase.HUNT),
    (4, BossPhase.HUNT),
    (2, BossPhase.RAGE),
    (1, BossPhase.RAGE),
])
def test_boss_phase_threshold(boss, hp, expected_phase):
    boss.hp = hp
    assert boss.phase == expected_phase


def test_boss_speed_scales_with_phase(boss):
    boss.hp = 8; calm_speed = boss.speed
    boss.hp = 4; hunt_speed = boss.speed
    boss.hp = 1; rage_speed = boss.speed
    assert calm_speed < hunt_speed < rage_speed


def test_boss_update_does_nothing_when_dead(boss, floor):
    boss.hp = 0
    before = boss.rect.copy()
    boss.update(Player(600, SCREEN_H - 50), floor)
    assert boss.rect == before


def test_custom_profile():
    profile = BossProfile(max_hp=4, speed=3.0, phase_hp=(3, 1))
    b = Boss(100, 500, profile=profile)
    assert b.max_hp == 4
    b.hp = 3
    assert b.phase == BossPhase.HUNT
    b.hp = 1
    assert b.phase == BossPhase.RAGE
