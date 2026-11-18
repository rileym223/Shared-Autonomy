"""Tutorial-scene can sorting game with player and robot interaction."""

import os
import sys

import pygame


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_WIDTH = 1200
SCREEN_SIZE = (1500, 840)
PLAYER_SPEED = 250
PLAYER_PICKUP_RADIUS = 60
ROBOT_SPEED = 350
FPS = 60
SORT_ZONE = pygame.Rect(577, 19, 140, 190)

# Robot delivery positions are inside the bin shown in Tutorial.png.
CAN_GOALS = {
    "Red Can": (590, 60),
    "Blue Can": (617, 55),
    "Silver Can": (665, 65),
}
ROBOT_WAYPOINTS = (
    (1050, 680),
    (1050, 500),
    (950, 400),
    (850, 320),
    (750, 280),
    (650, 250),
    (555, 250),
)


def asset_path(*parts):
    return os.path.join(BASE_DIR, *parts)


class Can(pygame.sprite.Sprite):
    def __init__(self, name, filename, goal, position, size):
        super().__init__()
        image = pygame.image.load(asset_path("assests", filename)).convert_alpha()
        self.image = pygame.transform.smoothscale(image, size)
        self.rect = self.image.get_rect(topleft=position)
        self.name = name
        self.goal = pygame.Vector2(goal)
        self.spawn = pygame.Vector2(position)
        self.placed = False
        self.size = size


class MovingCharacter(pygame.sprite.Sprite):
    def __init__(self, filename, position, size):
        super().__init__()
        image = pygame.image.load(asset_path("assests", filename)).convert_alpha()
        self.image = pygame.transform.smoothscale(image, size)
        self.rect = self.image.get_rect(topleft=position)


class RobotAssistant:
    IDLE = "idle"
    TO_CAN = "to_can"
    TO_GOAL = "to_goal"
    RETURNING = "returning"

    def __init__(self, robot, cans):
        self.robot = robot
        self.held_cans = list(cans)
        self.active_can = None
        self.phase = self.IDLE
        self.menu_open = False
        self.buttons = []
        self.path = []
        self.carry_offset = pygame.Vector2()
        self.home = pygame.Vector2(robot.rect.topleft)

    @property
    def delivering(self):
        return self.phase != self.IDLE

    def open_menu(self):
        if self.delivering:
            return
        self.menu_open = True
        self.buttons = []
        for index, can in enumerate(self.held_cans):
            rect = pygame.Rect(1218, 70 + index * 64, 264, 48)
            self.buttons.append((rect, can))

    def select(self, can):
        if can not in self.held_cans or self.delivering:
            return
        self.menu_open = False
        self.buttons = []
        self.active_can = can
        self.phase = self.TO_CAN
        self.path = self._build_path(can.rect.topleft)

    def player_take(self, can):
        if can in self.held_cans:
            self.held_cans.remove(can)

    def _build_path(self, destination):
        start = pygame.Vector2(self.robot.rect.topleft)
        target = pygame.Vector2(destination)
        waypoints = [pygame.Vector2(point) for point in ROBOT_WAYPOINTS]
        start_index = min(range(len(waypoints)), key=lambda i: waypoints[i].distance_to(start))
        end_index = min(range(len(waypoints)), key=lambda i: waypoints[i].distance_to(target))
        route = (
            waypoints[start_index : end_index + 1]
            if start_index <= end_index
            else list(reversed(waypoints[end_index : start_index + 1]))
        )
        path = [point for point in route if point.distance_to(start) > 12]
        if not path or path[-1].distance_to(target) > 4:
            path.append(target)
        else:
            path[-1] = target
        return path

    def _follow_path(self, dt):
        if not self.path:
            return True
        target = self.path[0]
        current = pygame.Vector2(self.robot.rect.topleft)
        offset = target - current
        distance = offset.length()
        if distance <= 4:
            self.robot.rect.topleft = target
            self.path.pop(0)
            return not self.path
        self.robot.rect.topleft = current + offset.normalize() * min(
            ROBOT_SPEED * dt, distance
        )
        if pygame.Vector2(self.robot.rect.topleft).distance_to(target) <= 4:
            self.path.pop(0)
            return not self.path
        return False

    def update(self, dt):
        if self.phase == self.IDLE:
            return
        if self.phase == self.TO_CAN:
            if self._follow_path(dt):
                can = self.active_can
                if can is None:
                    return
                self.held_cans.remove(can)
                self.carry_offset = (
                    pygame.Vector2(can.rect.topleft)
                    - pygame.Vector2(self.robot.rect.topleft)
                )
                self.phase = self.TO_GOAL
                self.path = self._build_path(can.goal - self.carry_offset)
        elif self.phase == self.TO_GOAL:
            can = self.active_can
            if can is None:
                return
            done = self._follow_path(dt)
            can.rect.topleft = pygame.Vector2(self.robot.rect.topleft) + self.carry_offset
            if SORT_ZONE.contains(can.rect):
                can.placed = True
                can.kill()
                self.active_can = None
                self.phase = self.RETURNING
                self.path = self._build_path(self.home)
            elif done:
                can.rect.topleft = can.goal
                if SORT_ZONE.contains(can.rect):
                    can.placed = True
                    can.kill()
                    self.active_can = None
                    self.phase = self.RETURNING
                    self.path = self._build_path(self.home)
        elif self.phase == self.RETURNING and self._follow_path(dt):
            self.phase = self.IDLE

    def draw_menu(self, surface, font):
        if not self.menu_open:
            return
        for rect, can in self.buttons:
            pygame.draw.rect(surface, (54, 76, 104), rect, border_radius=6)
            pygame.draw.rect(surface, (170, 200, 230), rect, width=2, border_radius=6)
            surface.blit(font.render(can.name, True, (245, 245, 245)), (rect.x + 12, rect.y + 13))

    def draw_panel(self, surface, font):
        panel = pygame.Rect(FIELD_WIDTH, 0, SCREEN_SIZE[0] - FIELD_WIDTH, SCREEN_SIZE[1])
        pygame.draw.rect(surface, (20, 28, 40), panel)
        pygame.draw.line(surface, (120, 155, 190), panel.topleft, (panel.x, panel.bottom), 2)
        surface.blit(font.render("Robot assistance", True, (240, 240, 240)), (1218, 18))
        if self.delivering:
            label = f"Delivering {self.active_can.name}" if self.active_can else "Returning to start"
            surface.blit(font.render(label, True, (200, 215, 230)), (1218, 42))
        elif not self.held_cans:
            surface.blit(font.render("No cans left for the robot", True, (200, 215, 230)), (1218, 48))
        elif not self.menu_open:
            surface.blit(font.render("Press C to choose a can", True, (200, 215, 230)), (1218, 48))
        self.draw_menu(surface, font)


