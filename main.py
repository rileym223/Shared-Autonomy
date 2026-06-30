"""Shared Autonomy — static wireframe UI (no functionality yet)."""

import pygame
import sys

# ── Colours ─────────────────────────────────────────────────────────────────
BG = (252, 250, 245)
INK = (30, 30, 28)
INK_LIGHT = (90, 88, 84)
BORDER = (50, 48, 44)

W, H = 960, 720
PAD = 24

# Section heights
GAME_H = 340
INTERACTION_H = 200
NOTES_H = H - GAME_H - INTERACTION_H - 2 * PAD


def draw_text(surf, text, font, color, x, y, anchor="topleft"):
    img = font.render(text, True, color)
    rect = img.get_rect(**{anchor: (x, y)})
    surf.blit(img, rect)


def draw_box(surf, rect, label=None, font=None, radius=4):
    pygame.draw.rect(surf, BG, rect, border_radius=radius)
    pygame.draw.rect(surf, BORDER, rect, 2, border_radius=radius)
    if label and font:
        draw_text(surf, label, font, INK, rect.centerx, rect.centery, anchor="center")


def draw_dashed_line(surf, start, end, color=BORDER, width=2, dash=8, gap=6):
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    drawing = True
    while pos < length:
        seg = dash if drawing else gap
        seg = min(seg, length - pos)
        if drawing:
            sx = x1 + ux * pos
            sy = y1 + uy * pos
            ex = x1 + ux * (pos + seg)
            ey = y1 + uy * (pos + seg)
            pygame.draw.line(surf, color, (sx, sy), (ex, ey), width)
        pos += seg
        drawing = not drawing


def draw_dashed_polyline(surf, points, **kwargs):
    for i in range(len(points) - 1):
        draw_dashed_line(surf, points[i], points[i + 1], **kwargs)


def draw_game_area(surf, rect, font_sm, font_lg):
    draw_box(surf, rect)

    inner = rect.inflate(-16, -16)
    mid_x = inner.centerx

    # Zone labels
    player_label = pygame.Rect(inner.left + 8, inner.top + 8, 72, 28)
    agent_label = pygame.Rect(inner.right - 100, inner.top + 8, 92, 28)
    draw_box(surf, player_label, "Player", font_sm)
    draw_box(surf, agent_label, "Agent Space", font_sm)

    # Vertical centre divider
    draw_dashed_line(
        surf,
        (mid_x, inner.top + 44),
        (mid_x, inner.bottom - 56),
        width=2,
    )

    # L-shaped path: player zone → down left edge → shared space
    path_top = inner.top + 52
    path_left = inner.left + 28
    shared_w, shared_h = 140, 36
    shared_rect = pygame.Rect(
        mid_x - shared_w // 2,
        inner.bottom - shared_h - 10,
        shared_w,
        shared_h,
    )
    draw_dashed_polyline(
        surf,
        [
            (player_label.left + 12, player_label.bottom + 4),
            (path_left, path_top),
            (path_left, shared_rect.centery),
            (shared_rect.left - 4, shared_rect.centery),
        ],
        width=2,
    )

    # Shared space
    draw_box(surf, shared_rect, "Shared Space", font_sm)

    # Player and agent circles
    circle_y = inner.centery - 10
    player_cx = inner.left + inner.width // 4
    agent_cx = inner.right - inner.width // 4
    radius = 52

    for cx, letter in ((player_cx, "P"), (agent_cx, "A")):
        pygame.draw.circle(surf, BG, (cx, circle_y), radius)
        pygame.draw.circle(surf, BORDER, (cx, circle_y), radius, 2)
        draw_text(surf, letter, font_lg, INK, cx, circle_y, anchor="center")


def draw_interaction_box(surf, y, font_sm, font_md):
    x = PAD
    w = W - 2 * PAD
    draw_text(surf, "Interaction Box", font_sm, INK, x, y)

    outer = pygame.Rect(x, y + 22, w, INTERACTION_H - 30)
    draw_box(surf, outer)

    inner = outer.inflate(-20, -20)
    draw_box(surf, inner)

    draw_text(surf, "Agent: .................", font_md, INK, inner.left + 16, inner.top + 14)

    btn_y = inner.bottom - 44
    btn_h = 32
    gap = 10
    yes_w, no_w = 56, 56
    action_w = (inner.width - 32 - yes_w - no_w - 3 * gap) // 2
    bx = inner.left + 16

    for label, bw in (("Yes", yes_w), ("No", no_w), ("Do X....", action_w), ("Do Y....", action_w)):
        btn = pygame.Rect(bx, btn_y, bw, btn_h)
        draw_box(surf, btn, label, font_sm)
        bx += bw + gap

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Shared Autonomy — Wireframe")
    clock = pygame.time.Clock()

    font_sm = pygame.font.SysFont("Arial", 14)
    font_md = pygame.font.SysFont("Arial", 16)
    font_lg = pygame.font.SysFont("Arial", 36, bold=True)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BG)

        game_rect = pygame.Rect(PAD, PAD, W - 2 * PAD, GAME_H)
        draw_game_area(screen, game_rect, font_sm, font_lg)

        interaction_y = PAD + GAME_H + PAD
        draw_interaction_box(screen, interaction_y, font_sm, font_md)

     
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
