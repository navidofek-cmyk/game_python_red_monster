# Red Monster – Journey of Mosta

Learning Python project — platform shooter game built in progressively more advanced versions.

## Verze

| Složka | Verze | Co přibilo |
|--------|-------|-----------|
| `game_mosta_v01` | 0.1 | Základní pygame hra: hráč, nepřátelé, platformy, střelba, levely |
| `game_mosta_v02` | 0.2 | Testy (pytest), `world.py`, `pyproject.toml`, balíčková struktura |
| `game_mosta_v03` | 0.3 | Save/load (JSON), boss fight, in-game help, level editor, procedurální generování světa |
| `game_mosta_v04_terminal` | 0.4 | Terminálová verze (curses, stdlib-only), ASCII grafika, stejný herní svět |

## Spuštění

### v01
```bash
cd game_mosta_v01
pip install pygame
python main.py
```

### v02 / v03 (pygame, uv)
```bash
cd game_mosta_v03
uv sync
uv run mosta
```

### v04 – terminálová verze (bez závislostí)
```bash
cd game_mosta_v04_terminal
python game.py
```

## Ovládání (v01–v03)

| Klávesa | Akce |
|---------|------|
| ← → | Pohyb |
| Mezerník | Skok |
| Z | Střelba |
| F1 | Nápověda (v03) |
| F5 / F9 | Uložit / načíst (v03) |
| E | Otevřít level editor (v03) |

## Ovládání (v04 – terminál)

| Klávesa | Akce |
|---------|------|
| A / D nebo ← → | Pohyb |
| W nebo ↑ | Skok |
| Mezerník | Střelba |
| S | Uložit |
| Q | Ukončit |

## Python koncepty demonstrované v projektu

- **v01** – třídy, dědičnost, pygame game loop
- **v02** – moduly, pytest, `pyproject.toml`
- **v03** – JSON serializace, dataclasses, procedurální generování, vzor editor
- **v04** – `curses`, `StrEnum`, `@dataclass`, `pathlib`, `random.Random(seed)`

## Struktura projektu

```
game_python_red_monster/
├── game_mosta_v01/        # pygame, základní hra
├── game_mosta_v02/        # testy, balíčková struktura
├── game_mosta_v03/        # plná hra s editorem a procgenem
├── game_mosta_v04_terminal/  # curses verze, stdlib-only
├── scripts/               # pomocné skripty
└── chat_history/          # záznamy konverzací s AI
```
