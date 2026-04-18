"""Round-trip tests for save.py."""
import json
import pytest

from constants import ItemKind
from entities  import Platform, Enemy, Player, Portal
from items     import Item, Inventory
from save      import (
    save_game, load_game, apply_save, has_save, delete_save, SAVE_VERSION,
)


@pytest.fixture
def save_path(tmp_path):
    return tmp_path / "save.json"


@pytest.fixture
def fake_world():
    """Minimal stand-in that mimics the GameWorld surface used by save_game."""
    class _GW:
        pass
    gw = _GW()
    gw.coord     = (2, 1)
    gw.visited   = {(1, 2), (1, 1), (2, 1)}
    gw.collected = {((1, 2), 0), ((2, 1), 1)}
    gw.score     = 42
    gw.player    = Player(123, 456)
    gw.player.hp        = 2
    gw.player.facing    = -1
    gw.player.inventory = Inventory()
    gw.player.inventory.add(ItemKind.POTION, 2)
    gw.player.inventory.add(ItemKind.JUMP)
    gw.player.speed_boost_frames = 30
    gw.player.jump_boost_frames  = 0
    return gw


def test_no_save_initially(save_path):
    assert has_save(save_path) is False
    assert load_game(save_path) is None


def test_save_and_load_roundtrip(fake_world, save_path):
    save_game(fake_world, save_path)
    assert has_save(save_path)
    data = load_game(save_path)
    assert data is not None
    assert data["version"] == SAVE_VERSION
    assert data["coord"]   == [2, 1]
    assert data["score"]   == 42


def test_apply_save_mutates_world(fake_world, save_path):
    save_game(fake_world, save_path)
    data = load_game(save_path)

    # Fresh world to receive the save
    class _GW: pass
    gw = _GW()
    gw.coord     = (0, 0)
    gw.visited   = set()
    gw.collected = set()
    gw.score     = 0
    gw.player    = Player(0, 0)

    apply_save(data, gw)

    assert gw.coord == (2, 1)
    assert (1, 2) in gw.visited
    assert ((1, 2), 0) in gw.collected
    assert gw.score == 42
    assert gw.player.hp == 2
    assert gw.player.facing == -1
    assert gw.player.inventory.count(ItemKind.POTION) == 2
    assert gw.player.inventory.count(ItemKind.JUMP)   == 1
    assert gw.player.speed_boost_frames == 30


def test_delete_save(fake_world, save_path):
    save_game(fake_world, save_path)
    assert has_save(save_path)
    delete_save(save_path)
    assert not has_save(save_path)


def test_load_rejects_wrong_version(save_path):
    save_path.write_text(json.dumps({"version": 0, "coord": [0, 0]}))
    assert load_game(save_path) is None


def test_load_rejects_corrupt_file(save_path):
    save_path.write_text("not json {{{{")
    assert load_game(save_path) is None


def test_save_file_is_valid_json(fake_world, save_path):
    save_game(fake_world, save_path)
    # Should parse without error
    raw = json.loads(save_path.read_text())
    assert "player" in raw and "inventory" in raw["player"]
