"""Built-in castle traps."""
import pygame
from settings import *
from spells import Projectile
import assets


class DartTrap:
    """A block in the wall that shoots a dart across the castle every few seconds.
    It flashes just before firing. The runner can block darts with the shield."""
    W, H = 18, 10

    def __init__(self, col, row, direction, offset):
        self.x, self.y = col * TILE, row * TILE
        self.dir = direction                  # +1 shoots right, -1 shoots left
        self.timer = offset

    @property
    def charging(self):
        return self.timer > DART_INTERVAL - 0.6

    def update(self, dt, world):
        self.timer += dt
        if self.timer >= DART_INTERVAL:
            self.timer -= DART_INTERVAL
            x = LEFT_X if self.dir > 0 else RIGHT_X - self.W
            world.projectiles.append(
                Projectile(x, self.y + 15, self.W, self.H, self.dir * DART_SPEED, 0, "dart_shot"))

    def draw(self, surface, cam):
        if self.charging:
            x = self.x + TILE - 8 if self.dir > 0 else self.x
            rect = pygame.Rect(x, self.y + 14 - cam, 8, 12)
            assets.draw_block(surface, "dart_shot", rect)
