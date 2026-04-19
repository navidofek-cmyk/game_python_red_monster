"""Sprite rendering for the terminal game.

Two sizes:
- HUD sprite  (12 chars wide) — shown in the info bar
- Game sprites (4 chars wide) — drawn in-game for player + enemies

Technique: Unicode '▀' (upper half block) with curses color pairs.
  foreground color = top pixel, background color = bottom pixel
  → 1 character cell shows 2 pixels vertically.

PIL is used to load & resize the PNG; tinting replaces the body color
to produce distinct enemy variants.
"""
from __future__ import annotations

import curses
from pathlib import Path

from PIL import Image

SPRITE_PATH = Path(__file__).resolve().parent.parent / "game_mosta_v03" / "mosta.png"

HUD_W  = 12   # HUD sprite: pixels wide (= display chars)

GAME_W = 4    # in-game sprite: pixels wide (= display chars)
GAME_H = 4    # in-game sprite: pixels tall  (= 2 display rows via half-block)

# Tint colors for enemy variants (replace the orange-red body)
_ENEMY_TINTS: dict[str, tuple[int, int, int]] = {
    "patrol": (70,  110, 255),   # blue
    "chase":  (230,  50,  50),   # bright red
    "jumper": (60,  200,  70),   # green
    "boss":   (190,  60, 220),   # purple
}

# ---- internal state ----------------------------------------------------------
# Pixel data: dict of name → list of rows, row = list of (top_rgb|None, bot_rgb|None)
_hud_rows:  list[list[tuple]] = []
_game_rows: dict[str, list[list[tuple]]] = {}

_color_idx: dict[tuple[int, int, int], int] = {}
_pair_idx:  dict[tuple[int, int], int]      = {}
_next_color = 16    # 0-15 are the 16 standard terminal colors
_next_pair  = 1


# ---- image helpers -----------------------------------------------------------

def _quantize(r: int, g: int, b: int) -> tuple[int, int, int]:
    return (r & ~15, g & ~15, b & ~15)


def _is_body(r: int, g: int, b: int, a: int) -> bool:
    """Detect the orange-red body pixels of mosta."""
    return a > 64 and r > 140 and g < 130 and b < 100 and r > g


def _tint(img: Image.Image, new_rgb: tuple[int, int, int]) -> Image.Image:
    """Replace body-colored pixels with new_rgb."""
    out = img.copy()
    px  = out.load()
    nr, ng, nb = new_rgb
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if _is_body(r, g, b, a):
                px[x, y] = (nr, ng, nb, a)
    return out


def _img_to_rows(img: Image.Image) -> list[list[tuple]]:
    """Convert an RGBA image to half-block pixel rows."""
    w, h = img.size
    px   = img.load()
    rows = []
    for y in range(0, h, 2):
        row = []
        for x in range(w):
            tr, tg, tb, ta = px[x, y]
            br, bg, bb, ba = px[x, y + 1] if y + 1 < h else (0, 0, 0, 255)
            top = _quantize(tr, tg, tb) if ta > 64 else None
            bot = _quantize(br, bg, bb) if ba > 64 else None
            row.append((top, bot))
        rows.append(row)
    return rows


# ---- public API: load (before curses) ----------------------------------------

def load_sprites(path: Path = SPRITE_PATH) -> bool:
    """Load all sprites from PNG. Call BEFORE curses.wrapper()."""
    global _hud_rows, _game_rows
    if not path.exists():
        return False
    src = Image.open(path).convert("RGBA")

    # HUD sprite — large version for the info bar
    # height: scale proportionally, round to even (half-block needs pairs of rows)
    hud_h  = max(2, round(src.height * HUD_W / src.width))
    if hud_h % 2:
        hud_h += 1
    hud_img   = src.resize((HUD_W, hud_h), Image.NEAREST)
    _hud_rows = _img_to_rows(hud_img)

    # Game sprites — small version for in-game entities
    base = src.resize((GAME_W, GAME_H), Image.NEAREST)
    _game_rows["player"] = _img_to_rows(base)
    for kind, tint in _ENEMY_TINTS.items():
        _game_rows[kind] = _img_to_rows(_tint(base, tint))

    return True


# ---- curses color registration (lazy, after start_color) ---------------------

def _get_color(rgb: tuple[int, int, int]) -> int:
    global _next_color
    if rgb in _color_idx:
        return _color_idx[rgb]
    idx = _next_color
    r, g, b = rgb
    curses.init_color(idx, r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)
    _color_idx[rgb] = idx
    _next_color += 1
    return idx


def _get_pair(fg: tuple | None, bg: tuple | None) -> int:
    global _next_pair
    fi = _get_color(fg) if fg else -1
    bi = _get_color(bg) if bg else -1
    key = (fi, bi)
    if key in _pair_idx:
        return _pair_idx[key]
    pair = _next_pair
    curses.init_pair(pair, fi, bi)
    _pair_idx[key] = pair
    _next_pair += 1
    return pair


# ---- public API: render (inside curses session) ------------------------------

def hud_sprite_height() -> int:
    return len(_hud_rows)


def render_hud_sprite(stdscr, y0: int, x0: int) -> None:
    """Draw the large HUD sprite at terminal position (y0, x0)."""
    for dy, row in enumerate(_hud_rows):
        for dx, (top, bot) in enumerate(row):
            if top is None and bot is None:
                continue
            pair = _get_pair(top, bot)
            char = "▀" if top else " "
            try:
                stdscr.addstr(y0 + dy, x0 + dx, char, curses.color_pair(pair))
            except curses.error:
                pass


def render_game_sprite(stdscr, kind: str, dy: int, dx: int,
                       flicker: bool = False) -> None:
    """Draw a game-size sprite.

    dy, dx — top-left corner in terminal coordinates.
    flicker — if True the sprite is invisible (iframes effect).
    """
    if flicker:
        return
    rows = _game_rows.get(kind)
    if not rows:
        return
    for row_i, row in enumerate(rows):
        for col_i, (top, bot) in enumerate(row):
            if top is None and bot is None:
                continue
            pair = _get_pair(top, bot)
            char = "▀" if top else " "
            try:
                stdscr.addstr(dy + row_i, dx + col_i, char,
                              curses.color_pair(pair))
            except curses.error:
                pass
