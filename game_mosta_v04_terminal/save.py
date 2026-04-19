from __future__ import annotations

import json
from pathlib import Path

from constants import SAVE_FILE
from engine import Game, new_game, _spawn_boss_if_goal


def save_game(game: Game, path: Path = SAVE_FILE) -> None:
    data = {
        "version": 4,
        "seed": game.seed,
        "coord": list(game.coord),
        "visited": sorted(list(list(c) for c in game.visited)),
        "collected": [[list(c), idx] for (c, idx) in game.collected],
        "score": game.score,
        "boss_defeated": game.boss_defeated,
        "player": {
            "x": game.player.x, "y": game.player.y,
            "hp": game.player.hp, "facing": game.player.facing,
            "speed_left": game.player.speed_left,
            "jump_left":  game.player.jump_left,
            "inventory":  dict(game.player.inventory),
        },
    }
    path.write_text(json.dumps(data, indent=2))


def load_game(path: Path = SAVE_FILE) -> Game | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("version") != 4:
        return None
    game = new_game(seed=data["seed"])
    game.coord         = tuple(data["coord"])
    game.visited       = {tuple(c) for c in data["visited"]}
    game.collected     = {(tuple(c), idx) for (c, idx) in data["collected"]}
    game.score         = data["score"]
    game.boss_defeated = data.get("boss_defeated", False)
    p = data["player"]
    game.player.x          = p["x"]
    game.player.y          = p["y"]
    game.player.hp         = p["hp"]
    game.player.facing     = p["facing"]
    game.player.speed_left = p.get("speed_left", 0)
    game.player.jump_left  = p.get("jump_left",  0)
    game.player.inventory  = dict(p["inventory"])
    area = game.world[game.coord]
    for it in area.items:
        if (tuple(it["uid"][0]), it["uid"][1]) in game.collected:
            it["alive"] = False
    _spawn_boss_if_goal(game)
    return game
