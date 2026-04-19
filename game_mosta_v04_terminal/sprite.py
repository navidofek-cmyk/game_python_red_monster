"""Load mosta.png and render it as colored half-block characters in curses.

Trick: Unicode '▀' (upper half block) with foreground = top pixel,
background = bottom pixel → each character cell shows 2 pixels vertically.
"""
from __future__ import annotations

import curses
from pathlib import Path

from PIL import Image

SPRITE_PATH = Path(__file__).resolve().parent.parent / "game_mosta_v03" / "mosta.png"
SPRITE_W    = 12   # pixels wide after resize (= 12 chars wide in terminal)

# Filled lazily on first render_sprite() call after curses.start_color()
_rows:       list[list[tuple]] = []   # [row][col] = (top_rgb|None, bot_rgb|None)
_color_idx:  dict[tuple[int,int,int], int] = {}
_pair_idx:   dict[tuple[int,int], int]     = {}
_next_color  = 16   # 0-15 are the standard terminal colors
_next_pair   = 1


def _quantize(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Snap to nearest multiple of 8 to cut down unique colors."""
    return (r & ~7, g & ~7, b & ~7)


def load_sprite(path: Path = SPRITE_PATH) -> bool:
    """Read PNG and store pixel data. Call once at startup (no curses yet)."""
    global _rows
    if not path.exists():
        return False
    img = Image.open(path).convert("RGBA")

    # Scale to SPRITE_W pixels wide, keeping pixel-art sharpness
    ratio  = SPRITE_W / img.width
    height = int(img.height * ratio)
    if height % 2:          # must be even for the half-block trick
        height += 1
    img = img.resize((SPRITE_W, height), Image.NEAREST)

    px = img.load()
    _rows.clear()
    for y in range(0, height, 2):
        row = []
        for x in range(SPRITE_W):
            tr, tg, tb, ta = px[x, y]
            br, bg, bb, ba = px[x, y + 1] if y + 1 < height else (0, 0, 0, 255)
            top = _quantize(tr, tg, tb) if ta > 64 else None
            bot = _quantize(br, bg, bb) if ba > 64 else None
            row.append((top, bot))
        _rows.append(row)
    return bool(_rows)


def _get_color(rgb: tuple[int, int, int]) -> int:
    """Register an RGB color with curses (0-1000 scale) and return its index."""
    global _next_color
    if rgb in _color_idx:
        return _color_idx[rgb]
    idx = _next_color
    r, g, b = rgb
    curses.init_color(idx, r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)
    _color_idx[rgb] = idx
    _next_color += 1
    return idx


def _get_pair(top: tuple | None, bot: tuple | None) -> int:
    """Return a curses color pair index for (fg=top, bg=bot) pixel colors."""
    global _next_pair
    fg = _get_color(top) if top else -1   # -1 = terminal default
    bg = _get_color(bot) if bot else -1
    key = (fg, bg)
    if key in _pair_idx:
        return _pair_idx[key]
    pair = _next_pair
    curses.init_pair(pair, fg, bg)
    _pair_idx[key] = pair
    _next_pair += 1
    return pair


def sprite_height() -> int:
    return len(_rows)


def render_sprite(stdscr, y0: int, x0: int) -> None:
    """Draw the pre-loaded sprite at terminal position (y0, x0)."""
    if not _rows:
        return
    for dy, row in enumerate(_rows):
        for dx, (top, bot) in enumerate(row):
            if top is None and bot is None:
                continue                         # fully transparent — skip
            pair  = _get_pair(top, bot)
            char  = "▀" if top else " "
            try:
                stdscr.addstr(y0 + dy, x0 + dx, char, curses.color_pair(pair))
            except curses.error:
                pass
