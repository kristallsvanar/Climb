"""The Game owns the window and switches between scenes (menu <-> match)."""
import pygame
from settings import *
from menu import MenuScene
from game_scene import GameScene


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Castle Climb - Runner vs Caster")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.show_menu()

    def show_menu(self):
        self.scene = MenuScene(self)

    def start_match(self, roles):
        self.scene = GameScene(self, roles)

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 1 / 30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
