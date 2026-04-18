"""Tests for the pure-logic parts of the level editor."""
import json
import pytest

from editor import (
    EditorState, Tool, TOOL_ORDER, BIOME_NAMES, DECOR_KINDS,
    _snap, _cycle, _rect_from_drag, _erase_at, save_json, load_json,
)
from constants import AiType, ItemKind


def test_snap_rounds_to_grid():
    assert _snap(13) == 10
    assert _snap(18) == 10
    assert _snap(25) == 20
    assert _snap(0)  == 0


def test_cycle_wraps_around():
    assert _cycle([1, 2, 3], 1) == 2
    assert _cycle([1, 2, 3], 3) == 1


def test_rect_from_drag_normalizes_direction():
    rect = _rect_from_drag((100, 100), (50, 50))
    assert rect.x == 50 and rect.y == 50
    assert rect.w >= 20 and rect.h >= 14


def test_rect_from_drag_min_size():
    rect = _rect_from_drag((100, 100), (101, 101))
    assert rect.w >= 20 and rect.h >= 14


def test_erase_platform():
    state = EditorState()
    state.platforms.append({"x": 100, "y": 100, "w": 50, "h": 20})
    assert _erase_at(state, (120, 110)) == "platform"
    assert len(state.platforms) == 0


def test_erase_returns_empty_when_nothing_under_point():
    state = EditorState()
    assert _erase_at(state, (50, 50)) == ""


def test_save_and_load_roundtrip(tmp_path):
    path  = tmp_path / "area.json"
    state = EditorState(biome="snow")
    state.platforms.append({"x": 0, "y": 100, "w": 200, "h": 14})
    state.enemies.append({"x": 300, "y": 400, "ai": "chase"})
    state.items.append({"x": 100, "y": 200, "kind": "potion"})
    state.decor.append({"kind": "tree", "x": 400, "y": 500})

    save_json(state, path)
    loaded = load_json(path)
    assert loaded is not None
    assert loaded.biome == "snow"
    assert len(loaded.platforms) == 1
    assert loaded.enemies[0]["ai"] == "chase"
    assert loaded.items[0]["kind"] == "potion"


def test_load_missing_returns_none(tmp_path):
    assert load_json(tmp_path / "nope.json") is None


def test_load_corrupt_returns_none(tmp_path):
    path = tmp_path / "area.json"
    path.write_text("{{{ not json")
    assert load_json(path) is None


def test_all_tools_present():
    assert set(TOOL_ORDER) == set(Tool)


def test_all_biomes_have_names():
    assert len(BIOME_NAMES) >= 9


def test_decor_kinds_match_sprites_registry():
    from sprites import DECOR_DRAWERS
    for kind in DECOR_KINDS:
        assert kind in DECOR_DRAWERS
