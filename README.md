# Red Monster – Journey of Mosta

Learning Python projekt — platformová střílečka budovaná postupně ve čtyřech verzích. Každá verze přidává nové herní funkce a demonstruje jiné koncepty Pythonu.

## Příběh

Mosta, červené monstrum, se probouzí v Domácí Louce a musí projít kouzlenou zemí až na Sopečný vrchol. Po cestě potkává nepřátele, sbírá předměty a na konci ho čeká souboj s bossem. Svět tvoří mřížka 3×3 biomů:

```
(0,0) Zasněžené vrcholy  (1,0) Kamenný hřeben  (2,0) Sopečný vrchol [CÍL]
(0,1) Starý les          (1,1) Křižovatka       (2,1) Hluboká jeskyně
(0,2) Bahnité mokřady    (1,2) Domácí louka     (2,2) Písečné duny
                              [START]
```

## Verze

### v01 – Základní pygame hra
**Složka:** `game_mosta_v01/`

První verze: jednoduchá platformovka s ručně navrženými levely.

**Co obsahuje:**
- Hráč se pohybuje, skáče a střílí projektily
- Tři typy nepřátel: hlídka (přechází po platformě), pronásledovatel (jde za hráčem), skokán
- Přechod do dalšího levelu přes portál
- Obrazovky: uvítací, herní, game over, vítězství

**Python koncepty:**
- Třídy a dědičnost — `PhysicsBody` mixin pro gravitaci a kolize
- OOP návrh — `Platform`, `Player`, `Enemy`, `Portal`, `Projectile`
- Pygame game loop — zpracování událostí, update, render
- Stavový automat — přepínání obrazovek

**Spuštění:**
```bash
cd game_mosta_v01
pip install pygame
python main.py
```

**Ovládání:**
| Klávesa | Akce |
|---------|------|
| ← → | Pohyb |
| Mezerník / W | Skok |
| F | Střelba |
| R | Restart (game over) |
| ESC | Ukončit |

---

### v02 – Testy, moduly, strukturovaný kód
**Složka:** `game_mosta_v02/`

Refaktoring na modulární architekturu, přidány testy a typový systém.

**Co přibylo:**
- Propojený svět 3×3 — hráč přechází mezi oblastmi okrajem obrazovky
- Minimap v HUD — zobrazuje navštívené oblasti
- Pytest testy pro entity a navigaci světem
- `pyproject.toml` a správa závislostí přes `uv`

**Python koncepty:**
- `typing.Final` — konstanty označené jako neměnné
- `enum.Enum` / `StrEnum` — typově bezpečné stavy a směry
- `typing.NamedTuple` — neměnné záznamy (`BiomePalette`)
- `match` / `case` (Python 3.10+) — pattern matching na enumy
- pytest fixtures — `@pytest.fixture` pro sdílené nastavení testů
- `@pytest.mark.parametrize` — testování více případů najednou

**Spuštění:**
```bash
cd game_mosta_v02
uv sync
uv run mosta
```

**Testy:**
```bash
uv run pytest
```
- `test_entities.py` — AI strategie, fyzika hráče, kolize platforem
- `test_world.py` — spawning oblastí, navigace, sousedé

---

### v03 – Plná hra: předměty, boss, uložení, procgen, editor
**Složka:** `game_mosta_v03/`

Nejkomplexnější pygame verze se všemi herními systémy.

**Co přibylo:**
- **Inventář a předměty** — lektvary (léčí 1 HP), zrychlení (2×), silný skok
- **Boss fight** — boss se 3 fázemi (klidný → lov → zuřivost), s HP barem
- **Save/Load** — uložení stavu do JSON, načtení při startu
- **Procedurální generování** — seeded random world (reprodukovatelný)
- **Level editor** — nástroj pro navrhování vlastních oblastí
- **Rozšířený HUD** — nápověda, inventář, HP bar bossse, notifikace uložení

**Python koncepty:**
- `@dataclass` se `slots=True` — paměťově efektivní záznamy
- `collections.Counter` — počítání předmětů v inventáři
- Přetížení operátorů — `__contains__`, `__len__` na třídě `Inventory`
- `@classmethod` konstruktory — `Inventory.from_dict()` pro deserializaci
- `pathlib.Path` — práce se soubory
- `json` stdlib — serializace s ručním převodem (tuple↔list, set↔list)
- `typing.Protocol` — strukturální typing pro AI strategie
- Strategy pattern — `PatrolStrategy`, `ChaseStrategy`, `JumperStrategy`
- `@property` — computed atributy (`boss.phase`, `player.alive`)
- `functools.cache` — memoizace výpočtů
- `random.Random(seed)` — reprodukovatelná procedurální generace

**Spuštění:**
```bash
cd game_mosta_v03
uv sync
uv run mosta
```

**Ovládání:**
| Klávesa | Akce |
|---------|------|
| ← → | Pohyb |
| Mezerník / W | Skok |
| F | Střelba |
| 1 / 2 / 3 | Použít předmět (lektvar / zrychlení / skok) |
| S | Uložit hru |
| L | Načíst hru (z uvítací obrazovky) |
| H | Přepnout nápovědu |
| E | Otevřít level editor (uvítací obrazovka) |
| P | Přepnout procgen mód (uvítací obrazovka) |
| ESC | Ukončit |

