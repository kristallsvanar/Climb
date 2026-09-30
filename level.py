"""The castle: builds tiles from map data, checks every jump is possible, and handles collisions."""
import math
import random
import pygame
from settings import *
from traps import DartTrap
from pickups import Pickup
import assets

SOLID = {"wall", "dart"}            # blocks that stop you from every side
ONE_WAY = {"stone", "bounce"}       # ledges: you land on top, but can jump up through them
MARGIN = 30                         # safety margin (px) used by the jump checker


class Tile:
    def __init__(self, kind, col, row):
        self.kind, self.col, self.row = kind, col, row
        self.x, self.y = col * TILE, row * TILE
        self.solid = kind in SOLID
        self.one_way = kind in ONE_WAY

    @property
    def hazard_rect(self):
        """Spikes only hurt on their sharp part (the visible red block)."""
        return pygame.Rect(self.x + 6, self.y + 16, TILE - 12, TILE - 16)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE, TILE)

    def draw(self, surface, cam):
        rect = self.hazard_rect if self.kind == "spike" else self.rect
        assets.draw_block(surface, self.kind, rect.move(0, -cam))


class Platform:
    def __init__(self, level, col, pattern, dart=None):
        self.level, self.col, self.pattern, self.dart = level, col, pattern, dart
        self.x0, self.x1 = col, col + len(pattern)

    @property
    def pads(self):
        return [self.col + i for i, ch in enumerate(self.pattern) if ch == "B"]


def _reach(v, rise):
    """Horizontal pixels a runner covers while jumping `rise` blocks up with launch speed v."""
    disc = v * v - 2 * GRAVITY * rise * TILE
    return -1 if disc < 0 else RUN_SPEED * (v + math.sqrt(disc)) / GRAVITY


