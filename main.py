import pygame
import serial
import random
import os
import sys
import time

# --- PATH SETUP ---
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- CONFIG ---
SERIAL_PORT = 'COM6'
BAUD_RATE   = 115200
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
LANE_X = [250, 400, 550]

# --- COLORS (defined once, used everywhere) ---
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
CYAN        = (0,   255, 255)
RED         = (255, 0,   0)
GREEN       = (0,   255, 0)
YELLOW      = (255, 200, 0)
GRAY        = (120, 120, 120)
DARK_BG     = (15,  15,  25)
HUD_BG      = (0,   0,   0)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ESP32 Pro Racer - EF-2 Edition")
clock = pygame.time.Clock()

# --- FONTS ---
font_main    = pygame.font.SysFont("Agency FB", 36, bold=True)
font_big     = pygame.font.SysFont("Agency FB", 90, bold=True)
font_instr   = pygame.font.SysFont("Agency FB", 28)
font_credits = pygame.font.SysFont("Arial", 18, italic=True)

# --- ASSET LOADING ---
def load_img(name, size):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((200, 0, 0, 200))
        return surf

player_img = load_img('car.png',          (65, 120))
obs_img    = load_img('obstacle_car.png', (65, 120))
road_img   = load_img('road_texture.png', (500, 600))
grass_img  = load_img('grass_texture.png',(150, 600))

# --- PRE-BAKE a tree placeholder surface (do it once, not every frame) ---
TREE_SURF = pygame.Surface((20, 40), pygame.SRCALPHA)
TREE_SURF.fill((0, 140, 0))

CREDIT_STR = "Made by the students of E.F-2: Sahib Singh, Diksha Kamboj, Antarjita"

# ─────────────────────────────────────────────
#  MOVING OBJECT
# ─────────────────────────────────────────────
class MovingObject:
    def __init__(self, obj_type='CAR'):
        self.type  = obj_type
        self.y     = -200
        if obj_type == 'CAR':
            self.x     = random.choice(LANE_X)
            self.speed = random.randint(7, 11)
        else:                                   # roadside decoration / tree
            self.x     = random.choice([60, 740])
            self.speed = random.randint(6, 9)

    def move(self):
        self.y += self.speed

    def draw(self):
        if self.type == 'CAR':
            img  = obs_img
            rect = img.get_rect(center=(self.x, self.y))
            screen.blit(img, rect)
        else:
            rect = TREE_SURF.get_rect(center=(self.x, self.y))
            screen.blit(TREE_SURF, rect)
        return rect

    @property
    def off_screen(self):
        return self.y > SCREEN_HEIGHT + 50


# ─────────────────────────────────────────────
#  SERIAL HELPER
# ─────────────────────────────────────────────
def open_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
        ser.reset_input_buffer()
        return ser
    except Exception:
        return None


def read_lane(ser, current_target):
    """Read the latest distance value and return the target lane X.
       Flushes stale bytes so we always act on the freshest reading."""
    if ser is None:
        return current_target
    try:
        # Drain everything except the last line to avoid latency build-up
        if ser.in_waiting > 0:
            raw = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            lines = [l.strip() for l in raw.splitlines() if l.strip()]
            for line in reversed(lines):           # newest first
                if line.isdigit():
                    dist = int(line)
                    if dist < 12:
                        return LANE_X[2]           # hand close  → right lane
                    elif dist > 28:
                        return LANE_X[0]           # hand far    → left lane
                    else:
                        return LANE_X[1]           # middle
    except Exception:
        pass
    return current_target


# ─────────────────────────────────────────────
#  DRAW HELPERS
# ─────────────────────────────────────────────
def draw_road(scroll):
    """Seamless scrolling road + grass."""
    # Two tiles stacked so the seam is always off-screen
    for offset in (scroll, scroll - 600):
        screen.blit(grass_img, (0,   offset))
        screen.blit(grass_img, (650, offset))
        screen.blit(road_img,  (150, offset))


def draw_hud(score):
    hud_surf = pygame.Surface((210, 50), pygame.SRCALPHA)
    hud_surf.fill((0, 0, 0, 160))
    screen.blit(hud_surf, (20, 20))
    s_txt = font_main.render(f"SCORE: {score}", True, CYAN)
    screen.blit(s_txt, (40, 27))


def draw_credits():
    credits = font_credits.render(CREDIT_STR, True, GRAY)
    screen.blit(credits, (SCREEN_WIDTH - credits.get_width() - 20, SCREEN_HEIGHT - 35))


# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def show_welcome_screen():
    """Shown once at the very start before first game."""
    waiting = True
    while waiting:
        screen.fill(DARK_BG)

        title  = font_big.render("PRO RACER",         True, CYAN)
        sub    = font_main.render("EF-2 Edition",      True, WHITE)
        i1     = font_instr.render("Move hand TOWARDS sensor  →  Move RIGHT", True, WHITE)
        i2     = font_instr.render("Move hand AWAY from sensor →  Move LEFT",  True, WHITE)
        i3     = font_instr.render("Stay between 5 cm and 40 cm from sensor",  True, YELLOW)
        play   = font_main.render("PRESS 'R' TO START",                         True, GREEN)

        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,  80))
        screen.blit(sub,   (SCREEN_WIDTH // 2 - sub.get_width()   // 2, 180))
        screen.blit(i1,    (110, 270))
        screen.blit(i2,    (110, 315))
        screen.blit(i3,    (110, 360))
        screen.blit(play,  (SCREEN_WIDTH // 2 - play.get_width()  // 2, 450))
        draw_credits()

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                waiting = False


def show_game_over_screen(final_score):
    """Two-phase game-over: 4 s score → instructions, wait for 'R'."""
    start_time = time.time()
    waiting    = True

    while waiting:
        elapsed = time.time() - start_time
        screen.fill(DARK_BG)

        if elapsed < 4.0:
            # ── Phase 1: WASTED + score ──
            go_msg = font_big.render("WASTED",              True, RED)
            sc_msg = font_main.render(f"FINAL SCORE: {final_score}", True, WHITE)
            rt_msg = font_instr.render("Press 'R' to Restart",       True, (200, 200, 200))

            screen.blit(go_msg, (SCREEN_WIDTH // 2 - go_msg.get_width() // 2, 180))
            screen.blit(sc_msg, (SCREEN_WIDTH // 2 - sc_msg.get_width() // 2, 300))
            screen.blit(rt_msg, (SCREEN_WIDTH // 2 - rt_msg.get_width() // 2, 360))
        else:
            # ── Phase 2: instructions ──
            title = font_main.render("GAME INSTRUCTIONS",                           True, CYAN)
            i1    = font_instr.render("- Move hand TOWARDS sensor  →  Move RIGHT",  True, WHITE)
            i2    = font_instr.render("- Move hand AWAY from sensor →  Move LEFT",  True, WHITE)
            i3    = font_instr.render("- Stay between 5 cm and 40 cm from sensor",  True, YELLOW)
            play  = font_main.render("PRESS 'R' TO PLAY AGAIN",                     True, GREEN)

            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
            screen.blit(i1,    (110, 200))
            screen.blit(i2,    (110, 250))
            screen.blit(i3,    (110, 300))
            screen.blit(play,  (SCREEN_WIDTH // 2 - play.get_width()  // 2, 420))

        draw_credits()
        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                waiting = False


# ─────────────────────────────────────────────
#  MAIN GAME LOOP
# ─────────────────────────────────────────────
def run_game():
    ser = open_serial()

    car_x       = 400.0
    target_x    = 400
    road_scroll = 0
    score       = 0
    objects     = []
    spawn_timer = 0
    active      = True
    start_time  = time.time()

    while active:
        # ── Serial ──
        target_x = read_lane(ser, target_x)

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if ser: ser.close()
                pygame.quit(); sys.exit()

        # ── Road scroll (modulo 600 so it loops cleanly) ──
        road_scroll = (road_scroll + 12) % 600
        draw_road(road_scroll)

        # ── Spawn objects ──
        spawn_timer += 1
        if spawn_timer >= 85:
            objects.append(MovingObject('CAR'))
            spawn_timer = 0

        # ── Smooth car movement ──
        car_x += (target_x - car_x) * 0.15
        player_rect   = player_img.get_rect(center=(int(car_x), 500))

        # Safe hitbox: never smaller than 1×1
        hb_w = max(1, player_rect.width  - 20)
        hb_h = max(1, player_rect.height - 30)
        player_hitbox = pygame.Rect(0, 0, hb_w, hb_h)
        player_hitbox.center = player_rect.center

        screen.blit(player_img, player_rect)

        # ── Update & draw objects ──
        for obj in objects[:]:
            obj.move()
            obj_rect = obj.draw()
            if obj.type == 'CAR' and player_hitbox.colliderect(obj_rect):
                active = False
            if obj.off_screen:
                objects.remove(obj)
                if obj.type == 'CAR':
                    score += 1

        # -- Instruction overlay (first 5 s, fades out in last 1 s) --
        elapsed = time.time() - start_time
        if elapsed < 5.0:
            alpha = int(200 * min(1.0, (5.0 - elapsed)))

            panel = pygame.Surface((480, 100), pygame.SRCALPHA)
            panel.fill((0, 0, 0, min(alpha, 150)))
            screen.blit(panel, (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 - 50))

            hint1 = font_instr.render("Hand CLOSE  ->  Move RIGHT", True, WHITE)
            hint2 = font_instr.render("Hand FAR    ->  Move LEFT",  True, WHITE)
            hint1.set_alpha(alpha)
            hint2.set_alpha(alpha)
            screen.blit(hint1, (SCREEN_WIDTH // 2 - hint1.get_width() // 2, SCREEN_HEIGHT // 2 - 38))
            screen.blit(hint2, (SCREEN_WIDTH // 2 - hint2.get_width() // 2, SCREEN_HEIGHT // 2 + 8))

        # -- HUD --
        draw_hud(score)

        pygame.display.flip()
        clock.tick(60)

    if ser:
        ser.close()
    return score


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
show_welcome_screen()

while True:
    final = run_game()
    show_game_over_screen(final)
