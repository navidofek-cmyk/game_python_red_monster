"""Red Monster — terminal (curses) version.  Run with: python3 game.py

Python features demonstrated across the modules:
- ``curses`` for the terminal UI (stdlib!)
- ``@dataclass`` for state  (entities.py, engine.py)
- ``enum.StrEnum`` for tiles + item kinds  (constants.py)
- ``pathlib`` + ``json`` for save/load  (save.py)
- ``random.Random(seed)`` for reproducible procgen  (world.py)
- Keyboard-driven game loop with ``stdscr.nodelay``  (here)
"""
from __future__ import annotations

import curses

from constants import GRID_H, GRID_W, HUD_H, TICK_MS
from engine import new_game, tick
from renderer import handle_key, render_area, render_hud, render_help
from sprite import load_sprite


def _main(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(TICK_MS)
    curses.start_color()
    curses.use_default_colors()   # -1 = terminal background (transparent)

    h, w = stdscr.getmaxyx()
    if h < GRID_H + HUD_H or w < GRID_W:
        stdscr.addstr(0, 0, f"Window too small. Need {GRID_W}x{GRID_H + HUD_H}, "
                            f"have {w}x{h}. Resize and restart.")
        stdscr.getch()
        return

    game = new_game()

    while True:
        stdscr.erase()
        render_area(stdscr, game)
        render_hud(stdscr, game)
        if game.show_help:
            render_help(stdscr)
        if game.status == "VICTORY":
            stdscr.addstr(GRID_H // 2, GRID_W // 2 - 5, "*** YOU WIN! ***")
        elif not game.player.alive:
            stdscr.addstr(GRID_H // 2, GRID_W // 2 - 5, "*** GAME OVER ***")
        stdscr.refresh()

        ch = stdscr.getch()
        if ch != -1:
            if not handle_key(game, ch):
                return
        tick(game)


def main() -> None:
    load_sprite()   # load PNG before curses starts
    try:
        curses.wrapper(_main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
