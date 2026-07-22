import pygame
import math
import sys
import os
from pygamepopup.menu_manager import MenuManager
from pygamepopup.components import Button, InfoBox
import pygamepopup


"""
TODO:
find a them for this game, and find assests, could make it into space theme or just organizing the household objects. food items I already have.
- I found UI asset pack https://www.kenney.nl/assets/ui-pack-sci-fi
Make an agent class, that handles things based on current states of the game. (research into that will be needed)
 - 4 different types of agents (no ask, ask yes and no, ask which option, ask)
 - Proacive and reactive in these different agents
 - Click C to call the agent, asks which task to be done, or asks should i do this yes or no
  - agent does not ask
  - agent asks on its own
make a button class that is reusable to create something that i can use quite often
choose a real game flow, point and drag items acrross the screen, I feel like the task is not going to be very engaging that needs to be discussed more
could go into cleaning the house game/organizer all the different items.
"""

"""
BY EOD:
 set up the task, totally
  - table png //done
  - fork png //done 
  - knife png //done 
  - spoon png //done 
  - placemat //done 
  - cup png //done 
  - napkin png //done 
  - create a place where they are all supposed to go, do not give user access to all of the items, give the agent some of the items that block other items from the user
  contunuing the task 

  Task FLow: 
    Placemat needs to go before the plate, fork, knife, spoon and napkin
    napkin needs to go before fork, spoon and knife go to the left of the plate, on top of placemat.

  TODO:
    - Get the buttons nice and make the task flow an actual thing.
    - bug found when the user brings up the call menu, the player gets soft locked into clicking on an item and cannot escpae for now'

"""


pygame.init()
pygamepopup.init()

pygamepopup.configuration.set_info_box_background("Default/button_square_header_small_rectangle_screws.png")


class ResponiveAgent:
    """Reactive, 'ask which option' agent.

    Holds a set of items in the robot-only zone that the player cannot
    drag out directly. Pressing C opens a menu listing those items; picking
    one starts the agent moving that item to the goal location (the table).
    """

    def __init__(self, held_items, goal_location, menu_manager, speed=350):
        self.held_items = list(held_items)   # Sprites currently blocked in robot space
        self.goal_location = pygame.Vector2(goal_location)
        self.menu_manager = menu_manager
        self.speed = speed                   # px/sec for the delivery animation

        self.choice_box = None
        self.choice_buttons = []
        self.active_item = None              # item currently being delivered
        self.is_delivering = False


    def call(self):
        """Show custom selection buttons in the bottom-left blue area."""
        if self.is_delivering or not self.held_items:
            return

        self.choice_buttons = []
        start_x = 700
        start_y = 650
        button_w = 220
        button_h = 46
        gap = 54

        for index, item in enumerate(self.held_items):
            button = myButton(
                title=item.name,
                x=start_x,
                y=start_y + index * gap,
                width=button_w,
                height=button_h,
                callback=self._make_selector(item),
                font=font,
                image_path="Default/button_square_header_small_rectangle_screws.png",
            )
            self.choice_buttons.append(button)

        self.choice_box = True

    def _make_selector(self, item):
        # each button needs its own callback bound to its own item
        return lambda: self.select_item(item)

    def select_item(self, item):
        if item not in self.held_items:
            return
        self.held_items.remove(item)
        self.active_item = item
        self.is_delivering = True
        self.choice_buttons = []
        self.choice_box = None

    def draw_choice_buttons(self, surface):
        for button in self.choice_buttons:
            button.draw(surface)

    def cancel_choice(self):
        self.choice_buttons = []
        self.choice_box = None

    def update(self, dt):
        if not self.is_delivering or self.active_item is None:
            return

        current = pygame.Vector2(self.active_item.rect.topleft)
        direction = self.goal_location - current
        dist = direction.length()

        if dist < 4:
            self.active_item.rect.topleft = self.goal_location
            self.active_item = None
            self.is_delivering = False
            return

        step = direction.normalize() * min(self.speed * dt, dist)
        self.active_item.rect.topleft = current + step

    @property
    def is_menu_open(self):
        return bool(self.choice_buttons)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, goal: pygame.Vector2, height, width, asset, name=None):
        super().__init__()

        self.popup = InfoBox(
            "Item not dropped in the correct sequence action blocked",
            [[]],
            element_linked = pygame.Rect(0,0,600,600),
            position=(0, 200),
            width=600,
            has_close_button=True,
            background_path="Default/bar_round_large.png"
        )
        self.snapped = False
        self.snap_radius =15
        self.goal = goal
        self.height = height
        self.width = width
        self.image = pygame.image.load(os.path.join("assests", asset)).convert_alpha()
        self.image = pygame.transform.scale(self.image, (height, width))
        self.rect = self.image.get_rect()
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)
        self.name = name or asset
        self.original_position = pygame.Vector2(self.rect.topleft)

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        if self.snapped or (mouse_pos[0] >= 600 and mouse_pos[1] <= 600):
            self.dragging = False
            return
        self.dragging = True
        self.original_position = pygame.Vector2(self.rect.topleft)
        self.drag_offset = pygame.Vector2(mouse_pos) - pygame.Vector2(self.rect.topleft)


        # If the player begins the drag, check to see if the star drag is true, if it is, draw green
        # sqaure or whatever around the goal location, if it is not draw a red one. 
        
    def get_rect(self) -> tuple:
        return(self.goal[0], self.goal[1], self.height, self.width)

    def stop_drag(self) -> None:
        self.dragging = False

    def drag(self, mouse_pos: tuple[int, int]) -> None:
        if not self.dragging:
            return

        self.rect.topleft = pygame.Vector2(mouse_pos) - self.drag_offset
        if self.check_stop():
            if can_place_item(self, sprite_list):
                self.rect.topleft = self.goal
                self.snapped = True
                self.stop_drag()
            else:
                self.rect.topleft = self.original_position
                self.stop_drag()
                menu_manager.open_menu(self.popup)

    def check_stop(self) -> bool:
        dist = math.hypot(self.rect.x - self.goal.x, self.rect.y - self.goal.y)
        return dist < self.snap_radius