class Level:
    def __init__(self, data, rng=None):
        rng = rng or random.Random()
        self.name = data["name"]
        self.platforms = [Platform(0, WALL_COLS, "=" * (COLS - 2 * WALL_COLS))]     # the ground
        height = 0
        for rise, col, pattern, *dart in data["platforms"]:
            height += rise
            self.platforms.append(Platform(height, col, pattern, dart[0] if dart else None))
        self.validate()
        self.rows = height + 8
        self.height = self.rows * TILE
        self.ground_y = self.row_of(0) * TILE
        self.goal_y = self.row_of(height) * TILE
        self.tiles, self.darts, self.pickups = {}, [], []
        self._build_tiles(rng)
        self._spawn_pickups(data, rng)

    def row_of(self, level):
        return self.rows - 2 - level

    # ------------------------------------------------------------------ building
    def _put(self, kind, col, row):
        self.tiles[(col, row)] = Tile(kind, col, row)

    def _build_tiles(self, rng):
        for r in range(self.rows):
            for c in range(COLS):
                if c < WALL_COLS or c >= COLS - WALL_COLS or r == 0 or r >= self.rows - 2:
                    self._put("wall", c, r)
        for p in self.platforms[1:]:
            row = self.row_of(p.level)
            for i, ch in enumerate(p.pattern):
                self._put("bounce" if ch == "B" else "stone", p.col + i, row)
                if ch == "^":
                    self._put("spike", p.col + i, row - 1)
            if p.dart:
                col = WALL_COLS - 1 if p.dart == "L" else COLS - WALL_COLS
                self._put("dart", col, row - 1)
                self.darts.append(DartTrap(col, row - 1, 1 if p.dart == "L" else -1,
                                           rng.uniform(0, DART_INTERVAL)))
        row = self.row_of(self.platforms[-1].level)
        for c in (9, 10):                               # golden goal block above the last ledge
            for r in (row - 1, row - 2):
                self._put("goal", c, r)

    def _spawn_pickups(self, data, rng):
        groups = []                                     # one list of free spots per normal platform
        for p in self.platforms[1:-1]:
            if len(p.pattern) == len(self.platforms[0].pattern):
                continue                                # skip the full-width rest ledges
            row = self.row_of(p.level)
            groups.append([(p.col + i, row - 1) for i, ch in enumerate(p.pattern) if ch == "="])
        groups = [g for g in groups if g]
        n = data["speed_boosts"]
        size = len(groups) / n
        for k in range(n):                              # spread the boosts evenly, positions random
            spot = rng.choice(rng.choice(groups[int(k * size):int((k + 1) * size)]))
            self.pickups.append(Pickup("speed", *spot))
        for _ in range(data["hearts"]):
            spot = rng.choice(rng.choice(groups[len(groups) // 5:]))
            self.pickups.append(Pickup("heart", *spot))

    # ------------------------------------------------------------------ jump checker
    def validate(self):
        normal_max = JUMP_V ** 2 / (2 * GRAVITY) - MARGIN
        bounce_max = BOUNCE_V ** 2 / (2 * GRAVITY) - 40
        for i in range(1, len(self.platforms)):
            a, b = self.platforms[i - 1], self.platforms[i]
            name = f"Platform #{i} (level {b.level}, column {b.col})"
            rise = b.level - a.level
            if b.col < WALL_COLS or b.x1 > COLS - WALL_COLS:
                raise ValueError(f"{name} sticks into a wall")
            if not 0 <= rise <= 7:
                raise ValueError(f"{name}: rise {rise} must be 0..7")
            if "^^^" in b.pattern or "^" in b.pattern[:2] or "^" in b.pattern[-2:]:
                raise ValueError(f"{name}: spikes need 2 safe blocks at each end and max 2 in a row")

            def gap(x0, x1):                            # empty pixels between two column ranges
                return max(0, b.x0 - x1, x0 - b.x1) * TILE

            ok = (rise * TILE <= normal_max and gap(a.x0, a.x1) <= _reach(JUMP_V, rise) - MARGIN)
            for pad in a.pads:                          # a bouncy block gives a much bigger jump
                if rise * TILE <= bounce_max and gap(pad, pad + 1) <= _reach(BOUNCE_V, rise) - MARGIN:
                    ok = True
            if not ok:
                raise ValueError(f"{name} cannot be reached from the previous platform")

    # ------------------------------------------------------------------ collisions
    def tiles_in(self, x, y, w, h):
        for r in range(int(y // TILE), int((y + h - 0.001) // TILE) + 1):
            for c in range(int(x // TILE), int((x + w - 0.001) // TILE) + 1):
                tile = self.tiles.get((c, r))
                if tile:
                    yield tile

    def is_solid(self, x, y, w, h):
        if x < 0 or y < 0 or x + w > COLS * TILE or y + h > self.height:
            return True
        return any(t.solid for t in self.tiles_in(x, y, w, h))

    def move_body(self, b, dt):
        """Moves anything with x, y, w, h, vx, vy. Sets b.on_ground and b.bounced."""
        b.on_ground = b.bounced = False

        # --- X pass ---
        b.x += b.vx * dt
        # Find the nearest solid tile and stop at it. We pick the closest face
        # so that multi-column walls (WALL_COLS > 1) don't push the player through
        # to the far side of the wall.
        if b.vx > 0:
            blocker = None
            for t in self.tiles_in(b.x, b.y, b.w, b.h):
                if t.solid and (blocker is None or t.x < blocker.x):
                    blocker = t
            if blocker is not None:
                b.x = blocker.x - b.w
                b.vx = 0
        elif b.vx < 0:
            blocker = None
            for t in self.tiles_in(b.x, b.y, b.w, b.h):
                if t.solid and (blocker is None or t.x > blocker.x):
                    blocker = t
            if blocker is not None:
                b.x = blocker.x + TILE
                b.vx = 0

        # --- Y pass ---
        prev_bottom = b.y + b.h
        b.y += b.vy * dt
        landing = None
        for t in self.tiles_in(b.x, b.y, b.w, b.h):
            if t.solid:
                if b.vy > 0:
                    b.y, b.vy, b.on_ground = t.y - b.h, 0, True
                elif b.vy < 0:
                    b.y, b.vy = t.y + TILE, 0
                break   # one solid tile is enough; stop so we don't double-resolve
            elif t.one_way and b.vy >= 0 and prev_bottom <= t.y + 1 and b.y + b.h > t.y:
                if landing is None or t.kind == "bounce":
                    landing = t
        if landing:
            b.y = landing.y - b.h
            if landing.kind == "bounce":
                b.vy, b.bounced = -BOUNCE_V, True
            else:
                b.vy, b.on_ground = 0, True

    # ------------------------------------------------------------------ drawing
    def draw(self, surface, cam):
        surface.fill(COLORS["bg"])
        pygame.draw.rect(surface, COLORS["room"], (LEFT_X, 0, RIGHT_X - LEFT_X, SCREEN_H))
        for r in range(cam // TILE, (cam + SCREEN_H) // TILE + 1):
            for c in range(COLS):
                tile = self.tiles.get((c, r))
                if tile:
                    tile.draw(surface, cam)
