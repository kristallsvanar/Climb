"""The castle: loads a Tiled map, builds collision from it, spawns its objects and runs the rules.

HOW TO MAKE A MAP IN TILED  (tile size 16x16, any map size, orthogonal, CSV/base64 layers both fine)

Tile layers (matched by name, case-insensitive):
  Terrain         solid blocks (walls, floors) - stops you from every side
  Platforms       one-way ledges: you land on top, but can jump up through them
  Bounce          one-way bouncy blocks
  Spike           spikes standing on a surface (hurt only on their sharp part)
  Spike Inverted  spikes hanging from a ceiling
  Goal            optional: touching any tile here wins the match for the runner
  wallpaper / background / props / foreground ... purely decorative (see LAYER_Z in settings.py)
  Any other name is decoration drawn behind the runner.

Objects (rectangle objects, any object layer, matched by the object's NAME):
  Player          runner spawn. The rectangle is the runner's size (a 12x14 box is a good start)
  Goal            rectangle that wins the match when touched. Hide it in Tiled if you use tile art
  DartTrap        solid block that fires darts. property  dir = "right" | "left"
                  (place it so the muzzle side faces open air, the dart starts right next to it)
  Speed, Heart    pickups. The rectangle is the pickup's size
  SpikeZone       where the caster may place Moving Spikes (the castle walls).
                  property  side = "left" | "right"  (guessed from position if missing).
                  The spike sweeps between the inner edge of the left zone and the right zone.
  MovingPlatform  one-way platform. The rectangle is its size and start position.
                  properties  axis = "x" | "y",  distance (px, negative = go the other way first),  speed (px/s)
  MovingBlock     same, but solid from every side (it reverses instead of crushing the runner)
  Small obj, Med obj, Big obj, Elevator
                  old-style PATH rectangles: the rectangle is the route, not the platform.
                  Wider than tall = horizontal, taller than wide = vertical. property  speed.
                  The platform's size comes from graphics/objects/<name>.png (see PATH_* in settings.py)

Use plain rectangle objects, not "tile objects" (those have a different origin in Tiled).
"""
import math
import random
import pygame
import pytmx
from settings import *
from sprites import Sprite, Tile, TileLayer, MovingSprite, SpriteGrid
from groups import Allsprites
from runner import Runner
from traps import DartTrap
from pickups import Pickup
import assets