def can_place_item(item, sprite_group) -> bool:
    """Enforce the placement order for the table-setting task."""
    if item.name == "Placemat":
        return True

    placemat = next((sprite for sprite in sprite_group if sprite.name == "Placemat"), None)
    if placemat is None or not placemat.snapped:
        return False

    if item.name in {"Plate", "Napkin"}:
        return True

    if item.name in {"Fork", "Knife", "Spoon"}:
        napkin = next((sprite for sprite in sprite_group if sprite.name == "Napkin"), None)
        return napkin is not None and napkin.snapped

    if item.name == "Cup":
        plate = next((sprite for sprite in sprite_group if sprite.name == "Plate"), None)
        return plate is not None and plate.snapped



    return True


screen = pygame.display.set_mode((1200, 840))

try:
    bg_raw = pygame.image.load("assests/floorpng.png").convert_alpha()
    background = pygame.transform.scale(bg_raw, (1200, 800))
except pygame.error as e:
    print(f"Error loading image: {e}")
    sys.exit()


# Helper functin to draw rect
def draw_alpha_rect(screen, color: pygame.Color, rect):
    surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    surf.fill(color)
    screen.blit(surf, (rect[0], rect[1]))




# Source - https://stackoverflow.com/a/28005796
# Posted by Anthony Pham
# Retrieved 2026-07-02, License - CC BY-SA 3.0

