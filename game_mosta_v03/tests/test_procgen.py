"""Tests for procedural world generation."""
import pytest

from world    import AreaDef, GRID_W, GRID_H, START_COORD, GOAL_COORD
from procgen  import generate_world, generate_area, BIOME_MAP
import random


def test_world_has_all_nine_areas():
    w = generate_world(seed=42)
    assert len(w) == GRID_W * GRID_H
    assert all(isinstance(defn, AreaDef) for defn in w.values())


def test_seed_is_deterministic():
    a = generate_world(seed=123)
    b = generate_world(seed=123)
    # Compare platform specs for every coord
    for coord, defn in a.items():
        assert defn.platforms == b[coord].platforms
        assert defn.enemies   == b[coord].enemies
        assert defn.items     == b[coord].items


def test_different_seeds_yield_different_worlds():
    a = generate_world(seed=1)
    b = generate_world(seed=2)
    differ = any(a[c].platforms != b[c].platforms for c in a)
    assert differ


def test_start_area_has_no_enemies():
    w = generate_world(seed=7)
    assert len(w[START_COORD].enemies) == 0


def test_goal_area_has_altar_decor():
    w = generate_world(seed=7)
    kinds = {d.kind for d in w[GOAL_COORD].decor}
    assert "altar" in kinds


def test_biome_map_is_stable_regardless_of_seed():
    w1 = generate_world(seed=1)
    w2 = generate_world(seed=999)
    for coord, biome in BIOME_MAP.items():
        assert w1[coord].biome == biome
        assert w2[coord].biome == biome


def test_generated_platforms_are_within_screen():
    from constants import SCREEN_W
    rng = random.Random(42)
    defn = generate_area((1, 1), rng)
    for p in defn.platforms:
        assert 0 <= p.x
        assert p.x + p.w <= SCREEN_W + 50   # small tolerance for off-grid
