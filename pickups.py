"""Power-ups lying around the castle."""
import math
import random
import pygame
from settings import TILE
import assets


class Pickup:
    def __init__(self, kind, col, row):
        self.kind = kind                                   # "speed" or "heart"
        self.rect = pygame.Rect(col * TILE + 8, row * TILE + 14, 24, 24)
        self.t = random.random() * 6

    def update(self, dt):
        self.t += dt

    def draw(self, surface, cam):
        bob = int(math.sin(self.t * 4) * 3)
        assets.draw_block(surface, self.kind, self.rect.move(0, -cam + bob))
