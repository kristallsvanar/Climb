"""The match itself: runner input, caster mouse input, HUD and the game-over screen."""
import pygame
from settings import *
from maps import CASTLE_1
from world import World
from caster import Caster
from ui import Button, draw_text, draw_bar, draw_crosshair
import assets

HUD_TOP = SCREEN_H - HUD_H


class GameScene:
    def __init__(self, game, roles):
        self.game, self.roles = game, roles
        self.runner_player = 1 if roles[1] == "runner" else 2
        self.caster_player = 3 - self.runner_player
        self.world = World(CASTLE_1)
        self.caster = Caster()
        self.blind_overlay = pygame.Surface((SCREEN_W, HUD_TOP))
        self.blind_overlay.set_alpha(245)
        self.spell_buttons = [Button((16 + i * 150, HUD_TOP + 10, 142, 44), s.name, 26)
                              for i, s in enumerate(self.caster.spells)]
        self.rematch = Button((250, 340, 300, 50), "REMATCH", 34)
        self.menu = Button((250, 405, 300, 50), "MAIN MENU", 34)

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.show_menu()
        elif self.world.winner:
            if self.rematch.clicked(event):
                self.game.start_match(self.roles)
            elif self.menu.clicked(event):
                self.game.show_menu()
        else:
            self.world.runner.handle_event(event)               # keyboard -> runner
            if event.type == pygame.MOUSEWHEEL:                 # mouse -> caster
                self.caster.select(self.caster.selected - event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, button in enumerate(self.spell_buttons):
                    if button.rect.collidepoint(event.pos):
                        self.caster.select(i)
                        return
                if event.pos[1] < HUD_TOP:
                    self.caster.cast(self.world, event.pos)

    # ------------------------------------------------------------------ update
    def update(self, dt):
        if not self.world.winner:
            self.caster.update(dt)
            self.world.update(dt, pygame.key.get_pressed())
        mouse_y = pygame.mouse.get_pos()[1]
        pygame.mouse.set_visible(bool(self.world.winner) or mouse_y >= HUD_TOP)

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        world, runner = self.world, self.world.runner
        world.draw(surface)
        if runner.blind > 0:
            surface.blit(self.blind_overlay, (0, 0))
            draw_text(surface, "BLINDED!", 64, (255, 255, 255), (SCREEN_W // 2, 260))
        mouse = pygame.mouse.get_pos()
        if not world.winner:
            self.caster.spell.draw_preview(surface, world, mouse)
        self._draw_hud(surface)
        if not world.winner and mouse[1] < HUD_TOP:
            can = self.caster.can_cast() and self.caster.spell.is_valid(world, (mouse[0], mouse[1] + world.cam))
            draw_crosshair(surface, mouse, (255, 255, 255) if can else (255, 70, 70))
        if world.winner:
            self._draw_game_over(surface)

    def _draw_hud(self, surface):
        r = self.world.runner
        for i in range(MAX_HEARTS):                             # runner: hearts, shield, boost
            assets.draw_block(surface, "heart" if i < r.hearts else "heart_empty",
                              pygame.Rect(12 + i * 30, 12, 24, 24))
        draw_bar(surface, (12, 44, 90, 8), 1 - r.shield_cd / SHIELD_COOLDOWN, COLORS["shield"])
        draw_text(surface, "SHIELD (S)", 18, (255, 255, 255), (108, 48), center=False)
        if r.boost > 0:
            draw_bar(surface, (12, 58, 90, 8), r.boost / BOOST_TIME, COLORS["speed"])
            draw_text(surface, "SPEED", 18, (255, 255, 255), (108, 62), center=False)
        draw_text(surface, f"P{self.runner_player}: RUNNER", 22, (170, 210, 255), (12, 76), center=False)

        draw_bar(surface, (SCREEN_W - 140, 14, 124, 12), self.world.progress, COLORS["goal"])
        draw_text(surface, f"CLIMB {int(self.world.progress * 100)}%", 20, (255, 255, 255),
                  (SCREEN_W - 78, 36))

        pygame.draw.rect(surface, (18, 14, 28), (0, HUD_TOP, SCREEN_W, HUD_H))          # caster bar
        for i, button in enumerate(self.spell_buttons):
            button.selected = i == self.caster.selected
            button.draw(surface)
        c = self.caster
        draw_text(surface, f"P{self.caster_player} CASTER   SPELLS {c.spells_left}/{MAX_SPELLS}", 24,
                  (220, 190, 255), (SCREEN_W - 170, HUD_TOP + 22))
        draw_bar(surface, (SCREEN_W - 270, HUD_TOP + 40, 200, 8), 1 - c.cooldown / CAST_COOLDOWN, COLORS["orb"])

    def _draw_game_over(self, surface):
        runner_won = self.world.winner == "runner"
        pygame.draw.rect(surface, (15, 12, 25), (190, 200, 420, 280), border_radius=12)
        pygame.draw.rect(surface, (255, 215, 0), (190, 200, 420, 280), 3, border_radius=12)
        title = "RUNNER WINS!" if runner_won else "CASTER WINS!"
        who = self.runner_player if runner_won else self.caster_player
        note = "reached the top of the castle" if runner_won else "stopped the runner"
        draw_text(surface, title, 60, (255, 215, 0), (SCREEN_W // 2, 245))
        draw_text(surface, f"Player {who} {note}", 28, (230, 230, 240), (SCREEN_W // 2, 295))
        self.rematch.draw(surface)
        self.menu.draw(surface)
