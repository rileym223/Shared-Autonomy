"""
Kitchen Runner — Intervention Timing Prototype
===============================================
A 2D top-down kitchen game exploring robot intervention timing.

Two conditions (toggle with TAB):
  PROACTIVE  — agent checks in every 5 seconds and offers help automatically
  REACTIVE   — agent waits until player presses SPACE to call for help

Controls:
  Arrow keys / WASD  — move player
  SPACE              — call agent for help (reactive) / confirm dialogue choice
  TAB                — toggle condition (proactive / reactive)
  1 / 2 / 3          — pick dialogue option when agent speaks
  R                  — restart
  ESC                — quit
"""

import pygame
import sys
import time
import textwrap

# ── Colours ────────────────────────────────────────────────────────────────
BG          = (245, 243, 238)
SURFACE     = (255, 255, 255)
SURFACE_ALT = (235, 233, 228)
BORDER      = (200, 198, 192)
BORDER_DARK = (160, 158, 152)

TEXT_PRIMARY   = (40,  40,  38)
TEXT_SECONDARY = (110, 108, 104)
TEXT_MUTED     = (160, 158, 152)

# Semantic colours (fill, border, text)
SUCCESS  = ((220, 245, 220), (100, 180, 100), (40, 120, 40))
WARNING  = ((255, 243, 200), (200, 160, 40),  (140, 100, 10))
DANGER   = ((255, 230, 225), (220, 100, 80),  (160, 40, 20))
ACCENT   = ((220, 235, 255), (80,  130, 210), (30,  70, 180))
TEAL     = ((210, 245, 235), (60,  170, 130), (20, 100,  70))
PURPLE   = ((235, 228, 255), (120, 90,  200), (60,  40, 140))

WHITE    = (255, 255, 255)
BLACK    = (0,   0,   0)

AGENT_COL  = (60,  170, 130)   # teal
PLAYER_COL = (80,  130, 210)   # accent blue
BLOCKED_COL= (220, 80,  60)    # danger red


# ── Layout constants ────────────────────────────────────────────────────────
W, H = 1100, 720

HUD_H      = 50
SIDEBAR_W  = 200
LOG_H      = 110
PAD        = 12

KITCHEN_X  = SIDEBAR_W
KITCHEN_Y  = HUD_H
KITCHEN_W  = W - SIDEBAR_W
KITCHEN_H  = H - HUD_H - LOG_H

TILE = 48   # grid tile size


# ── Recipe / task data ─────────────────────────────────────────────────────
RECIPE_STEPS = [
    {"label": "Get carrot",   "item": "carrot",  "target": "prep",  "blocked": False},
    {"label": "Get onion",    "item": "onion",   "target": "prep",  "blocked": False},
    {"label": "Get pepper",   "item": "pepper",  "target": "prep",  "blocked": True},   # HIGH SHELF
    {"label": "Get oil",      "item": "oil",     "target": "stove", "blocked": False},
    {"label": "Start stove",  "item": None,      "target": "stove", "blocked": False},
]

AGENT_TASKS = [
    "Fetch pan",
    "Chop carrots",
    "Add oil",
    "Cook 3 min",
    "Plate dish",
]


# ── Helper: draw rounded rect ───────────────────────────────────────────────
def draw_roundrect(surf, color, rect, radius=8, border=0, border_color=None, alpha=255):
    x, y, w, h = rect
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, w, h), border_radius=radius)
    if border and border_color:
        pygame.draw.rect(s, (*border_color, 255), (0, 0, w, h), border, border_radius=radius)
    surf.blit(s, (x, y))


def draw_text(surf, text, font, color, x, y, anchor="topleft", max_width=None):
    if max_width:
        words = text.split()
        lines, line = [], []
        for w in words:
            line.append(w)
            if font.size(" ".join(line))[0] > max_width:
                if len(line) > 1:
                    lines.append(" ".join(line[:-1]))
                    line = [w]
                else:
                    lines.append(" ".join(line))
                    line = []
        if line:
            lines.append(" ".join(line))
        for i, ln in enumerate(lines):
            draw_text(surf, ln, font, color, x, y + i * (font.get_height() + 2), anchor)
        return
    img = font.render(text, True, color)
    r = img.get_rect(**{anchor: (x, y)})
    surf.blit(img, r)


