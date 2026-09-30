"""Main menu: each player picks Runner or Caster (the other player gets the opposite role)."""
import pygame
from settings import *
from ui import Button, draw_text

ROLES = ("runner", "caster")
CONTROLS = {
    "runner": ["A / D  -  move", "SPACE  -  jump", "S or SHIFT  -  block shield", "Reach the top alive!"],
    "caster": ["MOUSE ONLY", "Click a spell, then click to cast", "Only 10 spells - choose wisely", "Stop the runner!"],
}
PANEL_X = {1: 50, 2: 410}


class MenuScene:
    def __init__(self, game):
        self.game = game
        pygame.mouse.set_visible(True)
        self.roles = {1: "runner", 2: "caster"}
        self.role_buttons = {}
        for player, x in PANEL_X.items():
            for i, role in enumerate(ROLES):
                self.role_buttons[(player, role)] = Button((x + 10 + i * 170, 275, 150, 54), role.upper(), 34)
        self.start = Button((280, 500, 240, 60), "START GAME", 38)
        self.quit = Button((330, 575, 140, 40), "QUIT", 26)

    def handle_event(self, event):
        for (player, role), button in self.role_buttons.items():
            if button.clicked(event):
                self.roles[player] = role
                self.roles[3 - player] = "caster" if role == "runner" else "runner"
        if self.start.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self.game.start_match(dict(self.roles))
        elif self.quit.clicked(event):
            self.game.quit()

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(COLORS["bg"])
        draw_text(surface, "CASTLE CLIMB", 84, (255, 215, 0), (SCREEN_W // 2, 70))
        draw_text(surface, "Runner  vs  Caster", 34, (200, 200, 220), (SCREEN_W // 2, 125))
        draw_text(surface, "MAP 1:  The Cramped Castle", 30, (170, 220, 170), (SCREEN_W // 2, 170))
        for player, x in PANEL_X.items():
            pygame.draw.rect(surface, COLORS["room"], (x, 200, 340, 270), border_radius=10)
            pygame.draw.rect(surface, (120, 120, 160), (x, 200, 340, 270), 2, border_radius=10)
            draw_text(surface, f"PLAYER {player}", 40, (255, 255, 255), (x + 170, 240))
            for role in ROLES:
                button = self.role_buttons[(player, role)]
                button.selected = self.roles[player] == role
                button.draw(surface)
            for i, line in enumerate(CONTROLS[self.roles[player]]):
                draw_text(surface, line, 26, (210, 210, 225), (x + 170, 360 + i * 28))
        self.start.draw(surface)
        self.quit.draw(surface)
