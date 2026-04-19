"""Curses rendering and keyboard handling."""
from __future__ import annotations

import curses

from constants import GRID_H, GRID_W, MAX_HP, Tile
from engine import Game, jump, move_player, new_game, shoot, use_item
from save import load_game, save_game
from sprite import render_game_sprite, render_hud_sprite

HELP_LINES = [
    "MOVE: arrows / hjkl   JUMP: space/w/k   SHOOT: f",
    "ITEMS: 1 potion  2 speed  3 jump      S save  L load",
    "HELP: H       QUIT: q                  NEW: n",
    "GOAL: reach the Volcano Summit altar after defeating the boss.",
    "Enemies: blue patrol, red chase, green jumper. Boss: purple $",
]


def render_area(stdscr, game: Game) -> None:
    area = game.world[game.coord]

    # --- background grid: platforms, decor, items, bullets ---
    grid = [[Tile.EMPTY.value for _ in range(GRID_W)] for _ in range(GRID_H)]

    for (x, y, w) in area.platforms:
        for i in range(w):
            if 0 <= x + i < GRID_W and 0 <= y < GRID_H:
                grid[y][x + i] = Tile.PLATFORM.value

    for d in area.decor:
        dx, dy = d["x"], d["y"]
        if 0 <= dx < GRID_W and 0 <= dy < GRID_H:
            grid[dy][dx] = {"altar": Tile.ALTAR, "tree": Tile.TREE,
                            "sign":  Tile.SIGN}[d["kind"]].value

    for it in area.items:
        if it["alive"] and 0 <= it["x"] < GRID_W and 0 <= it["y"] < GRID_H:
            grid[it["y"]][it["x"]] = {"potion": Tile.POTION,
                                       "speed":  Tile.SPEED,
                                       "jump":   Tile.JUMP}[it["kind"]].value

    for (bx, by, _) in game.player.bullets:
        if 0 <= bx < GRID_W and 0 <= by < GRID_H:
            grid[by][bx] = Tile.BULLET.value

    for y, row in enumerate(grid):
        stdscr.addstr(y, 0, "".join(row))

    # --- sprites overlaid on top of the background ---

    # Enemies (draw before player so player appears in front)
    for e in area.enemies:
        if e["alive"] and 0 <= e["x"] < GRID_W and 1 <= e["y"] < GRID_H:
            render_game_sprite(stdscr, e["ai"], e["y"] - 1, e["x"])

    # Boss
    if game.boss and game.boss.alive:
        bx, by = game.boss.x, game.boss.y
        if 0 <= bx < GRID_W and 1 <= by < GRID_H:
            render_game_sprite(stdscr, "boss", by - 1, bx)

    # Player (on top of everything)
    px, py = game.player.x, game.player.y
    if 0 <= px < GRID_W and 1 <= py < GRID_H:
        flicker = game.player.iframes > 0 and (game.player.iframes % 2 == 0)
        render_game_sprite(stdscr, "player", py - 1, px, flicker)


def render_hud(stdscr, game: Game) -> None:
    y0     = GRID_H
    sp_w   = 13
    txt_w  = GRID_W - sp_w
    hp_bar = "".join("♥" if i < game.player.hp else "·" for i in range(MAX_HP))
    inv    = game.player.inventory
    inv_line = (f"1:{inv.get('potion',0)}  2:{inv.get('speed',0)}  "
                f"3:{inv.get('jump',0)}")
    boost = []
    if game.player.speed_left > 0: boost.append(f"SPEED({game.player.speed_left})")
    if game.player.jump_left  > 0: boost.append(f"JUMP({game.player.jump_left})")
    coord_label = f"[{game.coord[0]},{game.coord[1]}] {game.world[game.coord].name}"
    try:
        stdscr.addstr(y0,     0, "─" * GRID_W)
        stdscr.addstr(y0 + 1, 0, f"HP {hp_bar}  Score {game.score:<4}  "
                                  f"{coord_label[:txt_w - 20]}")
        stdscr.addstr(y0 + 2, 0, f"Items {inv_line}   {' '.join(boost):<15}")
        if game.boss and game.boss.alive:
            stdscr.addstr(y0 + 3, 0,
                          f"BOSS [{game.boss.phase}] {game.boss.hp}/{game.boss.max_hp}")
        else:
            stdscr.addstr(y0 + 3, 0, f"Status: {game.status[:txt_w - 10]}")
    except curses.error:
        pass
    render_hud_sprite(stdscr, y0 + 1, GRID_W - sp_w)


def render_help(stdscr) -> None:
    for i, line in enumerate(HELP_LINES):
        try:
            stdscr.addstr(2 + i * 2, 4, line)
        except curses.error:
            pass


def handle_key(game: Game, ch: int) -> bool:
    """Return False to quit."""
    if ch in (ord("q"), 27):
        return False
    if ch == ord("h"):
        game.show_help = not game.show_help
        return True
    if ch == ord("n"):
        new = new_game()
        game.__dict__.update(new.__dict__)
        game.status = "New game."
        return True
    if ch == ord("s"):
        save_game(game)
        game.status = "Saved."
        return True
    if ch == ord("l"):
        loaded = load_game()
        if loaded:
            game.__dict__.update(loaded.__dict__)
            game.status = "Loaded."
        else:
            game.status = "No save."
        return True
    if not game.player.alive:
        return True
    if ch in (curses.KEY_LEFT,  ord("a")):
        move_player(game, -1)
    elif ch in (curses.KEY_RIGHT, ord("d")):
        move_player(game, 1)
    elif ch in (curses.KEY_UP, ord("w"), ord("k"), ord(" ")):
        jump(game)
    elif ch == ord("f"):
        shoot(game)
    elif ch == ord("1"):
        use_item(game, "potion")
    elif ch == ord("2"):
        use_item(game, "speed")
    elif ch == ord("3"):
        use_item(game, "jump")
    return True
