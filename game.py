

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
Make an angent class, that handles things based on current states of the game. (research into that will be needed)
 - 4 different types of agents (no ask, ask yes and no, ask which option, ask)
 - Proacive and reactive in these different agents
make a button class that is reusable to create something that i can use quite often
choose a real game flow, point and drag items acrross the screen, I feel like the task is not going to be very engaging that needs to be discussed more
could go into cleaning the house game/organizer all the different items.
"""

"""
BY EOD:
put an item around and click and drag it and it needs to be bound by the rectangles, make the button class
"""


pygame.init()
pygamepopup.init()

class Sprite(pygame.sprite.Sprite):
    def __init__(self, color, height, width):
        super().__init__()

        self.image = pygame.image.load(os.path.join("assests", "Horno.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)

    def start_drag(self, mouse_pos: tuple[int, int]) -> None:
        self.dragging = True
        self.drag_offset = pygame.Vector2(mouse_pos) - pygame.Vector2(self.rect.topleft)

    def stop_drag(self) -> None:
        self.dragging = False

    def drag(self, mouse_pos: tuple[int, int]) -> None:
        if self.dragging:
            self.rect.topleft = pygame.Vector2(mouse_pos) - self.drag_offset


screen = pygame.display.set_mode((1200, 850))

sprite_list = pygame.sprite.Group()
object_ = Sprite((255,0,0), 30, 30)
object_.rect.y = 200
object_.rect.x = 300
sprite_list.add(object_)

menu_manager = MenuManager(screen=screen)
oven = pygame.image.load(os.path.join("assests", "Horno.png"))

scaled_oven = pygame.transform.scale(oven, (150,200))

Notibox = InfoBox(
    "Robot Space access only",
    [[]],
    element_linked=pygame.Rect(600, 0, 600, 600),
    position=(600,200),
    width= 600,
    has_close_button=False,

)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if object_.rect.collidepoint(event.pos):
                object_.start_drag(event.pos)
            else:
                menu_manager.click(event.button, event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            object_.stop_drag()
        elif event.type == pygame.MOUSEMOTION:
            object_.drag(event.pos)
            if not object_.dragging:
                menu_manager.motion(event.pos)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    out_of_bounds = mouse_x >= 600 and mouse_y <= 600
    if out_of_bounds and menu_manager.active_menu is None:
        menu_manager.open_menu(Notibox)
        print("OUT OF BOUNDS STAY WHERE U CAN REACH")
    elif not out_of_bounds:
        menu_manager.close_active_menu()
        print("BACK IN BOUNDS")

    # fills screen with white
    screen.fill((156,148,146))


    #interaction box outline
    pygame.draw.rect(screen, (0,0,255), (0,600,1200,250), width=2, border_radius=-1)
    pygame.draw.rect(screen, (0,0,0), (0,0,600,600), width=2, border_radius=-1)
    pygame.draw.rect(screen, (255,0,0), (600,0,600,600), width=2, border_radius=-1)

    #screen.blit(scaled_oven, (100, 600))

    sprite_list.update()
    sprite_list.draw(screen)
    menu_manager.display()
    pygame.display.flip()


pygame.quit()
sys.exit()
