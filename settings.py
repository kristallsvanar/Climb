"""Every tweakable number and colour lives here."""

# ---------- screen / grid ----------
TILE = 40                                   # every block is 40x40 px
COLS = 20                                   # castle is 20 blocks wide
SCREEN_W, SCREEN_H = COLS * TILE, 640       # 800 x 640
HUD_H = 64                                  # bottom bar height
FPS = 60
WALL_COLS = 2                               # thickness of the castle walls
LEFT_X = WALL_COLS * TILE                   # play area starts here (80)
RIGHT_X = (COLS - WALL_COLS) * TILE         # ...and ends here (720)

# ---------- runner physics (pixels / second) ----------
GRAVITY = 2000
MAX_FALL = 900
JUMP_V = 800                # ~4 blocks high
BOUNCE_V = 1150             # ~8 blocks high
RUN_SPEED = 240
BOOST_SPEED = 340
BOOST_TIME = 6.0
MAX_HEARTS = 3
INVULN_TIME = 1.5           # seconds of safety after being hit
KNOCKBACK = (420, -420)     # (sideways, upwards)
STUN_TIME = 0.3
SHIELD_TIME = 0.6           # how long the block-shield stays up
SHIELD_COOLDOWN = 2.5
SHIELD_RADIUS = 38
COYOTE = 0.08               # grace time to jump after leaving a ledge
JUMP_BUFFER = 0.12          # grace time for pressing jump slightly early

# ---------- caster ----------
MAX_SPELLS = 10
CAST_COOLDOWN = 0.6
PROJECTILE_SPEED = 420
BLIND_TIME = 0.8
BLIND_RADIUS = 120
SPIKE_SPEED = 170
SPIKE_LIFETIME = 9.0

# ---------- castle traps ----------
DART_INTERVAL = 3.2
DART_SPEED = 240

# ---------- colours (every object is a coloured block; drop a PNG in /assets to replace it) ----------
COLORS = {
    "wall": (72, 68, 92), "stone": (140, 130, 120), "bounce": (70, 210, 100),
    "spike": (230, 60, 60), "dart": (150, 90, 50), "goal": (255, 215, 0),
    "runner": (80, 160, 255), "projectile": (190, 90, 255), "dart_shot": (255, 150, 40),
    "moving_spike": (255, 100, 30), "heart": (255, 90, 130), "heart_empty": (70, 60, 70),
    "speed": (255, 235, 60), "orb": (160, 90, 230),
    "bg": (24, 20, 34), "room": (38, 34, 54), "shield": (120, 230, 255),
}
