"""The Caster: mouse only. Picks a spell, aims with the crosshair, has a limited number of casts."""
from settings import *
from spells import ProjectileSpell, BlindnessSpell, SpikeSpell


class Caster:
    def __init__(self):
        self.spells = [ProjectileSpell(), BlindnessSpell(), SpikeSpell()]
        self.selected = 0
        self.spells_left = MAX_SPELLS
        self.cooldown = 0.0

    @property
    def spell(self):
        return self.spells[self.selected]

    def select(self, index):
        self.selected = index % len(self.spells)

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)

    def can_cast(self):
        return self.spells_left > 0 and self.cooldown <= 0

    def cast(self, world, screen_pos):
        """screen_pos is the mouse position on screen. Returns True if a spell was used."""
        pos = (screen_pos[0], screen_pos[1] + world.cam)      # convert to world coordinates
        if not self.can_cast() or not self.spell.is_valid(world, pos):
            return False
        self.spell.cast(world, pos)
        self.spells_left -= 1
        self.cooldown = CAST_COOLDOWN
        return True
