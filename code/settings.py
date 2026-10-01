"""Every tweakable number and colour lives here.

All pixel values below are tuned for TILE_SIZE = 16 (they are the old 40px-tile values x 0.4,
so jumps are still ~4 blocks high, bounce pads ~8 blocks, etc.).
"""
import sys
import pygame
from pygame.math import Vector2 as vector

# ---------- screen / grid ----------
TILE_SIZE = 16
WINDOW_WIDTH, WINDOW_HEIGHT = 480, 270      # logical size, the window is scaled up (pygame.SCALED)
HUD_H = 28                                  # caster bar at the bottom
VIEW_H = WINDOW_HEIGHT - HUD_H              # part of the screen that shows the castle
FPS = 60
ANIMATION_SPEED = 6

# ---------- draw order ----------
Z_LAYERS = {
    'bg': 0, 'clouds': 1, 'bg tiles': 2, 'path': 3, 'bg details': 4,
    'main': 5, 'water': 6, 'fg': 7,
}
# z of each Tiled tile layer (by lower-case layer name). Unknown layers are drawn as 'bg details'.
LAYER_Z = {
    'terrain': Z_LAYERS['main'], 'platforms': Z_LAYERS['main'], 'bounce': Z_LAYERS['main'],
    'goal': Z_LAYERS['main'], 'spike': Z_LAYERS['bg details'], 'spike inverted': Z_LAYERS['bg details'],
    'wallpaper': Z_LAYERS['bg tiles'], 'background': Z_LAYERS['path'], 'props': Z_LAYERS['bg'],
    'water': Z_LAYERS['water'], 'foreground': Z_LAYERS['fg'], 'fg': Z_LAYERS['fg'],
}

# ---------- maps (files live in ../data/levels) ----------
LEVELS = [("The Cramped Castle", "castle_1.tmx")]
# ---------- sizes used when a Tiled object has no size of its own ----------
RUNNER_SIZE = (12, 14)
PICKUP_SIZE = (10, 10)
ORB_SIZE = 16

# ---------- old-style moving platforms (Tiled "path rectangles": Small obj, Med obj, Big obj, Elevator) ----------
# The platform's size is read from graphics/objects/<name>.png (e.g. "small obj.png").
# PATH_PLATFORMS is only the fallback size (w, h) used when that PNG is missing.
PATH_PLATFORMS = {
    "small obj": (32, 8),
    "med obj": (48, 8),
    "big obj": (48, 8),
    "elevator": (48, 8),
}
PATH_SOLID = True       # True = solid like the old game, False = one-way (jump up through)
PATH_SCALE = 1.0        # scales platform size AND speed (use 16 / old_tile_size if the old art was for bigger tiles)

# ---------- runner physics (pixels / second) ----------
GRAVITY = 800
MAX_FALL = 360
JUMP_V = 320                # ~4 blocks high
BOUNCE_V = 460              # ~8 blocks high
RUN_SPEED = 96
BOOST_SPEED = 136
BOOST_TIME = 6.0
MAX_HEARTS = 3
INVULN_TIME = 1.5           # seconds of safety after being hit
KNOCKBACK = (168, -168)     # (sideways, upwards)
STUN_TIME = 0.3
SHIELD_TIME = 0.6           # how long the block-shield stays up
SHIELD_COOLDOWN = 2.5
SHIELD_RADIUS = 15
COYOTE = 0.08               # grace time to jump after leaving a ledge
JUMP_BUFFER = 0.12          # grace time for pressing jump slightly early

# ---------- caster ----------
MAX_SPELLS = 10
CAST_COOLDOWN = 0.6
PROJECTILE_SPEED = 168
PROJECTILE_SIZE = 8
BLIND_TIME = 0.8
BLIND_RADIUS = 48
SPIKE_SPEED = 68
SPIKE_SIZE = 14
SPIKE_LIFETIME = 9.0

# ---------- castle traps ----------
DART_INTERVAL = 3.2
DART_CHARGE = 0.6           # the trap flashes this long before firing
DART_SPEED = 96
DART_SIZE = (8, 4)

# ---------- colours (anything without a PNG in graphics/objects is drawn as a coloured block) ----------
COLORS = {
    "runner": (80, 160, 255), "projectile": (190, 90, 255), "dart_shot": (255, 150, 40),
    "dart": (150, 90, 50), "moving_spike": (255, 100, 30), "heart": (255, 90, 130),
    "heart_empty": (70, 60, 70), "speed": (255, 235, 60), "orb": (160, 90, 230),
    "goal": (255, 215, 0), "moving_platform": (110, 150, 190), "moving_block": (170, 120, 90),
    "bg": (24, 20, 34), "shield": (120, 230, 255),
}


def to_screen(rect, offset):
    """World rect (float or int) -> integer pygame.Rect on screen, given the camera offset."""
    return pygame.Rect(round(rect.x + offset[0]), round(rect.y + offset[1]), round(rect.w), round(rect.h))
