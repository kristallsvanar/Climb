"""The Runner: A/D to move, SPACE to jump, S or SHIFT to block projectiles."""
import pygame
from settings import *
import assets


class Runner:
    W, H = 28, 36

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.w, self.h = self.W, self.H
        self.vx = self.vy = 0.0
        self.on_ground = self.bounced = False
        self.facing = 1
        self.hearts = MAX_HEARTS
        # timers (seconds left)
        self.coyote = self.jump_buffer = 0.0
        self.invuln = self.stun = self.blind = self.boost = 0.0
        self.shield = self.shield_cd = 0.0

    # ------------------------------------------------------------------ helpers
    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), self.w, self.h)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.jump_buffer = JUMP_BUFFER
            elif event.key in (pygame.K_s, pygame.K_LSHIFT) and self.shield_cd <= 0:
                self.shield, self.shield_cd = SHIELD_TIME, SHIELD_COOLDOWN

    # ------------------------------------------------------------------ update
    def update(self, dt, level, keys):
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

        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        level.move_body(self, dt)
        if self.bounced:
            self.coyote = 0.0

    def hit(self, from_x):
        """Returns True if damage was taken."""
        if self.invuln > 0 or self.hearts <= 0:
            return False
        self.hearts -= 1
        self.invuln, self.stun = INVULN_TIME, STUN_TIME
        direction = 1 if self.cx >= from_x else -1
        self.vx, self.vy = direction * KNOCKBACK[0], KNOCKBACK[1]
        self.on_ground = False
        return True

    # ------------------------------------------------------------------ drawing
    def draw(self, surface, cam):
        if self.invuln > 0 and int(self.invuln * 10) % 2:   # blink while invulnerable
            return
        r = self.rect.move(0, -cam)
        assets.draw_block(surface, "runner", r)
        eye_x = r.centerx + (4 if self.facing > 0 else -10)
        pygame.draw.rect(surface, (255, 255, 255), (eye_x, r.y + 8, 6, 6))
        if self.shield > 0:
            pygame.draw.circle(surface, COLORS["shield"], r.center, SHIELD_RADIUS, 3)
