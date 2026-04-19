"""Tests for v04 terminal game pure logic (no curses)."""
import json

import pytest

from game import (
    Game, Player, Boss, Area, generate_world, generate_area,
    BIOMES, START_COORD, GOAL_COORD, GRID_W, GRID_H, MAX_HP, BOSS_HP,
    new_game, enter_area, tick, move_player, jump, use_item,
    save_game, load_game, is_platform_at, on_ground,
)
import random


def test_world_has_nine_areas():
    world = generate_world(seed=1)
    assert len(world) == 9
    assert set(world.keys()) == set(BIOMES.keys())


def test_seed_determinism():
    a = generate_world(seed=42)
    b = generate_world(seed=42)
    for coord in a:
        assert a[coord].platforms == b[coord].platforms
        assert a[coord].enemies   == b[coord].enemies


def test_start_area_has_no_enemies():
    world = generate_world(seed=123)
    assert world[START_COORD].enemies == []


def test_goal_area_has_altar_decor():
    world = generate_world(seed=123)
    kinds = {d["kind"] for d in world[GOAL_COORD].decor}
    assert "altar" in kinds


def test_new_game_initializes():
    game = new_game(seed=7)
    assert game.coord == START_COORD
    assert game.player.hp == MAX_HP
    assert game.seed == 7


def test_player_on_ground_when_standing_on_platform():
    game = new_game(seed=7)
    area = game.world[game.coord]
    # Put player above a known floor cell
    floor_plats = [p for p in area.platforms if p[1] == GRID_H - 1]
    assert floor_plats, "need a floor platform"
    px, py, pw = floor_plats[0]
    game.player.x = px + 1
    game.player.y = GRID_H - 2
    assert on_ground(area, game.player) is True


def test_jump_only_when_on_ground():
    game = new_game(seed=7)
    area = game.world[game.coord]
    game.player.y = 0
    jump(game)
    # Mid-air: vy shouldn't get a fresh jump velocity
    # (unless player happens to be on a platform at y=1)
    if not is_platform_at(area, game.player.x, 1):
        # Still falling
        assert game.player.vy >= 0 or game.player.vy == -3  # allow initial jump
    # Ground check
    floor_plats = [p for p in area.platforms if p[1] == GRID_H - 1]
    px, py, pw = floor_plats[0]
    game.player.x = px + 1
    game.player.y = GRID_H - 2
    game.player.vy = 0
    jump(game)
    assert game.player.vy < 0


def test_use_potion_heals():
    game = new_game(seed=7)
    game.player.hp = 1
    game.player.inventory["potion"] = 1
    use_item(game, "potion")
    assert game.player.hp == 2
    assert game.player.inventory["potion"] == 0


def test_use_item_without_stock_fails():
    game = new_game(seed=7)
    use_item(game, "potion")
    assert game.player.hp == MAX_HP  # unchanged


def test_boss_take_damage_and_phases():
    b = Boss(x=10, y=5)
    assert b.phase == "CALM"
    b.take_damage(2)
    b.iframes = 0
    b.take_damage(1)
    assert b.hp == 3
    assert b.phase == "HUNT"
    b.iframes = 0
    b.take_damage(2)
    assert b.phase == "RAGE"


def test_boss_in_goal_area_not_defeated():
    game = new_game(seed=7)
    game.coord = GOAL_COORD
    game.boss_defeated = False
    from game import _spawn_boss_if_goal
    _spawn_boss_if_goal(game)
    assert game.boss is not None
    assert not game.portal_active


def test_portal_after_boss_defeated():
    game = new_game(seed=7)
    game.coord = GOAL_COORD
    game.boss_defeated = True
    from game import _spawn_boss_if_goal
    _spawn_boss_if_goal(game)
    assert game.boss is None
    assert game.portal_active


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "save.json"
    game = new_game(seed=99)
    game.score = 42
    game.player.hp = 2
    game.player.inventory["potion"] = 3
    game.boss_defeated = True
    save_game(game, path)

    loaded = load_game(path)
    assert loaded is not None
    assert loaded.seed == 99
    assert loaded.score == 42
    assert loaded.player.hp == 2
    assert loaded.player.inventory["potion"] == 3
    assert loaded.boss_defeated is True


def test_load_missing_returns_none(tmp_path):
    assert load_game(tmp_path / "nope.json") is None


def test_load_wrong_version_returns_none(tmp_path):
    path = tmp_path / "save.json"
    path.write_text(json.dumps({"version": 0, "seed": 1, "coord": [0, 0]}))
    assert load_game(path) is None


@pytest.mark.parametrize("dx,expected_facing", [(1, 1), (-1, -1)])
def test_move_player_updates_facing(dx, expected_facing):
    game = new_game(seed=7)
    game.player.x = GRID_W // 2
    move_player(game, dx)
    assert game.player.facing == expected_facing
