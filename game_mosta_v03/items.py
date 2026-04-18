"""Inventory and pickable world items.

Python features demonstrated:
- ``@dataclass(slots=True)`` for memory-efficient fixed-attribute records
- ``collections.Counter`` to hold per-item counts
- Operator overloading on ``Inventory`` (``in``, ``len``)
- ``classmethod`` alternative constructor (``Inventory.from_dict``)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import pygame

from constants import ItemKind


@dataclass(slots=True)
class Inventory:
    """Pure-Python inventory. No pygame — fully unit-testable."""
    counts: Counter = field(default_factory=Counter)

    def add(self, kind: ItemKind, n: int = 1) -> None:
        self.counts[kind] += n

    def count(self, kind: ItemKind) -> int:
        return self.counts.get(kind, 0)

    def use(self, kind: ItemKind) -> bool:
        """Consume one of `kind`. Returns True if there was one to consume."""
        if self.counts.get(kind, 0) <= 0:
            return False
        self.counts[kind] -= 1
        if self.counts[kind] == 0:
            del self.counts[kind]
        return True

    def __contains__(self, kind: ItemKind) -> bool:
        return self.counts.get(kind, 0) > 0

    def __len__(self) -> int:
        return sum(self.counts.values())

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Inventory":
        """Build an Inventory from a plain dict (e.g. loaded from JSON)."""
        inv = cls()
        for k, v in data.items():
            inv.counts[ItemKind(k)] = v
        return inv

    def to_dict(self) -> dict[str, int]:
        """Serialize to a plain dict (ItemKind -> int) for JSON save."""
        return {k.value: v for k, v in self.counts.items()}


_ITEM_COLORS: dict[ItemKind, tuple] = {
    ItemKind.POTION: (220, 60,  90),
    ItemKind.SPEED:  (80,  200, 255),
    ItemKind.JUMP:   (255, 210, 80),
    ItemKind.KEY:    (240, 230, 130),
}


class Item:
    """A world pickup. Has a rect, kind, and draw."""
    W, H = 18, 20

    def __init__(self, x: int, y: int, kind: ItemKind) -> None:
        self.rect  = pygame.Rect(x - self.W // 2, y - self.H, self.W, self.H)
        self.kind  = kind
        self.alive = True

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        color = _ITEM_COLORS[self.kind]
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, (30, 30, 30), self.rect, 2, border_radius=4)
        # A small glyph so items are identifiable without reading colors.
        cx, cy = self.rect.center
        if self.kind is ItemKind.POTION:
            pygame.draw.circle(surface, (255, 230, 230), (cx, cy), 3)
        elif self.kind is ItemKind.SPEED:
            pygame.draw.polygon(surface, (240, 240, 255),
                                [(cx - 3, cy - 4), (cx + 4, cy), (cx - 3, cy + 4)])
        elif self.kind is ItemKind.JUMP:
            pygame.draw.polygon(surface, (60, 60, 30),
                                [(cx, cy - 5), (cx - 4, cy + 3), (cx + 4, cy + 3)])
        elif self.kind is ItemKind.KEY:
            pygame.draw.circle(surface, (30, 30, 30), (cx - 3, cy - 2), 3, 1)
            pygame.draw.line(surface, (30, 30, 30), (cx, cy - 2), (cx + 5, cy - 2), 2)
