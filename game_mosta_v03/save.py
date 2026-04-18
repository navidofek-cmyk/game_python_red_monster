"""Save / load the game state to JSON.

Python features demonstrated:
- ``pathlib.Path`` for filesystem operations
- ``json`` (stdlib) for serialization
- ``@dataclass`` + ``dataclasses.asdict`` for a typed save schema
- Round-trip conversion of custom types (tuples, sets) that JSON does not
  natively support — we convert them to/from lists on the boundary
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

SAVE_VERSION = 3
SAVE_FILE    = Path(__file__).resolve().parent / "save.json"


@dataclass
class PlayerSnapshot:
    hp:        int
    x:         int
    y:         int
    facing:    int
    inventory: dict[str, int]
    speed_boost_frames: int = 0
    jump_boost_frames:  int = 0


@dataclass
class SaveData:
    version:       int
    coord:         list[int]
    visited:       list[list[int]]
    collected:     list[list[Any]]
    score:         int
    player:        PlayerSnapshot
    boss_defeated: bool = False


def has_save(path: Path = SAVE_FILE) -> bool:
    return path.exists()


def delete_save(path: Path = SAVE_FILE) -> None:
    path.unlink(missing_ok=True)


def save_game(gw, path: Path = SAVE_FILE) -> None:
    """Serialize the current GameWorld to JSON."""
    data = SaveData(
        version       = SAVE_VERSION,
        coord         = list(gw.coord),
        visited       = sorted([list(c) for c in gw.visited]),
        collected     = [[list(coord), idx] for (coord, idx) in gw.collected],
        score         = gw.score,
        boss_defeated = getattr(gw, "boss_defeated", False),
        player        = PlayerSnapshot(
            hp        = gw.player.hp,
            x         = gw.player.rect.x,
            y         = gw.player.rect.y,
            facing    = gw.player.facing,
            inventory = gw.player.inventory.to_dict(),
            speed_boost_frames = gw.player.speed_boost_frames,
            jump_boost_frames  = gw.player.jump_boost_frames,
        ),
    )
    path.write_text(json.dumps(asdict(data), indent=2))


def load_game(path: Path = SAVE_FILE) -> dict | None:
    """Read the save file. Returns a plain dict, or None if missing/corrupt."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or data.get("version") != SAVE_VERSION:
        return None
    return data


def apply_save(data: dict, gw) -> None:
    """Mutate ``gw`` in place to match a loaded save dict."""
    from items import Inventory
    gw.coord         = tuple(data["coord"])
    gw.visited       = {tuple(c) for c in data["visited"]}
    gw.collected     = {(tuple(c), idx) for (c, idx) in data["collected"]}
    gw.score         = data["score"]
    gw.boss_defeated = data.get("boss_defeated", False)

    p = data["player"]
    gw.player.hp       = p["hp"]
    gw.player.rect.x   = p["x"]
    gw.player.rect.y   = p["y"]
    gw.player.facing   = p["facing"]
    gw.player.inventory = Inventory.from_dict(p["inventory"])
    gw.player.speed_boost_frames = p.get("speed_boost_frames", 0)
    gw.player.jump_boost_frames  = p.get("jump_boost_frames",  0)
