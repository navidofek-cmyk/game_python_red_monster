"""Tests for items.py and Inventory logic (no pygame needed for Inventory)."""
import pytest

from constants import ItemKind, MAX_HP
from items     import Inventory, Item


@pytest.fixture
def inv():
    return Inventory()


def test_inventory_starts_empty(inv):
    assert len(inv) == 0
    assert ItemKind.POTION not in inv


def test_inventory_add_and_count(inv):
    inv.add(ItemKind.POTION)
    inv.add(ItemKind.POTION, 2)
    assert inv.count(ItemKind.POTION) == 3
    assert ItemKind.POTION in inv


def test_inventory_use_decrements(inv):
    inv.add(ItemKind.SPEED, 2)
    assert inv.use(ItemKind.SPEED) is True
    assert inv.count(ItemKind.SPEED) == 1
    assert inv.use(ItemKind.SPEED) is True
    assert inv.count(ItemKind.SPEED) == 0
    assert inv.use(ItemKind.SPEED) is False  # nothing left


def test_inventory_use_empty_returns_false(inv):
    assert inv.use(ItemKind.JUMP) is False


def test_inventory_len_sums_counts(inv):
    inv.add(ItemKind.POTION, 2)
    inv.add(ItemKind.SPEED,  1)
    assert len(inv) == 3


def test_inventory_roundtrip_via_dict(inv):
    inv.add(ItemKind.POTION, 2)
    inv.add(ItemKind.JUMP,   1)
    data   = inv.to_dict()
    assert data == {"potion": 2, "jump": 1}
    restored = Inventory.from_dict(data)
    assert restored.count(ItemKind.POTION) == 2
    assert restored.count(ItemKind.JUMP)   == 1


@pytest.mark.parametrize("kind", list(ItemKind))
def test_item_has_rect_and_kind(kind):
    item = Item(100, 200, kind)
    assert item.kind is kind
    assert item.rect.width  == Item.W
    assert item.rect.height == Item.H
    assert item.alive is True