**Testy:**
- `test_entities.py` — fyzika, AI, projektily
- `test_items.py` — `Inventory` add/use/count, serializace
- `test_boss.py` — poškození, fáze, rychlost podle profilu
- `test_save.py` — round-trip save/load, version checking, korupce
- `test_procgen.py` — determinismus seedu, generování oblastí
- `test_editor.py` — výběr entit, JSON export
- `test_world.py` — definice oblastí, konektivita světa

---

### v04 – Terminálová verze (curses, stdlib-only)
**Složka:** `game_mosta_v04_terminal/`

Stejná hra přepsaná do terminálu — **bez závislostí**, čistá stdlib.

**Co je jinak:**
- ASCII grafika: `@` hráč, `P`/`C`/`J` nepřátelé, `$` boss, `#` oltář, `o` lektvar
- Mřížka 60×18 buněk místo pixelů
- Tick-based game loop s `curses.nodelay`
- Jeden soubor (`game.py`) pro snadné čtení a experimentování
- Stejný herní svět, mechaniky, boss, předměty a save/load jako v03

**Python koncepty:**
- `curses` — terminálové UI (stdlib!)
- `@dataclass` — záznamy stavu entit
- `enum.StrEnum` — typy dlaždic a předmětů jako znaky
- `pathlib.Path` + `json` — save/load soubor vedle skriptu
- `random.Random(seed)` — stejný procgen jako v03

**Spuštění:**
```bash
cd game_mosta_v04_terminal
python3 game.py
```

**Ovládání:**
| Klávesa | Akce |
|---------|------|
| A / D nebo ← → | Pohyb |
| W nebo ↑ | Skok |
| Mezerník | Skok (alternativa) |
| F | Střelba |
| 1 / 2 / 3 | Použít předmět |
| S | Uložit |
| L | Načíst |
| H | Nápověda |
| Q / ESC | Ukončit |

**Testy:**
- `test_game.py` — generování světa, fyzika, pohyb, předměty, boss fáze, save round-trip

---

## Přehled Python konceptů

| Koncept | v01 | v02 | v03 | v04 |
|---------|:---:|:---:|:---:|:---:|
| Třídy, dědičnost, mixin | ✓ | ✓ | ✓ | – |
| Pygame game loop | ✓ | ✓ | ✓ | – |
| `typing.Final` | – | ✓ | ✓ | ✓ |
| `enum.Enum` / `StrEnum` | – | ✓ | ✓ | ✓ |
| `typing.NamedTuple` | – | ✓ | ✓ | – |
| `match` / `case` | – | ✓ | ✓ | ✓ |
| `@dataclass` | – | – | ✓ | ✓ |
| `@dataclass(slots=True)` | – | – | ✓ | – |
| `typing.Protocol` | – | – | ✓ | – |
| Strategy pattern | – | – | ✓ | – |
| `@property`, `@classmethod` | – | – | ✓ | – |
| `functools.cache` | – | – | ✓ | – |
| `collections.Counter` | – | – | ✓ | – |
| Přetížení operátorů | – | – | ✓ | – |
| `pathlib.Path` + `json` | – | – | ✓ | ✓ |
| `random.Random(seed)` | – | – | ✓ | ✓ |
| `curses` (stdlib TUI) | – | – | – | ✓ |
| pytest, fixtures, parametrize | – | ✓ | ✓ | ✓ |

## Struktura projektu

```
game_python_red_monster/
├── game_mosta_v01/
│   ├── main.py          # game loop, stavový automat
│   ├── entities.py      # Player, Enemy, Platform, Portal, Projectile
│   ├── constants.py     # barvy, fyzikální konstanty
│   ├── sprites.py       # načítání a kreslení spritů
│   ├── hud.py           # overlay obrazovky
│   ├── levels.py        # definice levelů
│   └── mosta.png
│
├── game_mosta_v02/
│   ├── main.py
│   ├── entities.py      # PhysicsBody, AI strategie
│   ├── world.py         # mřížka 3×3, Direction enum, navigace
│   ├── constants.py     # GameState, AiType, BiomePalette
│   ├── hud.py           # minimap
│   ├── tests/
│   └── mosta.png
│
├── game_mosta_v03/
│   ├── main.py
│   ├── entities.py      # Player s HP/inventářem, Boss
│   ├── items.py         # Inventory, Item pickups
│   ├── world.py         # spawning, přechody oblastí
│   ├── procgen.py       # seeded procedurální generování
│   ├── save.py          # JSON save/load, version checking
│   ├── editor.py        # standalone level editor
│   ├── hud.py           # inventář, HP bar, nápověda, toast
│   ├── tests/
│   └── mosta.png
│
├── game_mosta_v04_terminal/
│   ├── game.py          # celá hra v jednom souboru
│   └── tests/
│
├── scripts/
├── chat_history/
└── README.md
```
