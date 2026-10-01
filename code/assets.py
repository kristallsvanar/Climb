"""Draws every object that does not come from a Tiled tile layer.

If graphics/objects/<name>.png exists it is used (scaled to the size of the Tiled object),
otherwise a coloured block is drawn. Adding art later = drop a PNG in graphics/objects.
"""
import os
import pygame
from settings import COLORS

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphics", "objects")
_cache = {}


def _shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def get(name, size):
    size = (max(1, int(size[0])), max(1, int(size[1])))
    key = (name, size)
    if key not in _cache:
        path = os.path.join(ASSET_DIR, name + ".png")
        if os.path.exists(path):
            _cache[key] = pygame.transform.scale(pygame.image.load(path).convert_alpha(), size)
        else:
            color = COLORS.get(name, (255, 0, 255))
            surf = pygame.Surface(size)
            surf.fill(color)
            pygame.draw.rect(surf, _shade(color, 0.6), surf.get_rect(), 1 if min(size) < 12 else 2)
            _cache[key] = surf
    return _cache[key]


def draw_block(surface, name, rect):
    surface.blit(get(name, (rect.w, rect.h)), (int(rect.x), int(rect.y)))


def natural_size(name):
    """Size of graphics/objects/<name>.png, or None if there is no such file."""
    path = os.path.join(ASSET_DIR, name + ".png")
    return pygame.image.load(path).get_size() if os.path.exists(path) else None