class Background(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location

class myButton:
    def __init__(self, title, x, y, width, height, callback, font=None, image_path=None):
        self.title = title
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        self.font = font or pygame.font.SysFont(None, 24)
        self.hovered = False
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (width, height))
            except pygame.error as e:
                print(f"Could not load button image {image_path}: {e}")

    def draw(self, surface):
        if self.image is not None:
            surface.blit(self.image, self.rect)
        else:
            color = (80, 140, 220) if self.hovered else (60, 110, 190)
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=8)

        text_surface = self.font.render(self.title, True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True
        return False

# scaled_floor = pygame.transform.scale('assests/floor.png',1200, 850)
# pygame.image.save(scaled_floor, "scaledfloor.png")
BackGround = Background('assests/bigfloorv3.png', [0, 0])



sprite_list = pygame.sprite.LayeredUpdates()

plate = Sprite(pygame.Vector2(357,644), 100, 75, "platepng.png", name="Plate")
plate.rect.y = 200
plate.rect.x = 300
sprite_list.add(plate)
sprite_list.change_layer(sprite=plate, new_layer=3)


spoon = Sprite(pygame.Vector2(450,654), 60, 60, "spoonpng.png", name="Spoon")
spoon.rect.x = 300
spoon.rect.y = 200
sprite_list.add(spoon)
sprite_list.change_layer(sprite=spoon, new_layer=3)

# # Fork and knife are held by the agent to start: place them inside the
# # robot-only zone (x >= 600, y <= 600) so start_drag already refuses to
# # let the player pull them out directly.
fork = Sprite(pygame.Vector2(306,651),60, 60, "forkpng.png", name="Fork")
fork.rect.x = 700
fork.rect.y = 100
sprite_list.add(fork)
sprite_list.change_layer(sprite=fork, new_layer=3)


knife = Sprite(pygame.Vector2(430,654),60, 60, "knifepng.png", name="Knife")
knife.rect.x = 800
knife.rect.y = 100
sprite_list.add(knife)
sprite_list.change_layer(sprite=knife, new_layer=3)

robot = Sprite(pygame.Vector2(200,248),200, 175, "Armature_Idle_00.png", name="Robot")
robot.rect.x = 100
robot.rect.y = 100
sprite_list.add(robot)
sprite_list.change_layer(sprite=robot, new_layer=0)


cup = Sprite(pygame.Vector2(521, 173), 50, 50, "cuppng.png", name="Cup")
cup.rect.x = 500
cup.rect.y = 475
sprite_list.add(cup)
sprite_list.change_layer(sprite=cup, new_layer=3)

napkin = Sprite(pygame.Vector2(308,650), 60,65, "napkinpng.png", name="Napkin")
napkin.rect.x = 100
napkin.rect.y = 100
sprite_list.add(napkin)
sprite_list.change_layer(sprite=napkin, new_layer=2)


placemat = Sprite(pygame.Vector2(303,633),200, 100, "placematpng.png", name="Placemat")
placemat.rect.x = 100
placemat.rect.y = 100
sprite_list.add(placemat)
sprite_list.change_layer(sprite=placemat, new_layer=1)


# table = Sprite(pygame.Vector2(155,198),500, 400, "woodpng.png", name="Table")
# table.rect.x = 100
# table.rect.y = 100
# sprite_list.add(table)
# sprite_list.change_layer(sprite=table, new_layer=0)


pygame.font.match_font(name="Kenney Future Narrow")
font = pygame.font.Font(filename="Kenney Future Narrow.ttf")
textSurfaceObj = font.render('some text', True, (240,240,240), (115,117,117))

menu_manager = MenuManager(screen=screen)

dragging_sprite = None

# goal_location is where delivered items should land, e.g. beside the table
agent = ResponiveAgent(
    held_items=[fork, knife],
    goal_location=(750, 700),
    menu_manager=menu_manager,
)

Notibox = InfoBox(
    "Robot Space access only",
    [[]],
    element_linked=pygame.Rect(600, 0, 600, 600),
    position=(600, 200),
    width=600,
    has_close_button=False,
)

running = True
clock = pygame.time.Clock()
highlight_rect = None
highlight_color = pygame.Color(0, 220, 0, 50)

while running:
    dt = clock.tick(60) / 1000  # seconds since last frame, needed for agent movement speed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if agent.is_menu_open:
                for button in agent.choice_buttons:
                    if button.handle_event(event):
                        break
                else:
                    menu_manager.click(event.button, event.pos)
            else:
                clicked_sprite = None
                for sprite in sprite_list:
                    if getattr(sprite, "snapped", False): 
                        continue
                    if sprite.rect.collidepoint(event.pos):
                        clicked_sprite = sprite
                        break

                if clicked_sprite:
                    dragging_sprite = clicked_sprite
                    dragging_sprite.start_drag(event.pos)
                else:
                    menu_manager.click(event.button, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if dragging_sprite:
                dragging_sprite.stop_drag()
                highlight_rect = None
                highlight_color = pygame.Color(0,0,0,0)
                print(f"{dragging_sprite.name} final position: ({dragging_sprite.rect.x}, {dragging_sprite.rect.y})")
                dragging_sprite = None
        elif event.type == pygame.MOUSEMOTION:
            if agent.is_menu_open:
                for button in agent.choice_buttons:
                    button.handle_event(event)
            if dragging_sprite:
                if can_place_item(dragging_sprite, sprite_list):
                    # pygame.draw.rect(screen, pygame.Color(0,220,0,a=0), dragging_sprite.get_rect())
                    # draw_alpha_rect(screen, pygame.Color(0,220,0,a=50),  dragging_sprite.get_rect())
                    # pygame.display.flip()
                    highlight_color = pygame.Color(0, 220, 0, 50)
                    highlight_rect = dragging_sprite.get_rect()
                    
                    print("show green")
                elif not can_place_item(dragging_sprite, sprite_list):
                    highlight_color = pygame.Color(220, 0, 0, 50)
                    highlight_rect = dragging_sprite.get_rect()
                    print("show red here")
                dragging_sprite.drag(event.pos)
            if not dragging_sprite and not agent.is_menu_open:
                menu_manager.motion(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                agent.call()
            elif event.key == pygame.K_ESCAPE:
                agent.cancel_choice()

    agent.update(dt)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    out_of_bounds = mouse_x >= 600 and mouse_y <= 600

    
    if out_of_bounds and menu_manager.active_menu is None:
        menu_manager.open_menu(Notibox)
        if dragging_sprite:
            dragging_sprite.stop_drag()
            dragging_sprite = None
    elif not out_of_bounds and menu_manager.active_menu is Notibox:
        menu_manager.close_active_menu()

    # screen.fill((156, 148, 146))
    screen.blit(BackGround.image, BackGround.rect)
    

    # blues1 = pygame.draw.rect(screen, (0, 0, 255), (0, 600, 1200, 250), width=2, border_radius=-1)
    # pygame.draw.rect(screen, (0, 0, 0), (0, 0, 600, 600), width=2, border_radius=-1)
    pygame.draw.rect(screen, (255, 0, 0), (600, 0, 600, 600), width=2, border_radius=-1)

    sprite_list.update()
    sprite_list.draw(screen)
    if highlight_rect:
        draw_alpha_rect(screen, highlight_color, highlight_rect)
    agent.draw_choice_buttons(screen)
    menu_manager.display()
   
    pygame.display.flip()


pygame.quit()
sys.exit()