class Level:
    ORB_SCREEN = (WINDOW_WIDTH // 2, 14)                # the caster's floating orb (fixed on screen)

    def __init__(self, tmx_map, name="", rng=None):
        if (tmx_map.tilewidth, tmx_map.tileheight) != (TILE_SIZE, TILE_SIZE):
            raise ValueError(f"Map tiles are {tmx_map.tilewidth}x{tmx_map.tileheight}, expected {TILE_SIZE}x{TILE_SIZE}")
        self.name = name
        self.rng = rng or random.Random()
        self.width, self.height = tmx_map.width * TILE_SIZE, tmx_map.height * TILE_SIZE

        # groups
        self.all_sprites = Allsprites(self.width, self.height)
        self.projectile_sprites = pygame.sprite.Group()
        self.spike_sprites = pygame.sprite.Group()      # moving spikes made by the caster
        self.effect_sprites = pygame.sprite.Group()
        self.pickup_sprites = pygame.sprite.Group()
        self.moving_sprites, self.traps = [], []
        self.solids, self.semis, self.hazards = SpriteGrid(), SpriteGrid(), SpriteGrid()
        self.goal_rects, self.spike_zones = [], []
        self.spike_bounds = None                        # (left_x, right_x) a moving spike sweeps between
        self.runner = None
        self.winner = None                              # "runner" or "caster"

        self._load_tile_layers(tmx_map)
        self._load_objects(tmx_map)
        if self.runner is None:
            raise ValueError("The map needs a rectangle object named 'Player' (the runner's spawn)")
        lefts = [z.right for side, z in self.spike_zones if side == "left"]
        rights = [z.left for side, z in self.spike_zones if side == "right"]
        if lefts and rights:
            self.spike_bounds = (max(lefts), min(rights))
        else:
            print("[WARNING] No SpikeZone objects on both sides: the Moving Spike spell is disabled")

        self.start_bottom = self.runner.rect.bottom
        self.goal_top = min((g.top for g in self.goal_rects), default=0)
        self.all_sprites.snap(self.runner.rect.center)

    # ------------------------------------------------------------------ loading
    def _load_tile_layers(self, tmx):
        baked = {}                                      # z -> TileLayer (one big pre-drawn surface)
        for layer in tmx.layers:
            if not isinstance(layer, pytmx.TiledTileLayer):
                continue
            key = layer.name.lower()
            z = LAYER_Z.get(key, Z_LAYERS['bg details'])
            for x, y, surf in layer.tiles():
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                if key == 'terrain':
                    self.solids.add(Tile(pos, surf, 'solid'))
                elif key == 'platforms':
                    self.semis.add(Tile(pos, surf, 'one_way'))
                elif key == 'bounce':
                    self.semis.add(Tile(pos, surf, 'bounce'))
                elif key == 'spike':
                    self.hazards.add(Tile(pos, surf, 'spike'))
                elif key == 'spike inverted':
                    self.hazards.add(Tile(pos, surf, 'spike_down'))
                elif key == 'goal':
                    self.goal_rects.append(pygame.FRect(pos[0], pos[1], TILE_SIZE, TILE_SIZE))
                if layer.visible:
                    if z not in baked:
                        baked[z] = TileLayer((self.width, self.height), z, self.all_sprites)
                    baked[z].image.blit(surf, pos)

    def _load_objects(self, tmx):
        for layer in tmx.layers:
            if not isinstance(layer, pytmx.TiledObjectGroup):
                continue
            for obj in layer:
                kind = (obj.name or getattr(obj, 'type', '') or '').lower()
                pos = (obj.x, obj.y)
                has_size = obj.width > 0 and obj.height > 0
                size = (obj.width, obj.height)
                props = obj.properties

                if kind == 'player':
                    self.runner = Runner(pos, size if has_size else RUNNER_SIZE, self.all_sprites, self)
                elif kind == 'goal':
                    size = size if has_size else (TILE_SIZE, TILE_SIZE)
                    self.goal_rects.append(pygame.FRect(pos[0], pos[1], *size))
                    if getattr(obj, 'visible', True):
                        Sprite(pos, assets.get('goal', size), self.all_sprites, Z_LAYERS['main'] - 0.1)
                elif kind == 'darttrap':
                    default = 'right' if obj.x < self.width / 2 else 'left'
                    direction = 1 if str(props.get('dir', default)).lower() in ('right', 'r') else -1
                    trap = DartTrap(pos, size if has_size else (TILE_SIZE, TILE_SIZE), direction,
                                    self.rng.uniform(0, DART_INTERVAL), self.all_sprites)
                    self.solids.add(trap)
                    self.traps.append(trap)
                elif kind in ('speed', 'heart'):
                    Pickup(kind, pos, size if has_size else PICKUP_SIZE, (self.all_sprites, self.pickup_sprites))
                elif kind == 'spikezone':
                    rect = pygame.FRect(pos[0], pos[1], obj.width, obj.height)
                    side = str(props.get('side') or ('left' if rect.centerx < self.width / 2 else 'right')).lower()
                    self.spike_zones.append((side, rect))
                elif kind in PATH_PLATFORMS:                # old-style path rectangle
                    nat = assets.natural_size(kind)         # the PNG's own size, like the old game
                    pw, ph = nat if nat else PATH_PLATFORMS[kind]
                    pw, ph = pw * PATH_SCALE, ph * PATH_SCALE
                    speed = float(props.get('speed', 40)) * PATH_SCALE
                    if obj.width > obj.height:              # horizontal path
                        axis = 'x'
                        plat_pos = (obj.x, obj.y + obj.height / 2 - ph / 2)
                        distance = obj.width - pw
                    else:                                   # vertical path
                        axis = 'y'
                        plat_pos = (obj.x + obj.width / 2 - pw / 2, obj.y)
                        distance = obj.height - ph
                    sprite = MovingSprite(plat_pos, (pw, ph), axis, max(0, distance), speed,
                                          PATH_SOLID, self.all_sprites, art=kind if nat else None)
                    self.moving_sprites.append(sprite)
                    (self.solids if PATH_SOLID else self.semis).add_moving(sprite)
                elif kind in ('movingplatform', 'movingblock'):
                    solid = kind == 'movingblock'
                    sprite = MovingSprite(pos, size if has_size else (TILE_SIZE * 3, TILE_SIZE),
                                          str(props.get('axis', 'x')).lower(),
                                          float(props.get('distance', 3 * TILE_SIZE)),
                                          float(props.get('speed', 40)), solid, self.all_sprites)
                    self.moving_sprites.append(sprite)
                    (self.solids if solid else self.semis).add_moving(sprite)
                elif obj.name and assets.natural_size(obj.name):    # decoration with art (Lamp, StrucL...)
                    Sprite(pos, assets.get(obj.name, size if has_size else assets.natural_size(obj.name)),
                           self.all_sprites, Z_LAYERS['bg details'])
                elif kind:
                    print(f"[WARNING] Unknown object {kind!r} in layer {layer.name!r} - ignored")

    # ------------------------------------------------------------------ helpers
    @property
    def orb_pos(self):
        return self.to_world(self.ORB_SCREEN)

    @property
    def progress(self):
        if self.winner == "runner":
            return 1.0
        total = self.start_bottom - self.goal_top
        if total <= 0:
            return 0.0
        return max(0.0, min(1.0, (self.start_bottom - self.runner.rect.bottom) / total))

    def to_world(self, screen_pos):
        off = self.all_sprites.draw_offset
        return screen_pos[0] - off[0], screen_pos[1] - off[1]

    def in_bounds(self, rect):
        return rect.left >= 0 and rect.top >= 0 and rect.right <= self.width and rect.bottom <= self.height

    def hits_solid(self, rect):
        return any(rect.colliderect(s.rect) for s in self.solids.query(rect))

    # ------------------------------------------------------------------ update
    def update(self, dt, keys):
        if self.winner:
            return
        r = self.runner

        for s in self.moving_sprites:                   # platforms first, so the runner can ride them
            s.update(dt)
        r.update(dt, keys)
        for s in self.moving_sprites:
            if s.solid:
                s.check_crush(r)

        cam_mid_y = -self.all_sprites.offset.y + VIEW_H / 2
        for trap in self.traps:                         # only nearby traps are active
            if abs(trap.rect.centery - cam_mid_y) < WINDOW_HEIGHT * 1.5:
                trap.update(dt, self)

        for p in self.projectile_sprites.sprites():
            p.update(dt, self)
            if p.alive():
                self._projectile_vs_runner(p)

        for s in self.spike_sprites.sprites():
            s.update(dt)
            if s.alive() and r.rect.colliderect(s.rect):
                r.hit(s.rect.centerx)

        for b in self.effect_sprites.sprites():
            b.update(dt)

        self._contacts()
        self._pickups(dt)

        if not self.winner and r.hearts <= 0:
            self.winner = "caster"
        self.all_sprites.update_camera(r.rect.center, dt)

    def _projectile_vs_runner(self, p):
        r = self.runner
        if r.shield > 0 and math.hypot(p.cx - r.cx, p.cy - r.cy) <= SHIELD_RADIUS + p.rect.w / 2:
            p.kill()                                    # BLOCKED!
        elif p.rect.colliderect(r.rect) and r.hit(p.cx):
            p.kill()

    def _contacts(self):
        r = self.runner
        for t in self.hazards.query(r.rect.inflate(2, 2)):
            if r.rect.colliderect(t.hazard_rect):
                r.hit(t.rect.centerx)
        for g in self.goal_rects:
            if r.rect.colliderect(g):
                self.winner = "runner"

    def _pickups(self, dt):
        r = self.runner
        for pk in self.pickup_sprites.sprites():
            pk.update(dt)
            if not r.rect.colliderect(pk.rect):
                continue
            if pk.kind == "speed":
                r.boost = BOOST_TIME
            elif r.hearts < MAX_HEARTS:
                r.hearts += 1
            else:
                continue                                # full hearts: leave it for later
            pk.kill()

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        surface.fill(COLORS["bg"])
        self.all_sprites.draw(surface)
        ox, oy = self.ORB_SCREEN
        assets.draw_block(surface, "orb", pygame.Rect(ox - ORB_SIZE // 2, oy - ORB_SIZE // 2, ORB_SIZE, ORB_SIZE))
