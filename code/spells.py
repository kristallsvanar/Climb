"""Everything the Caster can create, plus the Spell classes themselves.

Spell positions: `pos` is in WORLD coordinates, `mouse` (for previews) is in SCREEN coordinates.
"""
import math
from settings import *
from sprites import Sprite
import assets


# ------------------------------------------------------------------ things that exist in the world
class Projectile(Sprite):
    """A flying block. Used by the Caster's projectile spell AND by dart traps."""

    def __init__(self, pos, size, velocity, name, groups, through_walls=False):
        super().__init__(pos, assets.get(name, size), groups, Z_LAYERS['main'] + 0.4)
        self.velocity = vector(velocity)
        self.age = 0.0
        self.through_walls = through_walls                 # True = ignores terrain (caster's projectile)

    @property
    def cx(self):
        return self.rect.centerx

    @property
    def cy(self):
        return self.rect.centery

    def update(self, dt, level):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        self.age += dt
        if self.age > 6 or not level.in_bounds(self.rect) or (not self.through_walls and level.hits_solid(self.rect)):
            self.kill()


class MovingSpike(Sprite):
    """Sweeps left <-> right across the castle. Placed on a wall, disappears after a while."""

    def __init__(self, y, side, bounds, groups):
        x = bounds[0] if side == "left" else bounds[1] - SPIKE_SIZE
        super().__init__((x, y), assets.get("moving_spike", (SPIKE_SIZE, SPIKE_SIZE)), groups,
                         Z_LAYERS['main'] + 0.3)
        self.bounds = bounds
        self.dir = 1 if side == "left" else -1
        self.life = SPIKE_LIFETIME

    def update(self, dt):
        self.rect.x += self.dir * SPIKE_SPEED * dt
        lo, hi = self.bounds
        if self.rect.left <= lo:
            self.rect.left, self.dir = lo, 1
        elif self.rect.right >= hi:
            self.rect.right, self.dir = hi, -1
        self.life -= dt
        if self.life <= 0:
            self.kill()


class BlindBurst(pygame.sprite.Sprite):
    """Visual ring for the blindness spell."""
    DURATION = 0.4

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.pos, self.t = pos, self.DURATION
        self.z = Z_LAYERS['fg']

    def update(self, dt):
        self.t -= dt
        if self.t <= 0:
            self.kill()

    def draw(self, surface, offset):
        width = 1 + int(4 * self.t / self.DURATION)
        center = (round(self.pos[0] + offset[0]), round(self.pos[1] + offset[1]))
        pygame.draw.circle(surface, (210, 210, 255), center, BLIND_RADIUS, width)


# ------------------------------------------------------------------ the spells
class Spell:
    name = "Spell"

    def is_valid(self, level, pos):
        """Return False if the spell can't be placed at this world position."""
        return True

    def cast(self, level, pos):
        raise NotImplementedError

    def draw_preview(self, surface, level, mouse):
        """Optional aiming help drawn in SCREEN coordinates."""


class ProjectileSpell(Spell):
    name = "Projectile"

    def cast(self, level, pos):
        ox, oy = level.orb_pos
        dx, dy = pos[0] - ox, pos[1] - oy
        dist = math.hypot(dx, dy) or 1
        s = PROJECTILE_SIZE
        Projectile((ox - s / 2, oy - s / 2), (s, s),
                   (dx / dist * PROJECTILE_SPEED, dy / dist * PROJECTILE_SPEED), "projectile",
                   (level.all_sprites, level.projectile_sprites), through_walls=True)

    def draw_preview(self, surface, level, mouse):
        pygame.draw.line(surface, COLORS["projectile"], level.ORB_SCREEN, mouse, 1)


class BlindnessSpell(Spell):
    name = "Blindness"

    def cast(self, level, pos):
        BlindBurst(pos, (level.all_sprites, level.effect_sprites))
        r = level.runner
        if math.hypot(r.cx - pos[0], r.cy - pos[1]) <= BLIND_RADIUS:
            r.blind = BLIND_TIME

    def draw_preview(self, surface, level, mouse):
        pygame.draw.circle(surface, (210, 210, 255), mouse, BLIND_RADIUS, 1)


class SpikeSpell(Spell):
    """Only works inside the 'SpikeZone' rectangles of the map (the castle walls)."""
    name = "Moving Spike"

    @staticmethod
    def _side(level, pos):
        for side, zone in level.spike_zones:
            if zone.collidepoint(pos):
                return side
        return None

    def is_valid(self, level, pos):
        return level.spike_bounds is not None and self._side(level, pos) is not None

    def cast(self, level, pos):
        y = int(pos[1] // TILE_SIZE) * TILE_SIZE + (TILE_SIZE - SPIKE_SIZE) / 2
        MovingSpike(y, self._side(level, pos), level.spike_bounds, (level.all_sprites, level.spike_sprites))

    def draw_preview(self, surface, level, mouse):
        off = level.all_sprites.draw_offset
        for _, zone in level.spike_zones:
            pygame.draw.rect(surface, (255, 200, 60), to_screen(zone, off), 1)      # where it's allowed
        world = level.to_world(mouse)
        side = self._side(level, world)
        if side and level.spike_bounds is not None:
            row_y = int(world[1] // TILE_SIZE) * TILE_SIZE + off[1]
            zone = next(z for s, z in level.spike_zones if s == side and z.collidepoint(world))
            zr = to_screen(zone, off)
            pygame.draw.rect(surface, COLORS["moving_spike"], (zr.x, row_y, zr.w, TILE_SIZE), 1)
