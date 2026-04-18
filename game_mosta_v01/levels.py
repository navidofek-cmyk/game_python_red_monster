import random
from constants import SCREEN_H

LEVEL_DEFS = [
    {   # Level 1 – intro
        "bg": (20, 20, 35),
        "enemy_count": 3,
        "speed_bonus": 0.0,
        "platforms": [
            (0,   570, 800),
            (50,  460, 180), (300, 460, 200), (580, 460, 180),
            (130, 350, 160), (380, 340, 220), (660, 355, 120),
            (20,  230, 140), (250, 220, 200), (530, 235, 150), (720, 230, 80),
        ],
    },
    {   # Level 2 – narrow bridges
        "bg": (15, 30, 25),
        "enemy_count": 4,
        "speed_bonus": 0.3,
        "platforms": [
            (0,   570, 800),
            (0,   460, 120), (250, 460, 100), (500, 460, 120), (680, 460, 120),
            (80,  360, 80),  (300, 355, 90),  (520, 350, 80),  (700, 360, 100),
            (0,   250, 100), (200, 240, 120), (420, 245, 80),  (620, 240, 140),
            (300, 140, 200),
        ],
    },
    {   # Level 3 – stairs right
        "bg": (30, 15, 30),
        "enemy_count": 5,
        "speed_bonus": 0.6,
        "platforms": [
            (0,   570, 800),
            (0,   490, 160), (160, 430, 160), (320, 370, 160),
            (480, 310, 160), (640, 250, 160),
            (0,   250, 120), (160, 330, 100),
            (350, 180, 200),
        ],
    },
    {   # Level 4 – floating islands
        "bg": (10, 20, 40),
        "enemy_count": 6,
        "speed_bonus": 1.0,
        "platforms": [
            (0,   570, 800),
            (60,  490, 100), (220, 440, 100), (380, 490, 100),
            (540, 430, 100), (680, 480, 120),
            (100, 360, 80),  (310, 320, 90),  (530, 355, 80),
            (200, 230, 100), (450, 210, 100), (670, 240, 100),
            (320, 120, 160),
        ],
    },
    {   # Level 5 – chaos
        "bg": (35, 10, 10),
        "enemy_count": 8,
        "speed_bonus": 1.5,
        "platforms": [
            (0,   570, 800),
            (30,  500, 70),  (160, 480, 70),  (290, 510, 70),  (420, 490, 70),
            (550, 505, 70),  (680, 480, 70),
            (60,  400, 60),  (200, 380, 60),  (360, 400, 60),  (500, 375, 60),
            (640, 395, 60),
            (100, 290, 80),  (280, 270, 80),  (460, 285, 80),  (640, 265, 80),
            (200, 175, 100), (450, 160, 100), (680, 175, 100),
            (330, 80,  140),
        ],
    },
]


def spawn_level(level_idx, Platform, Player, Enemy, Portal):
    defn      = LEVEL_DEFS[min(level_idx, len(LEVEL_DEFS) - 1)]
    platforms = [Platform(*p) for p in defn["platforms"]]
    player    = Player(80, SCREEN_H - 60)
    speed     = 1.5 + defn["speed_bonus"]
    enemies   = [Enemy(random.randint(300, 760), SCREEN_H - 60, speed)
                 for _ in range(defn["enemy_count"])]
    top_plat  = min(platforms, key=lambda p: p.rect.top)
    portal    = Portal(top_plat.rect.centerx, top_plat.rect.top)
    return platforms, player, enemies, portal, defn["bg"]
