"""Main menu: each player picks Runner or Caster (the other player gets the opposite role)."""
from settings import *
from ui import Button, draw_text

ROLES = ("runner", "caster")
CONTROLS = {
    "runner": ["A / D  -  move", "SPACE  -  jump", "S or SHIFT  -  block shield", "Reach the top alive!"],
    "caster": ["MOUSE ONLY", "Click a spell, then click to cast", f"Only {MAX_SPELLS} spells - choose wisely",
               "Stop the runner!"],
}
PANEL_X = {1: 20, 2: 250}
PANEL_Y, PANEL_W, PANEL_H = 84, 210, 124


class MenuScene:
    def __init__(self, game):
        self.game = game
        pygame.mouse.set_visible(True)
        self.roles = {1: "runner", 2: "caster"}
        self.role_buttons = {}
        for player, x in PANEL_X.items():
            for i, role in enumerate(ROLES):
                self.role_buttons[(player, role)] = Button((x + 8 + i * 100, PANEL_Y + 30, 94, 24), role.upper(), 20)
        self.start = Button((170, 214, 140, 26), "START GAME", 24)
        self.quit = Button((210, 246, 60, 18), "QUIT", 16)

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
        draw_text(surface, "CASTLE CLIMB", 44, (255, 215, 0), (WINDOW_WIDTH // 2, 24))
        draw_text(surface, "Runner  vs  Caster", 20, (200, 200, 220), (WINDOW_WIDTH // 2, 50))
        draw_text(surface, f"MAP 1:  {LEVELS[0][0]}", 18, (170, 220, 170), (WINDOW_WIDTH // 2, 68))
        for player, x in PANEL_X.items():
            pygame.draw.rect(surface, (38, 34, 54), (x, PANEL_Y, PANEL_W, PANEL_H), border_radius=6)
            pygame.draw.rect(surface, (120, 120, 160), (x, PANEL_Y, PANEL_W, PANEL_H), 1, border_radius=6)
            draw_text(surface, f"PLAYER {player}", 24, (255, 255, 255), (x + PANEL_W // 2, PANEL_Y + 14))
            for role in ROLES:
                button = self.role_buttons[(player, role)]
                button.selected = self.roles[player] == role
                button.draw(surface)
            for i, line in enumerate(CONTROLS[self.roles[player]]):
                draw_text(surface, line, 14, (210, 210, 225), (x + PANEL_W // 2, PANEL_Y + 68 + i * 13))
        self.start.draw(surface)
        self.quit.draw(surface)
