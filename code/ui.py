"""Small reusable UI pieces."""
import pygame

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def draw_text(surface, text, size, color, pos, center=True):
    img = font(size).render(text, True, color)
    rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
    surface.blit(img, rect)
    return rect


def draw_bar(surface, rect, fraction, color):
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, (20, 18, 28), rect)
    pygame.draw.rect(surface, color, (rect[0], rect[1], int(rect[2] * fraction), rect[3]))
    pygame.draw.rect(surface, (200, 200, 210), rect, 1)


def draw_crosshair(surface, pos, color):
    x, y = pos
    pygame.draw.circle(surface, color, pos, 6, 1)
    pygame.draw.line(surface, color, (x - 11, y), (x - 4, y), 1)
    pygame.draw.line(surface, color, (x + 4, y), (x + 11, y), 1)
    pygame.draw.line(surface, color, (x, y - 11), (x, y - 4), 1)
    pygame.draw.line(surface, color, (x, y + 4), (x, y + 11), 1)
    pygame.draw.circle(surface, color, pos, 1)


class Button:
    def __init__(self, rect, text, size=32):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.size = size
        self.selected = False

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surface):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        color = (70, 170, 110) if self.selected else (95, 95, 140) if hover else (60, 60, 95)
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        pygame.draw.rect(surface, (230, 230, 240), self.rect, 1, border_radius=3)
        draw_text(surface, self.text, self.size, (255, 255, 255), self.rect.center)
