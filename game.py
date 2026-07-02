

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

  TODO:
    - Create an agent asking system
"""


pygame.init()
pygamepopup.init()


class ResponiveAgent():
    def __init__(self, list_sprites, goal_location):
        self.sprite_list = list_sprites
        self.goal_location = goal_location
    
    # function that responds to the user c, needs to display the buttons as to asking what can it do for you (each button should have their own item)
    def response():
        



        
    # move the passed in item 
    def move_specified_item(item):
        pass

class Sprite(pygame.sprite.Sprite):
    def __init__(self, height, width, asset):
        super().__init__()

        self.image = pygame.image.load(os.path.join("assests", asset)).convert_alpha()
        self.image = pygame.transform.scale(self.image, (height, width))
        self.rect = self.image.get_rect()
        self.dragging = False
        self.drag_offset = pygame.Vector2(0, 0)
      

        


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
        pygame.sprite.Sprite.__init__(self)  #call Sprite initializer
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location

# Source - https://stackoverflow.com/a/28005796
# Posted by Anthony Pham
# Retrieved 2026-07-02, License - CC BY-SA 3.0

BackGround = Background('assests/floor2png.png', [0,0])



sprite_list = pygame.sprite.Group()
plate = Sprite(45, 45, "platepng.png")
plate.rect.y = 200
plate.rect.x = 300
sprite_list.add(plate)

spoon = Sprite(50,50, "spoonpng.png")
spoon.rect.x= 300
spoon.rect.y = 200
sprite_list.add(spoon)

fork = Sprite(50,50, "forkpng.png")
fork.rect.x = 100
fork.rect.y = 100
sprite_list.add(fork)

knife = Sprite(50,50, "knifepng.png")
knife.rect.x = 100
knife.rect.y = 100
sprite_list.add(knife)

cup = Sprite(50,50, "cuppng.png")
cup.rect.x = 500
cup.rect.y = 475
sprite_list.add(cup)

napkin = Sprite(50,50, "napkinpng.png")
napkin.rect.x = 100
napkin.rect.y = 100
sprite_list.add(napkin)

placemat = Sprite(50,50, "placematpng.png")
placemat.rect.x = 100
placemat.rect.y = 100
sprite_list.add(placemat)


table = Sprite(200,75, "woodpng.png")
table.rect.x = 100
table.rect.y = 100
sprite_list.add(table)


menu_manager = MenuManager(screen=screen)

dragging_sprite = None 

agent = ResponiveAgent(sprite_list, (700, 700))

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
            # Check collision against all sprites in the group
            clicked_sprite = None
            for sprite in sprite_list:
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
            if event.key == pygame.K_a:
                agent.response()

    mouse_x, mouse_y = pygame.mouse.get_pos()
    out_of_bounds = mouse_x >= 600 and mouse_y <= 600
    if out_of_bounds and menu_manager.active_menu is None:
        menu_manager.open_menu(Notibox)
        # print("OUT OF BOUNDS STAY WHERE U CAN REACH")
        if dragging_sprite:
            dragging_sprite.stop_drag()
            dragging_sprite = None
    elif not out_of_bounds:
        menu_manager.close_active_menu()
        # print("BACK IN BOUNDS")

    # fills screen with white
    screen.fill((156,148,146))
    screen.blit(BackGround.image, BackGround.rect)


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
