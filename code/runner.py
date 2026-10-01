"""The Runner: A/D to move, SPACE to jump, S or SHIFT to block projectiles."""
from settings import *
import assets


class Runner(pygame.sprite.Sprite):
    def __init__(self, pos, size, groups, level):
        super().__init__(groups)
        self.z = Z_LAYERS['main'] + 0.5
        self.level = level
        self.rect = pygame.FRect(pos[0], pos[1], size[0], size[1])      # size comes from the Tiled object
        self.old_rect = self.rect.copy()
        self.vx = self.vy = 0.0
        self.on_ground = self.bounced = False
        self.platform = None                                # moving platform we are standing on
        self.facing = 1
        self.hearts = MAX_HEARTS
        # timers (seconds left)
        self.coyote = self.jump_buffer = 0.0
        self.invuln = self.stun = self.blind = self.boost = 0.0
        self.shield = self.shield_cd = 0.0

    # ------------------------------------------------------------------ helpers
    @property
    def cx(self):
        return self.rect.centerx

    @property
    def cy(self):
        return self.rect.centery

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.jump_buffer = JUMP_BUFFER
            elif event.key in (pygame.K_s, pygame.K_LSHIFT) and self.shield_cd <= 0:
                self.shield, self.shield_cd = SHIELD_TIME, SHIELD_COOLDOWN

    # ------------------------------------------------------------------ update
    def update(self, dt, keys):
        self.old_rect = self.rect.copy()
        for name in ("invuln", "stun", "blind", "boost", "shield", "shield_cd", "jump_buffer"):
            setattr(self, name, max(0.0, getattr(self, name) - dt))

        if self.stun > 0:                                   # knocked back: no control for a moment
            self.vx *= max(0.0, 1 - 5 * dt)
        else:
            direction = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
            self.vx = direction * (BOOST_SPEED if self.boost > 0 else RUN_SPEED)
            if direction:
                self.facing = direction

        self.coyote = COYOTE if self.on_ground else max(0.0, self.coyote - dt)
        if self.jump_buffer > 0 and self.coyote > 0 and self.stun <= 0:
            self.vy = -JUMP_V
            self.jump_buffer = self.coyote = 0.0
            self.platform = None                            # jumped off, stop riding

        if self.platform:                                   # ride the platform we landed on last frame
            self.rect.x += self.platform.rect.x - self.platform.old_rect.x
            self.rect.y += self.platform.rect.y - self.platform.old_rect.y

        self.move(dt)
        if self.bounced:
            self.coyote = 0.0

    # ------------------------------------------------------------------ movement + collisions
    def move(self, dt):
        self.on_ground = self.bounced = False
        self.platform = None

        self.rect.x += self.vx * dt
        self.collide_x()

        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        self.rect.y += self.vy * dt
        self.collide_y()
        self.collide_one_way()
        self.clamp_to_map()

    def collide_x(self):
        for s in self.level.solids.query(self.rect):
            if not self.rect.colliderect(s.rect):
                continue
            if self.rect.left <= s.rect.right and int(self.old_rect.left) >= int(s.old_rect.right):
                self.rect.left = s.rect.right
                self.vx = 0
            elif self.rect.right >= s.rect.left and int(self.old_rect.right) <= int(s.old_rect.left):
                self.rect.right = s.rect.left
                self.vx = 0

    def collide_y(self):
        for s in self.level.solids.query(self.rect):
            if not self.rect.colliderect(s.rect):
                continue
            if self.rect.top <= s.rect.bottom and int(self.old_rect.top) >= int(s.old_rect.bottom):
                self.rect.top = s.rect.bottom
                if getattr(s, 'moving', False):
                    self.rect.top -= 0.1                    # keep overlapping so the block notices the crush
                self.vy = 0
            elif self.rect.bottom >= s.rect.top and int(self.old_rect.bottom) <= int(s.old_rect.top):
                self.rect.bottom = s.rect.top
                self.vy = 0
                self.on_ground = True
                if getattr(s, 'moving', False):
                    self.platform = s

    def collide_one_way(self):
        """Ledges and bounce pads: land on top, but pass through from below and the sides."""
        if self.vy < 0:
            return
        landing = None
        for s in self.level.semis.query(self.rect):
            if self.rect.colliderect(s.rect) and self.old_rect.bottom <= s.old_rect.top + 0.01:
                if landing is None or getattr(s, 'bounce', False):
                    landing = s
        if landing:
            self.rect.bottom = landing.rect.top
            if getattr(landing, 'bounce', False):
                self.vy, self.bounced = -BOUNCE_V, True
            else:
                self.vy, self.on_ground = 0, True
                if getattr(landing, 'moving', False):
                    self.platform = landing

    def clamp_to_map(self):
        lv = self.level
        if self.rect.left < 0:
            self.rect.left, self.vx = 0, 0
        if self.rect.right > lv.width:
            self.rect.right, self.vx = lv.width, 0
        if self.rect.top < 0:
            self.rect.top, self.vy = 0, max(self.vy, 0)
        if self.rect.bottom > lv.height:                    # the bottom of the map always catches you
            self.rect.bottom, self.vy, self.on_ground = lv.height, 0, True

    # ------------------------------------------------------------------ damage
    def hit(self, from_x):
        """Returns True if damage was taken."""
        if self.invuln > 0 or self.hearts <= 0:
            return False
        self.hearts -= 1
        self.invuln, self.stun = INVULN_TIME, STUN_TIME
        direction = 1 if self.cx >= from_x else -1
        self.vx, self.vy = direction * KNOCKBACK[0], KNOCKBACK[1]
        self.on_ground = False
        self.platform = None
        return True

    # ------------------------------------------------------------------ drawing
    def draw(self, surface, offset):
        if self.invuln > 0 and int(self.invuln * 10) % 2:   # blink while invulnerable
            return
        r = to_screen(self.rect, offset)
        assets.draw_block(surface, "runner", r)
        eye_x = r.centerx + (2 if self.facing > 0 else -5)
        pygame.draw.rect(surface, (255, 255, 255), (eye_x, r.y + 3, 3, 3))
        if self.shield > 0:
            pygame.draw.circle(surface, COLORS["shield"], r.center, SHIELD_RADIUS, 1)
