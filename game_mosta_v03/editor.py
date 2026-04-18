"""Standalone area editor for Red Monster.

Run with:  uv run python editor.py

Lets you design a single custom area (platforms, enemies, items, decor) and
save it to JSON. The save format mirrors ``world.AreaDef``.

Python features demonstrated:
- ``enum.Enum`` for tool modes
- ``@dataclass`` for editor state
- ``json`` + ``pathlib`` for save/load
- ``match``/``case`` for key/mouse event dispatch
- Small UI rendered entirely with pygame primitives
"""
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator

import pygame

from constants import (
    SCREEN_W, SCREEN_H, FPS, BIOMES, AiType, ItemKind,
    TEXT_COLOR, HINT_COLOR, DIM_COLOR, PLAYER_COLOR,
)
from sprites import load_sprites, draw_decor
from entities import Platform, Enemy, Player

EDITOR_FILE = Path(__file__).resolve().parent / "custom_area.json"

BIOME_NAMES = list(BIOMES.keys())
DECOR_KINDS = ("tree", "altar", "sign")
GRID_SNAP   = 10   # snap cursor to 10-pixel grid


class Tool(Enum):
    PLATFORM = "platform"
    ENEMY    = "enemy"
    ITEM     = "item"
    DECOR    = "decor"
    ERASE    = "erase"


TOOL_ORDER = list(Tool)


@dataclass
class EditorState:
    biome:     str  = "meadow"
    tool:      Tool = Tool.PLATFORM
    enemy_ai:  AiType    = AiType.PATROL
    item_kind: ItemKind  = ItemKind.POTION
    decor_idx: int       = 0
    platforms: list = field(default_factory=list)   # list[dict(x,y,w,h)]
    enemies:   list = field(default_factory=list)   # list[dict(x,y,ai)]
    items:     list = field(default_factory=list)   # list[dict(x,y,kind)]
    decor:     list = field(default_factory=list)   # list[dict(kind,x,y)]
    drag_start: tuple[int, int] | None = None
    status:     str = "Ready."


