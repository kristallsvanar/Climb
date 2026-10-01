"""The match itself: runner keyboard input, caster mouse input, HUD and the game-over screen."""
from settings import *
from caster import Caster
from ui import Button, draw_text, draw_bar, draw_crosshair
import assets

HUD_TOP = VIEW_H
WHITE = (255, 255, 255)


class GameScene:
    def __init__(self, game, roles):
        self.game, self.roles = game, roles
        self.runner_player = 1 if roles[1] == "runner" else 2
        self.caster_player = 3 - self.runner_player
        self.level = game.new_level()
        self.caster = Caster()
        self.blind_overlay = pygame.Surface((WINDOW_WIDTH, VIEW_H))
        self.blind_overlay.set_alpha(245)
        self.spell_buttons = [Button((6 + i * 80, HUD_TOP + 4, 76, 20), s.name, 14)
                              for i, s in enumerate(self.caster.spells)]
        self.rematch = Button((150, 140, 180, 24), "REMATCH", 20)
        self.menu = Button((150, 172, 180, 24), "MAIN MENU", 20)

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.show_menu()
        elif self.level.winner:
            if self.rematch.clicked(event):
                self.game.start_match(self.roles)
            elif self.menu.clicked(event):
                self.game.show_menu()
        else:
            self.level.runner.handle_event(event)                   # keyboard -> runner
            if event.type == pygame.MOUSEWHEEL:                     # mouse -> caster
                self.caster.select(self.caster.selected - event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, button in enumerate(self.spell_buttons):
                    if button.rect.collidepoint(event.pos):
                        self.caster.select(i)
                        return
                if event.pos[1] < HUD_TOP:
                    self.caster.cast(self.level, event.pos)

    # ------------------------------------------------------------------ update
    def update(self, dt):
        if not self.level.winner:
            self.caster.update(dt)
            self.level.update(dt, pygame.key.get_pressed())
        mouse_y = pygame.mouse.get_pos()[1]
        pygame.mouse.set_visible(bool(self.level.winner) or mouse_y >= HUD_TOP)

    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        level, runner = self.level, self.level.runner
        level.draw(surface)
        if runner.blind > 0:
            surface.blit(self.blind_overlay, (0, 0))
            draw_text(surface, "BLINDED!", 36, WHITE, (WINDOW_WIDTH // 2, 110))
        mouse = pygame.mouse.get_pos()
        if not level.winner:
            self.caster.spell.draw_preview(surface, level, mouse)
        self._draw_hud(surface)
        if not level.winner and mouse[1] < HUD_TOP:
            can = self.caster.can_cast() and self.caster.spell.is_valid(level, level.to_world(mouse))
            draw_crosshair(surface, mouse, WHITE if can else (255, 70, 70))
        if level.winner:
            self._draw_game_over(surface)

    def _draw_hud(self, surface):
        r = self.level.runner
        for i in range(MAX_HEARTS):                                 # runner: hearts, shield, boost
            assets.draw_block(surface, "heart" if i < r.hearts else "heart_empty",
                              pygame.Rect(6 + i * 14, 6, 12, 12))
        draw_bar(surface, (6, 22, 48, 4), 1 - r.shield_cd / SHIELD_COOLDOWN, COLORS["shield"])
        draw_text(surface, "SHIELD (S)", 12, WHITE, (58, 20), center=False)
        if r.boost > 0:
            draw_bar(surface, (6, 30, 48, 4), r.boost / BOOST_TIME, COLORS["speed"])
            draw_text(surface, "SPEED", 12, WHITE, (58, 28), center=False)
        draw_text(surface, f"P{self.runner_player}: RUNNER", 14, (170, 210, 255), (6, 38), center=False)

        draw_bar(surface, (WINDOW_WIDTH - 76, 6, 70, 6), self.level.progress, COLORS["goal"])
        draw_text(surface, f"CLIMB {int(self.level.progress * 100)}%", 14, WHITE, (WINDOW_WIDTH - 41, 20))

        pygame.draw.rect(surface, (18, 14, 28), (0, HUD_TOP, WINDOW_WIDTH, HUD_H))              # caster bar
        for i, button in enumerate(self.spell_buttons):
            button.selected = i == self.caster.selected
            button.draw(surface)
        c = self.caster
        draw_text(surface, f"P{self.caster_player} CASTER   SPELLS {c.spells_left}/{MAX_SPELLS}", 16,
                  (220, 190, 255), (WINDOW_WIDTH - 120, HUD_TOP + 9))
        draw_bar(surface, (WINDOW_WIDTH - 190, HUD_TOP + 19, 160, 4), 1 - c.cooldown / CAST_COOLDOWN, COLORS["orb"])

    def _draw_game_over(self, surface):
        runner_won = self.level.winner == "runner"
        pygame.draw.rect(surface, (15, 12, 25), (110, 60, 260, 150), border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0), (110, 60, 260, 150), 2, border_radius=8)
        title = "RUNNER WINS!" if runner_won else "CASTER WINS!"
        who = self.runner_player if runner_won else self.caster_player
        note = "reached the top of the castle" if runner_won else "stopped the runner"
        draw_text(surface, title, 36, (255, 215, 0), (WINDOW_WIDTH // 2, 90))
        draw_text(surface, f"Player {who} {note}", 16, (230, 230, 240), (WINDOW_WIDTH // 2, 118))
        self.rematch.draw(surface)
        self.menu.draw(surface)
