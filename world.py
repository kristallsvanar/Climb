"""The World ties everything together: level, runner, projectiles, spikes, camera, win/lose."""
import math
import pygame
from settings import *
from level import Level
from runner import Runner
import assets


class World:
    ORB_SCREEN = (SCREEN_W // 2, 34)                # the caster's floating orb (fixed on screen)

    def __init__(self, map_data):
        self.level = Level(map_data)
        self.runner = Runner(SCREEN_W / 2 - Runner.W / 2, self.level.ground_y - Runner.H)
        self.projectiles, self.spikes, self.bursts = [], [], []
        self.winner = None                          # "runner" or "caster"
        self.cam_y = self._target_cam()

    # ------------------------------------------------------------------ helpers
    @property
    def cam(self):
        return round(self.cam_y)

    @property
    def orb_pos(self):
        return self.ORB_SCREEN[0], self.ORB_SCREEN[1] + self.cam

    @property
    def progress(self):
        total = self.level.ground_y - self.level.goal_y
        return max(0.0, min(1.0, (self.level.ground_y - (self.runner.y + Runner.H)) / total))

    def _target_cam(self):
        target = self.runner.cy - (SCREEN_H - HUD_H) * 0.6
        return max(0, min(target, self.level.height - SCREEN_H))

    # ------------------------------------------------------------------ update
    def update(self, dt, keys):
        if self.winner:
            return
        r, level = self.runner, self.level
        r.update(dt, level, keys)

        for trap in level.darts:                                # only nearby traps are active
            if abs(trap.y - self.cam_y) < SCREEN_H * 1.5:
                trap.update(dt, self)

        for p in self.projectiles:
            p.update(dt, level)
            self._projectile_vs_runner(p)
        self.projectiles = [p for p in self.projectiles if p.alive]

        for s in self.spikes:
            s.update(dt)
            if r.rect.colliderect(s.rect):
                r.hit(s.rect.centerx)
        self.spikes = [s for s in self.spikes if s.alive]

        for b in self.bursts:
            b.update(dt)
        self.bursts = [b for b in self.bursts if b.alive]

        self._tile_contacts()
        self._pickups(dt)

        if r.hearts <= 0:
            self.winner = "caster"
        self.cam_y += (self._target_cam() - self.cam_y) * min(1.0, 10 * dt)

    def _projectile_vs_runner(self, p):
        r = self.runner
        if r.shield > 0 and math.hypot(p.cx - r.cx, p.cy - r.cy) <= SHIELD_RADIUS + p.w / 2:
            p.alive = False                                     # BLOCKED!
        elif p.rect.colliderect(r.rect) and r.hit(p.cx):
            p.alive = False

    def _tile_contacts(self):
        r = self.runner
        for t in self.level.tiles_in(r.x - 2, r.y - 2, r.w + 4, r.h + 4):
            if t.kind == "spike" and r.rect.colliderect(t.hazard_rect):
                r.hit(t.x + TILE / 2)
            elif t.kind == "goal" and r.rect.colliderect(t.rect):
                self.winner = "runner"

    def _pickups(self, dt):
        r = self.runner
        for pk in list(self.level.pickups):
            pk.update(dt)
            if not r.rect.colliderect(pk.rect):
                continue
            if pk.kind == "speed":
                r.boost = BOOST_TIME
            elif r.hearts < MAX_HEARTS:
                r.hearts += 1
            else:
                continue                                        # full hearts: leave it for later
            self.level.pickups.remove(pk)

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        cam = self.cam
        self.level.draw(surface, cam)
        for trap in self.level.darts:
            trap.draw(surface, cam)
        for group in (self.level.pickups, self.spikes, self.projectiles, self.bursts):
            for obj in group:
                obj.draw(surface, cam)
        self.runner.draw(surface, cam)
        ox, oy = self.ORB_SCREEN
        assets.draw_block(surface, "orb", pygame.Rect(ox - 18, oy - 18, 36, 36))
