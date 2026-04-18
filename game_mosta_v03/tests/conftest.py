import os
import sys
import pathlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