def draw_sort_zone(surface):
    pygame.draw.rect(surface, (90, 220, 125), SORT_ZONE, width=3, border_radius=8)


def draw_pickup_area(surface, center, radius):
    area = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    area_center = pygame.Vector2(radius + 2, radius + 2)
    pygame.draw.circle(area, (55, 190, 220, 32), area_center, radius)
    pygame.draw.circle(area, (120, 230, 245, 210), area_center, radius, width=3)
    surface.blit(area, (center[0] - radius - 2, center[1] - radius - 2))


def place_player_can(can, status):
    if not can:
        return None, status
    if SORT_ZONE.contains(can.rect):
        can.placed = True
        can.kill()
        return None, f"{can.name} placed."
    return can, "Move the whole can inside the outlined bin to place it."


def main():
    pygame.init()
    pygame.display.set_caption("Tutorial Can Sorting")
    screen = pygame.display.set_mode(SCREEN_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 20)
    field_bounds = pygame.Rect(0, 0, FIELD_WIDTH, SCREEN_SIZE[1])

    background_image = pygame.image.load(asset_path("Tutorial.png")).convert()
    background = pygame.transform.scale(background_image, field_bounds.size)
    player = MovingCharacter("person011.png", (165, 680), (70, 98))
    robot = MovingCharacter("Armature_Idle_00.png", (1010, 635), (150, 184))
    cans = [
        Can("Red Can", "redcan.png", CAN_GOALS["Red Can"], (460, 740), (38, 62)),
        Can("Blue Can", "bluecan.png", CAN_GOALS["Blue Can"], (520, 700), (60, 100)),
        Can("Silver Can", "silvercan.png", CAN_GOALS["Silver Can"], (605, 740), (38, 62)),
    ]
    sprites = pygame.sprite.LayeredUpdates(*cans, player, robot)
    sprites.change_layer(robot, 0)
    assistant = RobotAssistant(robot, cans[1:])
    carried_can = None
    carry_offset = pygame.Vector2()
    status = "WASD move; E places your can; C calls the robot."
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    assistant.open_menu()
                elif event.key == pygame.K_ESCAPE:
                    assistant.menu_open = False
                    assistant.buttons = []
                elif event.key == pygame.K_e and carried_can is not None:
                    carried_can, status = place_player_can(carried_can, status)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                
                print(f"Mouse clicked at: {event.pos}")
                clicked_button = next(
                    (can for rect, can in assistant.buttons if rect.collidepoint(event.pos)),
                    None,
                )
                if clicked_button is not None:
                    assistant.select(clicked_button)
                    continue
                if assistant.menu_open:
                    assistant.menu_open = False
                    assistant.buttons = []
                    continue
                if event.pos[0] < FIELD_WIDTH and robot.rect.collidepoint(event.pos):
                    assistant.open_menu()

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            keys[pygame.K_d] - keys[pygame.K_a],
            keys[pygame.K_s] - keys[pygame.K_w],
        )
        if movement.length_squared():
            movement = movement.normalize() * PLAYER_SPEED * dt
            player.rect.x += round(movement.x)
            player.rect.y += round(movement.y)
            player.rect.clamp_ip(field_bounds)

        player_center = pygame.Vector2(player.rect.center)
        if carried_can is None and not assistant.menu_open:
            nearby = [
                can
                for can in cans
                if not can.placed
                and can is not assistant.active_can
                and pygame.Vector2(can.rect.center).distance_to(player_center)
                <= PLAYER_PICKUP_RADIUS
            ]
            if nearby:
                carried_can = min(
                    nearby,
                    key=lambda can: pygame.Vector2(can.rect.center).distance_squared_to(
                        player_center
                    ),
                )
                assistant.player_take(carried_can)
                carry_offset = pygame.Vector2(carried_can.rect.center) - player_center
                status = f"Carrying {carried_can.name}; move it to the marked target or use E."
        if carried_can is not None:
            carried_can.rect.center = player_center + carry_offset
            if SORT_ZONE.contains(carried_can.rect):
                carried_can, status = place_player_can(carried_can, status)
        assistant.update(dt)
        screen.blit(background, (0, 0))
        draw_sort_zone(screen)
        draw_pickup_area(screen, player.rect.center, PLAYER_PICKUP_RADIUS)
        sprites.draw(screen)
        assistant.draw_panel(screen, font)
        screen.blit(font.render(status, True, (30, 35, 40)), (16, 16))
        if all(can.placed for can in cans):
            screen.blit(font.render("Sorting complete!", True, (30, 150, 70)), (16, 44))
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
