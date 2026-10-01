"""Built-in castle traps."""
from settings import *
from sprites import Sprite
from spells import Projectile
import assets


class DartTrap(Sprite):
    """A block (a Tiled object named 'DartTrap') that shoots a dart across the castle every few seconds.
    It flashes just before firing. It is solid, and the runner can block darts with the shield."""

    def __init__(self, pos, size, direction, offset, groups):
        super().__init__(pos, assets.get("dart", size), groups, Z_LAYERS['main'] + 0.1)
        self.dir = direction                  # +1 shoots right, -1 shoots left
        self.timer = offset

    @property
    def charging(self):
        return self.timer > DART_INTERVAL - DART_CHARGE

    def update(self, dt, level):
        self.timer += dt
        if self.timer >= DART_INTERVAL:
            self.timer -= DART_INTERVAL
            w, h = DART_SIZE
            x = self.rect.right if self.dir > 0 else self.rect.left - w
            Projectile((x, self.rect.centery - h / 2), DART_SIZE, (self.dir * DART_SPEED, 0), "dart_shot",
                       (level.all_sprites, level.projectile_sprites))

    def draw(self, surface, offset):
        surface.blit(self.image, to_screen(self.rect, offset))
        if self.charging:
            w, h = DART_SIZE
            x = self.rect.right - w if self.dir > 0 else self.rect.left
            assets.draw_block(surface, "dart_shot", to_screen(pygame.FRect(x, self.rect.centery - h / 2, w, h), offset))
