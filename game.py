import pygame
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
    - Create an agent asking system  -> DONE below (reactive / "ask which option" variant)
"""


pygame.init()
pygamepopup.init()


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
        self.active_item = None              # item currently being delivered
        self.is_delivering = False

    # --- called on 'C' keypress -----------------------------------------

    def call(self):
        """Open the 'which item do you need' menu. No-op if already
        delivering something or nothing left to give."""
        if self.is_delivering or not self.held_items:
            return

        buttons = [
            [Button(title=item.name, callback=self._make_selector(item))]
            for item in self.held_items
        ]

        self.choice_box = InfoBox(
            "Which item do you need?",
            buttons,
            position=(350, 500),
            width=400,
            has_close_button=True,
            element_linked=blues1
        )
        self.menu_manager.open_menu(self.choice_box)

    def _make_selector(self, item):
        # each button needs its own callback bound to its own item
        return lambda: self.select_item(item)

    def select_item(self, item):
        if item not in self.held_items:
            return
        self.held_items.remove(item)
        self.active_item = item
        self.is_delivering = True
        self.menu_manager.close_active_menu()
        self.choice_box = None

    # --- called once per frame from the main loop -------------------------

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
        return self.choice_box is not None


class Sprite(pygame.sprite.Sprite):
    def __init__(self, height, width, asset, name=None):
        super().__init__()

        self.image = pygame.image.load(os.path.join("assests", asset)).convert_alpha()
        self.image = pygame.transform.scale(self.image, (height, width))
        self.rect = self.image.get_rect()
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)
        self.name = name or asset  # used as the button label in the agent menu

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        if mouse_pos[0] >= 600 and mouse_pos[1] <= 600:
            self.dragging = False
            return
        self.dragging = True
        self.drag_offset = pygame.Vector2(mouse_pos) - pygame.Vector2(self.rect.topleft)

    def stop_drag(self) -> None:
        self.dragging = False

    def drag(self, mouse_pos: tuple[int, int]) -> None:
        if self.dragging:
            self.rect.topleft = pygame.Vector2(mouse_pos) - self.drag_offset


screen = pygame.display.set_mode((1200, 850))

try:
    bg_raw = pygame.image.load("assests/floorpng.png").convert_alpha()
    background = pygame.transform.scale(bg_raw, (1200, 850))
except pygame.error as e:
    print(f"Error loading image: {e}")
    sys.exit()


# Source - https://stackoverflow.com/a/28005796
# Posted by Anthony Pham
# Retrieved 2026-07-02, License - CC BY-SA 3.0

class Background(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location


BackGround = Background('assests/floor2png.png', [0, 0])


sprite_list = pygame.sprite.LayeredUpdates()

plate = Sprite(45, 45, "platepng.png", name="Plate")
plate.rect.y = 200
plate.rect.x = 300
sprite_list.add(plate)
sprite_list.change_layer(sprite=plate, new_layer=2)


spoon = Sprite(50, 50, "spoonpng.png", name="Spoon")
spoon.rect.x = 300
spoon.rect.y = 200
sprite_list.add(spoon)
sprite_list.change_layer(sprite=spoon, new_layer=2)

# Fork and knife are held by the agent to start: place them inside the
# robot-only zone (x >= 600, y <= 600) so start_drag already refuses to
# let the player pull them out directly.
fork = Sprite(50, 50, "forkpng.png", name="Fork")
fork.rect.x = 700
fork.rect.y = 100
sprite_list.add(fork)
sprite_list.change_layer(sprite=fork, new_layer=2)


knife = Sprite(50, 50, "knifepng.png", name="Knife")
knife.rect.x = 800
knife.rect.y = 100
sprite_list.add(knife)
sprite_list.change_layer(sprite=knife, new_layer=2)


cup = Sprite(50, 50, "cuppng.png", name="Cup")
cup.rect.x = 500
cup.rect.y = 475
sprite_list.add(cup)
sprite_list.change_layer(sprite=cup, new_layer=2)

napkin = Sprite(50, 50, "napkinpng.png", name="Napkin")
napkin.rect.x = 100
napkin.rect.y = 100
sprite_list.add(napkin)
sprite_list.change_layer(sprite=napkin, new_layer=2)


placemat = Sprite(50, 50, "placematpng.png", name="Placemat")
placemat.rect.x = 100
placemat.rect.y = 100
sprite_list.add(placemat)
sprite_list.change_layer(sprite=placemat, new_layer=1)


table = Sprite(500, 400, "woodpng.png", name="Table")
table.rect.x = 100
table.rect.y = 100
sprite_list.add(table)
sprite_list.change_layer(sprite=table, new_layer=0)


print(pygame.font.get_fonts())
pygame.font.match_font(name="Kenney Future Narrow")
font = pygame.font.Font(filename="Kenney Future Narrow.ttf")
textSurfaceObj = font.render('some text', True, (240,240,240), (115,117,117))

menu_manager = MenuManager(screen=screen)

dragging_sprite = None

# goal_location is where delivered items should land, e.g. beside the table
agent = ResponiveAgent(
    held_items=[fork, knife],
    goal_location=(350, 260),
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

while running:
    dt = clock.tick(60) / 1000  # seconds since last frame, needed for agent movement speed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_sprite = None
            for sprite in sprite_list:
                if sprite is table:  # Skip table — it's not draggable
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
                dragging_sprite = None
        elif event.type == pygame.MOUSEMOTION:
            if dragging_sprite:
                dragging_sprite.drag(event.pos)
            if not dragging_sprite:
                menu_manager.motion(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                agent.call()

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

    screen.fill((156, 148, 146))
    screen.blit(BackGround.image, BackGround.rect)

    blues1 = pygame.draw.rect(screen, (0, 0, 255), (0, 600, 1200, 250), width=2, border_radius=-1)
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, 600, 600), width=2, border_radius=-1)
    pygame.draw.rect(screen, (255, 0, 0), (600, 0, 600, 600), width=2, border_radius=-1)

    sprite_list.update()
    sprite_list.draw(screen)
    menu_manager.display()
    screen.blit(textSurfaceObj, (100, 50))  # Display your rendered tex
    pygame.display.flip()


pygame.quit()
sys.exit()