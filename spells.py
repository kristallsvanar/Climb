"""Everything the Caster can create, plus the Spell classes themselves."""
import math
import pygame
from settings import *
import assets


# ------------------------------------------------------------------ things that exist in the world
class Projectile:
    """A flying block. Used by the Caster's projectile spell AND by dart traps."""

    def __init__(self, x, y, w, h, vx, vy, name):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.vx, self.vy, self.name = vx, vy, name
        self.alive, self.age = True, 0.0

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def update(self, dt, level):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        if self.age > 6 or level.is_solid(self.x, self.y, self.w, self.h):
            self.alive = False

    def draw(self, surface, cam):
        assets.draw_block(surface, self.name, self.rect.move(0, -cam))


class MovingSpike:
    """Sweeps left <-> right across the castle. Placed on a wall, disappears after a while."""
    SIZE = 32

    def __init__(self, y, side):
        self.w = self.h = self.SIZE
        self.y = y
        self.x = LEFT_X if side == "left" else RIGHT_X - self.w
        self.dir = 1 if side == "left" else -1
        self.life = SPIKE_LIFETIME

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.x += self.dir * SPIKE_SPEED * dt
        if self.x <= LEFT_X:
            self.x, self.dir = LEFT_X, 1
        elif self.x + self.w >= RIGHT_X:
            self.x, self.dir = RIGHT_X - self.w, -1
        self.life -= dt

    def draw(self, surface, cam):
        assets.draw_block(surface, "moving_spike", self.rect.move(0, -cam))


class BlindBurst:
    """Visual ring for the blindness spell."""
    DURATION = 0.4

    def __init__(self, x, y):
        self.x, self.y, self.t = x, y, self.DURATION

    @property
    def alive(self):
        return self.t > 0

    def update(self, dt):
        self.t -= dt

    def draw(self, surface, cam):
        width = 3 + int(8 * self.t / self.DURATION)
        pygame.draw.circle(surface, (210, 210, 255), (int(self.x), int(self.y) - cam), BLIND_RADIUS, width)


# ------------------------------------------------------------------ the spells
class Spell:
    name = "Spell"

    def is_valid(self, world, pos):
        """pos is in WORLD coordinates. Return False if the spell can't be placed there."""
        return True

    def cast(self, world, pos):
        raise NotImplementedError

    def draw_preview(self, surface, world, mouse):
        """Optional aiming help drawn in SCREEN coordinates."""


class ProjectileSpell(Spell):
    name = "Projectile"
    SIZE = 22

    def cast(self, world, pos):
        ox, oy = world.orb_pos
        dx, dy = pos[0] - ox, pos[1] - oy
        dist = math.hypot(dx, dy) or 1
        s = self.SIZE
        world.projectiles.append(Projectile(ox - s / 2, oy - s / 2, s, s,
                                            dx / dist * PROJECTILE_SPEED, dy / dist * PROJECTILE_SPEED,
                                            "projectile"))

    def draw_preview(self, surface, world, mouse):
        pygame.draw.line(surface, COLORS["projectile"], world.ORB_SCREEN, mouse, 1)


class BlindnessSpell(Spell):
    name = "Blindness"

    def cast(self, world, pos):
        world.bursts.append(BlindBurst(*pos))
        r = world.runner
        if math.hypot(r.cx - pos[0], r.cy - pos[1]) <= BLIND_RADIUS:
            r.blind = BLIND_TIME

    def draw_preview(self, surface, world, mouse):
        pygame.draw.circle(surface, (210, 210, 255), mouse, BLIND_RADIUS, 1)


class SpikeSpell(Spell):
    name = "Moving Spike"

    def is_valid(self, world, pos):
        return pos[0] < LEFT_X or pos[0] > RIGHT_X            # walls only, never the middle

    def cast(self, world, pos):
        side = "left" if pos[0] < LEFT_X else "right"
        y = int(pos[1] // TILE) * TILE + (TILE - MovingSpike.SIZE) / 2
        world.spikes.append(MovingSpike(y, side))

    def draw_preview(self, surface, world, mouse):
        for rect in ((0, 0, LEFT_X, SCREEN_H - HUD_H), (RIGHT_X, 0, LEFT_X, SCREEN_H - HUD_H)):
            pygame.draw.rect(surface, (255, 200, 60), rect, 2)      # highlights where it's allowed
        if mouse[0] < LEFT_X or mouse[0] > RIGHT_X:
            y = int(mouse[1] // TILE) * TILE
            x = 0 if mouse[0] < LEFT_X else RIGHT_X
            pygame.draw.rect(surface, COLORS["moving_spike"], (x, y, LEFT_X, TILE), 2)