# ── Main game class ────────────────────────────────────────────────────────
class KitchenGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Kitchen Runner — Intervention Prototype")
        self.clock = pygame.time.Clock()

        self.font_lg  = pygame.font.SysFont("Arial", 17, bold=True)
        self.font_md  = pygame.font.SysFont("Arial", 14)
        self.font_sm  = pygame.font.SysFont("Arial", 12)
        self.font_xs  = pygame.font.SysFont("Arial", 11)

        self.reset()

    def reset(self):
        # ── Player state ──
        # Start player in the middle of the kitchen
        kx, ky = KITCHEN_X, KITCHEN_Y
        self.player_pos  = pygame.Vector2(kx + KITCHEN_W // 2, ky + KITCHEN_H // 2)
        self.player_speed = 3
        self.player_item  = None   # currently carrying
        self.recipe_step  = 0
        self.steps_done   = []

        # ── Agent state ──
        self.agent_pos       = pygame.Vector2(kx + KITCHEN_W - 120, ky + KITCHEN_H // 2 - 30)
        self.agent_task_idx  = 0
        self.agent_busy      = True    # doing own task
        self.agent_subtask_progress = 0.0   # 0–1 within current task

        # ── Condition ──
        self.condition = "PROACTIVE"   # or "REACTIVE"

        # ── Intervention / dialogue ──
        self.dialogue_active  = False
        self.dialogue_text    = ""
        self.dialogue_options = []
        self.dialogue_choice  = None

        # ── Proactive timer ──
        self.last_checkin = time.time()
        self.checkin_interval = 5.0
        self.checkin_countdown = self.checkin_interval

        # ── Event log ──
        self.log = [
            "Game started — " + self.condition + " condition",
            "Player: collect ingredients in order",
            "Agent: running parallel cooking tasks",
        ]

        # ── World objects ──
        kx, ky = KITCHEN_X + PAD, KITCHEN_Y + PAD
        kw, kh = KITCHEN_W - 2*PAD, KITCHEN_H - 2*PAD

        # Counter across the top
        self.counter = pygame.Rect(kx, ky, kw, 56)

        # Items on counter (x,y, label, item_id, blocked)
        item_y = ky + 14
        self.items = [
            {"rect": pygame.Rect(kx + 20,  item_y, 70, 30), "label": "🥕 Carrot", "id": "carrot",  "blocked": False, "collected": False},
            {"rect": pygame.Rect(kx + 110, item_y, 70, 30), "label": "🧅 Onion",  "id": "onion",   "blocked": False, "collected": False},
            {"rect": pygame.Rect(kx + 200, item_y, 80, 30), "label": "🫑 Pepper",  "id": "pepper",  "blocked": True,  "collected": False},  # HIGH SHELF
            {"rect": pygame.Rect(kx + 300, item_y, 60, 30), "label": "🫙 Oil",     "id": "oil",     "blocked": False, "collected": False},
        ]

        # Stove (bottom left)
        self.stove = pygame.Rect(kx, ky + kh - 80, 120, 76)

        # Prep zone (centre-left)
        self.prep_zone = pygame.Rect(kx + 140, ky + kh - 80, 140, 76)

        # Drop zone (where agent places things for player)
        self.drop_zone = pygame.Rect(kx + 300, ky + kh - 80, 150, 76)
        self.drop_zone_item = None   # item agent has delivered here

        # Agent workspace (top right)
        self.agent_workspace = pygame.Rect(kx + kw - 160, ky + 70, 150, 90)

        # Game state
        self.game_over  = False
        self.won        = False
        self.start_time = time.time()
        self.elapsed    = 0

    # ── Update ─────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.game_over or self.dialogue_active:
            return

        self.elapsed = time.time() - self.start_time

        # Player movement
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1
        if dx or dy:
            v = pygame.Vector2(dx, dy).normalize() * self.player_speed
            np = self.player_pos + v
            # Clamp to kitchen
            np.x = max(KITCHEN_X + 16, min(W - 16, np.x))
            np.y = max(KITCHEN_Y + 16, min(H - LOG_H - 16, np.y))
            self.player_pos = np

        # Check player collision with items
        pr = pygame.Rect(self.player_pos.x - 14, self.player_pos.y - 14, 28, 28)
        if self.player_item is None:
            for itm in self.items:
                if not itm["collected"] and pr.colliderect(itm["rect"]):
                    if itm["blocked"]:
                        # Can't pick up — trigger intervention?
                        if self.condition == "REACTIVE":
                            self.log_event("Player blocked — press SPACE to call agent", "warning")
                        else:
                            self._proactive_check(forced=True)
                    else:
                        self._pick_up(itm)

            # Check drop zone
            if self.drop_zone_item and pr.colliderect(self.drop_zone):
                for itm in self.items:
                    if itm["id"] == self.drop_zone_item:
                        self._pick_up(itm)
                        self.drop_zone_item = None
                        self.log_event("Player collected item from drop zone", "success")
                        break

        # Check delivery zones
        if self.player_item:
            step = RECIPE_STEPS[self.recipe_step] if self.recipe_step < len(RECIPE_STEPS) else None
            if step:
                target_rect = self.stove if step["target"] == "stove" else self.prep_zone
                if pr.colliderect(target_rect):
                    if step["item"] is None or self.player_item == step["item"]:
                        self._complete_step()

        # Agent subtask progress
        if self.agent_busy:
            self.agent_subtask_progress += dt * 0.12   # ~8s per task
            if self.agent_subtask_progress >= 1.0:
                self.agent_subtask_progress = 0.0
                self.agent_task_idx = (self.agent_task_idx + 1) % len(AGENT_TASKS)
                self.log_event(f"Agent finished: {AGENT_TASKS[self.agent_task_idx - 1]}", "agent")

        # Proactive check-in timer
        if self.condition == "PROACTIVE":
            self.checkin_countdown = self.checkin_interval - (time.time() - self.last_checkin)
            if self.checkin_countdown <= 0:
                self.last_checkin = time.time()
                self.checkin_countdown = self.checkin_interval
                self._proactive_check()

        # Win condition
        if self.recipe_step >= len(RECIPE_STEPS):
            self.game_over = True
            self.won = True
            self.log_event("All steps complete — recipe done!", "success")

    def _pick_up(self, itm):
        self.player_item = itm["id"]
        itm["collected"] = True
        self.log_event(f"Player picked up: {itm['label']}", "player")

    def _complete_step(self):
        step = RECIPE_STEPS[self.recipe_step]
        self.steps_done.append(step["label"])
        self.log_event(f"✓ Step done: {step['label']}", "success")
        self.player_item = None
        self.recipe_step += 1

    def _proactive_check(self, forced=False):
        # Only interrupt if there's something relevant to help with
        if self.recipe_step >= len(RECIPE_STEPS):
            return
        step = RECIPE_STEPS[self.recipe_step]
        if step["blocked"] or forced:
            self._open_dialogue(
                "I see you need the pepper from the high shelf. Should I get it now, or finish my task first?",
                [
                    ("Get it now",            self._agent_fetch_blocked),
                    ("Finish your task first", self._agent_delay),
                    ("I'll handle it",         self._dismiss_dialogue),
                ]
            )
        elif not forced:
            # Generic check-in when nothing is blocked
            self._open_dialogue(
                f"I'm currently {AGENT_TASKS[self.agent_task_idx].lower()}. Do you need anything?",
                [
                    ("I'm fine, thanks",  self._dismiss_dialogue),
                    ("Pause and stand by", self._agent_pause),
                ]
            )

    def _open_dialogue(self, text, options):
        self.dialogue_active  = True
        self.dialogue_text    = text
        self.dialogue_options = options
        self.dialogue_choice  = None
        self.log_event("Agent: " + text[:60] + ("…" if len(text) > 60 else ""), "agent")

    def _dismiss_dialogue(self):
        self.dialogue_active = False
        self.log_event("Player dismissed agent — agent continues task", "player")

    def _agent_fetch_blocked(self):
        self.dialogue_active = False
        self.agent_busy = False
        self.drop_zone_item = "pepper"
        # Mark pepper as available (agent delivers it to drop zone)
        for itm in self.items:
            if itm["id"] == "pepper":
                itm["blocked"] = False
        self.log_event("Agent paused task → fetching pepper from high shelf", "agent")
        self.log_event("Agent placed pepper at drop zone → resuming task", "agent")
        self.agent_busy = True

    def _agent_delay(self):
        self.dialogue_active = False
        self.log_event("Agent will fetch pepper after current task", "agent")
        # Schedule a delayed fetch (will trigger next check-in)
        self.last_checkin = time.time() - (self.checkin_interval - 2)

    def _agent_pause(self):
        self.dialogue_active = False
        self.agent_busy = False
        self.log_event("Agent paused — standing by", "agent")

    def log_event(self, msg, kind="info"):
        ts = f"{int(self.elapsed // 60):02d}:{int(self.elapsed % 60):02d}"
        self.log.append((ts, msg, kind))
        if len(self.log) > 40:
            self.log.pop(0)

    # ── Events ─────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            if event.key == pygame.K_r:
                self.reset(); return

            if event.key == pygame.K_TAB and not self.dialogue_active:
                self.condition = "REACTIVE" if self.condition == "PROACTIVE" else "PROACTIVE"
                self.last_checkin = time.time()
                self.log_event(f"Condition switched to: {self.condition}", "info")
                return

            # Dialogue choices
            if self.dialogue_active:
                if event.key == pygame.K_1 and len(self.dialogue_options) >= 1:
                    self.dialogue_options[0][1]()
                elif event.key == pygame.K_2 and len(self.dialogue_options) >= 2:
                    self.dialogue_options[1][1]()
                elif event.key == pygame.K_3 and len(self.dialogue_options) >= 3:
                    self.dialogue_options[2][1]()
                return

            # SPACE — call agent in reactive mode
            if event.key == pygame.K_SPACE and self.condition == "REACTIVE":
                if self.recipe_step < len(RECIPE_STEPS):
                    step = RECIPE_STEPS[self.recipe_step]
                    if step["blocked"]:
                        self._open_dialogue(
                            "Player called: I need the pepper from the high shelf.",
                            [
                                ("Fetch it now (pause task)", self._agent_fetch_blocked),
                                ("Can't right now",            self._dismiss_dialogue),
                            ]
                        )
                    else:
                        self.log_event("Player called agent — nothing blocked right now", "info")

    # ── Draw ───────────────────────────────────────────────────────────────
    def draw(self):
        self.screen.fill(BG)
        self._draw_hud()
        self._draw_sidebar()
        self._draw_kitchen()
        self._draw_log()
        if self.dialogue_active:
            self._draw_dialogue()
        if self.game_over:
            self._draw_game_over()
        pygame.display.flip()

    def _draw_hud(self):
        pygame.draw.rect(self.screen, SURFACE, (0, 0, W, HUD_H))
        pygame.draw.line(self.screen, BORDER, (0, HUD_H), (W, HUD_H))

        mins, secs = divmod(int(self.elapsed), 60)
        draw_text(self.screen, f"⏱  {mins:02d}:{secs:02d}", self.font_md, TEXT_PRIMARY, 16, 16)

        recipe_label = "Recipe: Veggie stir-fry"
        draw_text(self.screen, recipe_label, self.font_md, TEXT_PRIMARY, W // 2, 16, anchor="midtop")

        # Progress bar
        total = len(RECIPE_STEPS)
        done  = self.recipe_step
        bar_x, bar_y, bar_w, bar_h = W - 320, 14, 200, 14
        pygame.draw.rect(self.screen, SURFACE_ALT, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if done:
            fill_w = int(bar_w * done / total)
            pygame.draw.rect(self.screen, SUCCESS[1], (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
        draw_text(self.screen, f"{done}/{total} steps", self.font_sm, TEXT_SECONDARY, bar_x, bar_y + 18)

        # Condition badge
        c_col = TEAL if self.condition == "PROACTIVE" else PURPLE
        draw_roundrect(self.screen, c_col[0], (W - 108, 10, 96, 28), radius=6, border=1, border_color=c_col[1])
        draw_text(self.screen, self.condition, self.font_sm, c_col[2], W - 60, 24, anchor="center")
        draw_text(self.screen, "TAB to switch", self.font_xs, TEXT_MUTED, W - 60, HUD_H - 3, anchor="midbottom")

    def _draw_sidebar(self):
        pygame.draw.rect(self.screen, SURFACE, (0, HUD_H, SIDEBAR_W, H - HUD_H))
        pygame.draw.line(self.screen, BORDER, (SIDEBAR_W, HUD_H), (SIDEBAR_W, H))

        y = HUD_H + PAD

        # Agent header
        draw_roundrect(self.screen, TEAL[0], (PAD, y, SIDEBAR_W - 2*PAD, 26), radius=6,
                       border=1, border_color=TEAL[1])
        draw_text(self.screen, "🤖  Agent", self.font_md, TEAL[2], SIDEBAR_W // 2, y + 13, anchor="center")
        y += 34

        # Agent avatar circle
        pygame.draw.circle(self.screen, TEAL[0], (SIDEBAR_W // 2, y + 22), 22)
        pygame.draw.circle(self.screen, TEAL[1], (SIDEBAR_W // 2, y + 22), 22, 1)
        draw_text(self.screen, "A", self.font_lg, TEAL[2], SIDEBAR_W // 2, y + 22, anchor="center")
        y += 54

        # Agent status
        status_text = AGENT_TASKS[self.agent_task_idx] if self.agent_busy else "Standby"
        status_col  = SUCCESS if self.agent_busy else WARNING
        draw_roundrect(self.screen, status_col[0], (PAD, y, SIDEBAR_W - 2*PAD, 24), radius=4,
                       border=1, border_color=status_col[1])
        dot = "●" if self.agent_busy else "○"
        draw_text(self.screen, f"{dot} {status_text}", self.font_sm, status_col[2],
                  SIDEBAR_W // 2, y + 12, anchor="center")
        y += 32

        # Agent task list
        draw_text(self.screen, "Tasks:", self.font_sm, TEXT_MUTED, PAD, y)
        y += 18
        for i, task in enumerate(AGENT_TASKS):
            if i < self.agent_task_idx:
                icon, col = "✓", TEXT_MUTED
            elif i == self.agent_task_idx:
                icon, col = "→", TEXT_PRIMARY
            else:
                icon, col = " ", TEXT_MUTED
            draw_text(self.screen, f"{icon} {task}", self.font_sm, col, PAD + 4, y)
            y += 17

        y += 6
        pygame.draw.line(self.screen, BORDER, (PAD, y), (SIDEBAR_W - PAD, y))
        y += 8

        # Checkin timer (proactive only)
        if self.condition == "PROACTIVE":
            countdown = max(0, self.checkin_countdown)
            draw_roundrect(self.screen, WARNING[0], (PAD, y, SIDEBAR_W - 2*PAD, 44), radius=6,
                           border=1, border_color=WARNING[1])
            draw_text(self.screen, "Check-in in", self.font_sm, WARNING[2], SIDEBAR_W // 2, y + 10, anchor="midtop")
            draw_text(self.screen, f"{countdown:.1f}s", self.font_lg, WARNING[2], SIDEBAR_W // 2, y + 26, anchor="midtop")
            y += 52
        else:
            draw_roundrect(self.screen, ACCENT[0], (PAD, y, SIDEBAR_W - 2*PAD, 36), radius=6,
                           border=1, border_color=ACCENT[1])
            draw_text(self.screen, "SPACE = call agent", self.font_sm, ACCENT[2],
                      SIDEBAR_W // 2, y + 18, anchor="center")
            y += 44

        y += 4
        # Recipe steps
        draw_text(self.screen, "Recipe steps:", self.font_sm, TEXT_MUTED, PAD, y)
        y += 18
        for i, step in enumerate(RECIPE_STEPS):
            if i < self.recipe_step:
                icon, col = "✓", SUCCESS[2]
            elif i == self.recipe_step:
                icon, col = "→", TEXT_PRIMARY
            else:
                icon, col = " ", TEXT_MUTED
            draw_text(self.screen, f"{icon} {step['label']}", self.font_sm, col, PAD + 4, y)
            y += 16

        # Controls help (bottom of sidebar)
        ctrl_y = H - LOG_H - 90
        draw_text(self.screen, "Controls:", self.font_xs, TEXT_MUTED, PAD, ctrl_y)
        for i, line in enumerate(["Arrows/WASD: move", "SPACE: call (reactive)", "1/2/3: dialogue", "R: restart  TAB: mode"]):
            draw_text(self.screen, line, self.font_xs, TEXT_MUTED, PAD, ctrl_y + 14 + i * 13)

    def _draw_kitchen(self):
        kx, ky = KITCHEN_X, KITCHEN_Y
        kw, kh = KITCHEN_W, KITCHEN_H

        # Kitchen background
        pygame.draw.rect(self.screen, SURFACE_ALT, (kx, ky, kw, kh))

        # Grid lines (subtle)
        for gx in range(kx, kx + kw, TILE):
            pygame.draw.line(self.screen, BORDER, (gx, ky), (gx, ky + kh), 1)
        for gy in range(ky, ky + kh, TILE):
            pygame.draw.line(self.screen, BORDER, (kx, gy), (kx + kw, gy), 1)

        # Counter
        pygame.draw.rect(self.screen, SURFACE, self.counter, border_radius=6)
        pygame.draw.rect(self.screen, BORDER_DARK, self.counter, 1, border_radius=6)
        draw_text(self.screen, "─── counter / prep area ───", self.font_sm, TEXT_MUTED,
                  self.counter.centerx, self.counter.centery + 20, anchor="center")

        # Items on counter
        for itm in self.items:
            if itm["collected"]:
                continue
            if itm["blocked"]:
                col = DANGER
                label = itm["label"] + " 🔒"
                # Dashed border
                r = itm["rect"].inflate(4, 4)
                draw_roundrect(self.screen, col[0], r, radius=6, border=1, border_color=col[1])
                draw_text(self.screen, label, self.font_sm, col[2], r.centerx, r.centery - 6, anchor="center")
                draw_text(self.screen, "high shelf", self.font_xs, col[2], r.centerx, r.centery + 7, anchor="center")
            else:
                col = SUCCESS
                draw_roundrect(self.screen, col[0], itm["rect"], radius=6, border=1, border_color=col[1])
                draw_text(self.screen, itm["label"], self.font_sm, col[2],
                          itm["rect"].centerx, itm["rect"].centery, anchor="center")

        # Stove
        pygame.draw.rect(self.screen, SURFACE, self.stove, border_radius=8)
        pygame.draw.rect(self.screen, BORDER_DARK, self.stove, 1, border_radius=8)
        draw_text(self.screen, "🔥 Stove", self.font_md, TEXT_PRIMARY, self.stove.centerx, self.stove.top + 14, anchor="midtop")
        draw_text(self.screen, "deliver here", self.font_xs, TEXT_MUTED, self.stove.centerx, self.stove.top + 32, anchor="midtop")

        # Prep zone
        pygame.draw.rect(self.screen, SURFACE, self.prep_zone, border_radius=8)
        pygame.draw.rect(self.screen, BORDER_DARK, self.prep_zone, 1, border_radius=8)
        draw_text(self.screen, "🔪 Prep zone", self.font_md, TEXT_PRIMARY, self.prep_zone.centerx, self.prep_zone.top + 14, anchor="midtop")
        draw_text(self.screen, "deliver here", self.font_xs, TEXT_MUTED, self.prep_zone.centerx, self.prep_zone.top + 32, anchor="midtop")

        # Drop zone
        dz_col = ACCENT if self.drop_zone_item else (SURFACE_ALT, BORDER, TEXT_MUTED)
        draw_roundrect(self.screen, dz_col[0], self.drop_zone, radius=8, border=1, border_color=dz_col[1])
        draw_text(self.screen, "📥 Drop zone", self.font_md, dz_col[2], self.drop_zone.centerx, self.drop_zone.top + 14, anchor="midtop")
        if self.drop_zone_item:
            draw_text(self.screen, f"{self.drop_zone_item} ready!", self.font_sm, dz_col[2],
                      self.drop_zone.centerx, self.drop_zone.top + 34, anchor="midtop")
        else:
            draw_text(self.screen, "agent delivers here", self.font_xs, TEXT_MUTED,
                      self.drop_zone.centerx, self.drop_zone.top + 34, anchor="midtop")

        # Agent workspace
        pygame.draw.rect(self.screen, SURFACE, self.agent_workspace, border_radius=8)
        pygame.draw.rect(self.screen, TEAL[1], self.agent_workspace, 1, border_radius=8)
        draw_text(self.screen, "Agent workspace", self.font_sm, TEAL[2],
                  self.agent_workspace.centerx, self.agent_workspace.top + 10, anchor="midtop")
        # Progress bar for current agent task
        if self.agent_busy:
            bw = self.agent_workspace.width - 20
            bx = self.agent_workspace.left + 10
            by = self.agent_workspace.bottom - 24
            pygame.draw.rect(self.screen, SURFACE_ALT, (bx, by, bw, 12), border_radius=4)
            fw = int(bw * self.agent_subtask_progress)
            if fw:
                pygame.draw.rect(self.screen, TEAL[1], (bx, by, fw, 12), border_radius=4)
            pygame.draw.rect(self.screen, BORDER, (bx, by, bw, 12), 1, border_radius=4)
            draw_text(self.screen, AGENT_TASKS[self.agent_task_idx], self.font_xs, TEAL[2],
                      self.agent_workspace.centerx, by - 14, anchor="midtop")

        # Current step hint
        if self.recipe_step < len(RECIPE_STEPS):
            step = RECIPE_STEPS[self.recipe_step]
            hint = f"Next: {step['label']}"
            if step["blocked"]:
                hint += "  ← BLOCKED (agent needed)"
            draw_text(self.screen, hint, self.font_sm, ACCENT[2],
                      kx + kw // 2, ky + kh - 20, anchor="midbottom")

        # ── Agent character ──
        ax, ay = int(self.agent_pos.x), int(self.agent_pos.y)
        pygame.draw.circle(self.screen, WHITE, (ax, ay), 18)
        pygame.draw.circle(self.screen, TEAL[1], (ax, ay), 18, 2)
        draw_text(self.screen, "A", self.font_lg, TEAL[2], ax, ay, anchor="center")

        # ── Player character ──
        px, py = int(self.player_pos.x), int(self.player_pos.y)
        pygame.draw.circle(self.screen, WHITE, (px, py), 18)
        pygame.draw.circle(self.screen, PLAYER_COL, (px, py), 18, 2)
        draw_text(self.screen, "P", self.font_lg, PLAYER_COL, px, py, anchor="center")

        if self.player_item:
            draw_text(self.screen, self.player_item, self.font_xs, PLAYER_COL, px, py - 26, anchor="midbottom")

        # Player label
        draw_text(self.screen, "you", self.font_xs, TEXT_SECONDARY, px, py + 22, anchor="midtop")

    def _draw_log(self):
        log_y = H - LOG_H
        pygame.draw.rect(self.screen, SURFACE, (0, log_y, W, LOG_H))
        pygame.draw.line(self.screen, BORDER, (0, log_y), (W, log_y))
        draw_text(self.screen, "Event log", self.font_sm, TEXT_MUTED, PAD, log_y + 6)

        color_map = {
            "success": SUCCESS[2],
            "warning": WARNING[2],
            "agent":   TEAL[2],
            "player":  PLAYER_COL,
            "info":    TEXT_SECONDARY,
        }

        # Show last 4 entries
        visible = [e for e in self.log if isinstance(e, tuple)][-5:]
        for i, (ts, msg, kind) in enumerate(reversed(visible)):
            col = color_map.get(kind, TEXT_SECONDARY)
            y = log_y + LOG_H - 14 - i * 18
            draw_text(self.screen, ts, self.font_xs, TEXT_MUTED, PAD + SIDEBAR_W, y)
            draw_text(self.screen, msg, self.font_sm, col, PAD + SIDEBAR_W + 46, y)

    def _draw_dialogue(self):
        # Overlay strip
        box_h = 110 + 36 * len(self.dialogue_options)
        box_y = KITCHEN_Y + KITCHEN_H // 2 - box_h // 2
        box_x = KITCHEN_X + 30
        box_w = KITCHEN_W - 60

        draw_roundrect(self.screen, PURPLE[0], (box_x, box_y, box_w, box_h),
                       radius=12, border=2, border_color=PURPLE[1])

        draw_text(self.screen, "🤖  Agent says:", self.font_md, PURPLE[2], box_x + 16, box_y + 14)

        # Wrap dialogue text
        chars_per_line = (box_w - 32) // 8
        wrapped = textwrap.wrap(self.dialogue_text, width=chars_per_line)
        for i, line in enumerate(wrapped):
            draw_text(self.screen, line, self.font_md, TEXT_PRIMARY, box_x + 16, box_y + 36 + i * 20)

        # Options
        opt_y = box_y + 36 + len(wrapped) * 20 + 14
        for i, (label, _) in enumerate(self.dialogue_options):
            key = str(i + 1)
            obg = SUCCESS[0] if i == 0 else (WARNING[0] if i == 1 else SURFACE_ALT)
            obd = SUCCESS[1] if i == 0 else (WARNING[1] if i == 1 else BORDER)
            otx = SUCCESS[2] if i == 0 else (WARNING[2] if i == 1 else TEXT_SECONDARY)
            draw_roundrect(self.screen, obg, (box_x + 16, opt_y, box_w - 32, 30),
                           radius=6, border=1, border_color=obd)
            draw_text(self.screen, f"[{key}]  {label}", self.font_md, otx,
                      box_x + 32, opt_y + 15, anchor="midleft")
            opt_y += 36

    def _draw_game_over(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((245, 243, 238, 200))
        self.screen.blit(overlay, (0, 0))
        msg = "🎉  Recipe complete!" if self.won else "Game over"
        draw_text(self.screen, msg, self.font_lg, SUCCESS[2] if self.won else DANGER[2],
                  W // 2, H // 2 - 30, anchor="center")
        mins, secs = divmod(int(self.elapsed), 60)
        draw_text(self.screen, f"Time: {mins:02d}:{secs:02d}", self.font_md, TEXT_PRIMARY,
                  W // 2, H // 2 + 4, anchor="center")
        draw_text(self.screen, "Press R to restart", self.font_md, TEXT_SECONDARY,
                  W // 2, H // 2 + 28, anchor="center")

    # ── Main loop ──────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle_event(event)
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    game = KitchenGame()
    game.run()