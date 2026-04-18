"""Tests for world.py.

Pytest features used:
- ``pytest.fixture`` for reusable setup
- ``pytest.mark.parametrize`` for data-driven tests
"""
import pygame
import pytest

from world import (
    AREAS, AreaDef, Direction, START_COORD, GOAL_COORD, DELTA, OPPOSITE,
    all_coords, neighbor, edge_direction, in_bounds, reachable_from,
    spawn_position, spawn_area,
)
from constants import SCREEN_W, SCREEN_H
from entities import Platform, Enemy


@pytest.fixture
def all_area_coords():
    return list(AREAS.keys())


def test_has_nine_areas():
    assert len(AREAS) == 9


def test_area_defs_are_dataclasses():
    for coord, defn in AREAS.items():
        assert isinstance(defn, AreaDef), f"{coord} is not an AreaDef"


def test_start_and_goal_are_areas():
    assert START_COORD in AREAS
    assert GOAL_COORD  in AREAS


def test_every_area_has_at_least_one_neighbor(all_area_coords):
    for coord in all_area_coords:
        assert any(neighbor(coord, d) for d in Direction), f"{coord} isolated"


def test_all_areas_reachable_from_start():
    assert reachable_from(START_COORD) == set(AREAS.keys())


def test_neighbor_symmetry(all_area_coords):
    for coord in all_area_coords:
        for d in Direction:
            nxt = neighbor(coord, d)
            if nxt is None:
                continue
            assert neighbor(nxt, d.opposite) == coord


@pytest.mark.parametrize("coord,expected", [
    ((0, 0), True),  ((2, 2), True),
    ((-1, 0), False), ((3, 0), False), ((0, 3), False),
])
def test_in_bounds(coord, expected):
    assert in_bounds(coord) is expected


@pytest.mark.parametrize("rect,expected", [
    (pygame.Rect(-50, 100, 40, 30),          "left"),
    (pygame.Rect(SCREEN_W + 5, 100, 40, 30), "right"),
    (pygame.Rect(100, -50, 40, 30),          "up"),
    (pygame.Rect(100, SCREEN_H + 10, 40, 30), "down"),
    (pygame.Rect(100, 100, 40, 30),          None),
])
def test_edge_direction(rect, expected):
    assert edge_direction(rect) == expected


def test_spawn_position_opposite_sides():
    left_x,  _ = spawn_position("left")
    right_x, _ = spawn_position("right")
    assert left_x  < SCREEN_W // 2
    assert right_x > SCREEN_W // 2


def test_spawn_area_produces_platforms_and_enemies():
    platforms, enemies, bg, decor = spawn_area(START_COORD, Platform, Enemy)
    assert len(platforms) > 0
    assert isinstance(bg, tuple) and len(bg) == 3


def test_spawn_area_goal_has_altar_decor():
    _, _, _, decor = spawn_area(GOAL_COORD, Platform, Enemy)
    assert any(kind == "altar" for (kind, _, _) in decor)


def test_opposite_is_involutive():
    for d in Direction:
        assert d.opposite.opposite == d


def test_all_coords_generator_has_nine_items():
    assert len(list(all_coords())) == 9


def test_direction_delta_and_opposite():
    assert Direction.LEFT.delta    == (-1, 0)
    assert Direction.RIGHT.delta   == ( 1, 0)
    assert Direction.LEFT.opposite is Direction.RIGHT


def test_legacy_delta_and_opposite_maps():
    assert DELTA["left"]    == (-1, 0)
    assert OPPOSITE["up"]   == "down"