def _snap(v: int) -> int:
    return (v // GRID_SNAP) * GRID_SNAP


def _cycle(seq, current):
    i = seq.index(current)
    return seq[(i + 1) % len(seq)]


def _rect_from_drag(start: tuple[int, int], end: tuple[int, int]) -> pygame.Rect:
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = max(20, abs(end[0] - start[0]))
    h = max(14, abs(end[1] - start[1]))
    return pygame.Rect(_snap(x), _snap(y), max(20, _snap(w)), max(14, _snap(h)))


def _point_in(obj_rect_dict: dict, point: tuple[int, int]) -> bool:
    x, y = point
    r = obj_rect_dict
    return r["x"] <= x <= r["x"] + r.get("w", 20) and \
           r["y"] <= y <= r["y"] + r.get("h", 20)


def _erase_at(state: EditorState, point: tuple[int, int]) -> str:
    """Remove first item under point. Returns kind removed (or empty string)."""
    for obj in state.platforms:
        if _point_in(obj, point):
            state.platforms.remove(obj); return "platform"
    for obj in state.enemies:
        if abs(obj["x"] - point[0]) < 20 and abs(obj["y"] - point[1]) < 28:
            state.enemies.remove(obj); return "enemy"
    for obj in state.items:
        if abs(obj["x"] - point[0]) < 18 and abs(obj["y"] - point[1]) < 20:
            state.items.remove(obj); return "item"
    for obj in state.decor:
        if abs(obj["x"] - point[0]) < 40 and abs(obj["y"] - point[1]) < 120:
            state.decor.remove(obj); return "decor"
    return ""


def save_json(state: EditorState, path: Path = EDITOR_FILE) -> None:
    data = {
        "biome":     state.biome,
        "name":      "Custom Area",
        "platforms": state.platforms,
        "enemies":   state.enemies,
        "items":     state.items,
        "decor":     state.decor,
    }
    path.write_text(json.dumps(data, indent=2))


def load_json(path: Path = EDITOR_FILE) -> EditorState | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    state = EditorState(biome=data.get("biome", "meadow"))
    state.platforms = data.get("platforms", [])
    state.enemies   = data.get("enemies",   [])
    state.items     = data.get("items",     [])
    state.decor     = data.get("decor",     [])
    return state


@contextmanager
def pygame_session(title: str, size: tuple[int, int]) -> Iterator[pygame.Surface]:
    pygame.init()
    try:
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption(title)
        yield screen
    finally:
        pygame.quit()


def _handle_keydown(event, state: EditorState) -> None:
    k = event.key
    if k == pygame.K_TAB:
        state.tool = _cycle(TOOL_ORDER, state.tool)
        state.status = f"Tool: {state.tool.value}"
    elif k == pygame.K_b:
        state.biome = _cycle(BIOME_NAMES, state.biome)
        state.status = f"Biome: {state.biome}"
    elif k == pygame.K_s:
        save_json(state)
        state.status = f"Saved to {EDITOR_FILE.name}"
    elif k == pygame.K_l:
        loaded = load_json()
        if loaded is not None:
            state.__dict__.update(loaded.__dict__)
            state.status = f"Loaded {EDITOR_FILE.name}"
        else:
            state.status = "Nothing to load."
    elif k == pygame.K_r:
        state.platforms.clear(); state.enemies.clear()
        state.items.clear();     state.decor.clear()
        state.status = "Cleared."
    elif k == pygame.K_ESCAPE:
        pygame.quit(); sys.exit()
    elif k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
        idx = k - pygame.K_1
        match state.tool:
            case Tool.ENEMY:
                options = list(AiType)
                if idx < len(options):
                    state.enemy_ai = options[idx]
                    state.status = f"Enemy AI: {state.enemy_ai.value}"
            case Tool.ITEM:
                options = list(ItemKind)
                if idx < len(options):
                    state.item_kind = options[idx]
                    state.status = f"Item: {state.item_kind.value}"
            case Tool.DECOR:
                if idx < len(DECOR_KINDS):
                    state.decor_idx = idx
                    state.status = f"Decor: {DECOR_KINDS[idx]}"


def _handle_click(pos: tuple[int, int], button: int, state: EditorState) -> None:
    if button == 3:  # right click = always erase
        removed = _erase_at(state, pos)
        state.status = f"Erased {removed}" if removed else "Nothing here."
        return

    match state.tool:
        case Tool.PLATFORM:
            pass  # handled on drag end
        case Tool.ENEMY:
            state.enemies.append({"x": _snap(pos[0]), "y": _snap(pos[1]),
                                  "ai": state.enemy_ai.value})
            state.status = f"+ {state.enemy_ai.value}"
        case Tool.ITEM:
            state.items.append({"x": _snap(pos[0]), "y": _snap(pos[1]),
                                "kind": state.item_kind.value})
            state.status = f"+ {state.item_kind.value}"
        case Tool.DECOR:
            state.decor.append({"kind": DECOR_KINDS[state.decor_idx],
                                "x": _snap(pos[0]), "y": _snap(pos[1])})
            state.status = f"+ {DECOR_KINDS[state.decor_idx]} decor"
        case Tool.ERASE:
            removed = _erase_at(state, pos)
            state.status = f"Erased {removed}" if removed else "Nothing here."


def _draw_preview(screen, state: EditorState) -> None:
    palette = BIOMES[state.biome]
    screen.fill(palette.bg)
    # Platforms
    for p in state.platforms:
        rect = pygame.Rect(p["x"], p["y"], p["w"], p["h"])
        pygame.draw.rect(screen, palette.platform, rect)
        pygame.draw.line(screen, palette.shine, rect.topleft, rect.topright, 2)
    # Decor (use the game's registry)
    draw_decor(screen, [(d["kind"], d["x"], d["y"]) for d in state.decor])
    # Enemies (tiny red squares with label)
    for e in state.enemies:
        pygame.draw.rect(screen, (220, 40, 40),
                         (e["x"] - 18, e["y"] - 28, 36, 28))
        lbl = pygame.font.SysFont("monospace", 11, bold=True).render(
            e["ai"][:1].upper(), True, (255, 255, 255))
        screen.blit(lbl, (e["x"] - 4, e["y"] - 22))
    # Items
    for it in state.items:
        pygame.draw.rect(screen, (220, 60, 90),
                         (it["x"] - 9, it["y"] - 20, 18, 20), border_radius=4)


def _draw_hud(screen, font, state: EditorState) -> None:
    bar = pygame.Surface((SCREEN_W, 60), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 170))
    screen.blit(bar, (0, SCREEN_H - 60))

    detail = ""
    match state.tool:
        case Tool.ENEMY: detail = f" [{state.enemy_ai.value}]"
        case Tool.ITEM:  detail = f" [{state.item_kind.value}]"
        case Tool.DECOR: detail = f" [{DECOR_KINDS[state.decor_idx]}]"

    screen.blit(font.render(f"Tool: {state.tool.value}{detail}   Biome: {state.biome}",
                            True, TEXT_COLOR), (10, SCREEN_H - 54))
    screen.blit(font.render(state.status, True, PLAYER_COLOR),
                (10, SCREEN_H - 28))
    hint = ("TAB tool  B biome  1-4 sub  L-click place  drag = rect  "
            "R-click erase  S save  L load  R reset  ESC quit")
    screen.blit(font.render(hint, True, HINT_COLOR),
                (10, SCREEN_H - 12))


def main() -> None:
    with pygame_session("Red Monster – Level Editor", (SCREEN_W, SCREEN_H)) as screen:
        clock = pygame.time.Clock()
        load_sprites(Player.W, Player.H, Enemy.W, Enemy.H)
        font = pygame.font.SysFont("monospace", 14, bold=True)

        state = EditorState()

        while True:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    _handle_keydown(event, state)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and state.tool == Tool.PLATFORM:
                        state.drag_start = event.pos
                    else:
                        _handle_click(event.pos, event.button, state)
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and state.drag_start is not None:
                        rect = _rect_from_drag(state.drag_start, event.pos)
                        state.platforms.append(
                            {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h})
                        state.status = (f"+ platform ({rect.w}x{rect.h}) at "
                                        f"({rect.x},{rect.y})")
                        state.drag_start = None

            _draw_preview(screen, state)

            # Active drag rectangle preview
            if state.drag_start is not None:
                rect = _rect_from_drag(state.drag_start, pygame.mouse.get_pos())
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)

            _draw_hud(screen, font, state)
            pygame.display.flip()


if __name__ == "__main__":
    main()
