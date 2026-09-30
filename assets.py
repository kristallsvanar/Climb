"""Draws every object.

If assets/<name>.png exists it is used as the sprite, otherwise a coloured block is drawn.
So adding art later = just drop a PNG in the assets folder. No code changes needed.
"""
import os
import pygame
from settings import COLORS

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_cache = {}


def _shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def get(name, size):
    key = (name, size)
    if key not in _cache:
        path = os.path.join(ASSET_DIR, name + ".png")
        if os.path.exists(path):
            _cache[key] = pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
        else:
            color = COLORS.get(name, (255, 0, 255))
            surf = pygame.Surface(size)
            surf.fill(color)
            pygame.draw.rect(surf, _shade(color, 0.6), surf.get_rect(), 2)
            pygame.draw.line(surf, _shade(color, 1.25), (2, 2), (size[0] - 3, 2))
            _cache[key] = surf
    return _cache[key]


def draw_block(surface, name, rect):
    size = (max(1, int(rect.w)), max(1, int(rect.h)))
    surface.blit(get(name, size), (int(rect.x), int(rect.y)))
