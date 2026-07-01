

import pygame
import sys
import os

screen = pygame.display.set_mode((1200, 800))

oven = pygame.image.load(os.path.join("assests", "Horno.png"))

scaled_oven = pygame.transform.scale(oven, (150,200))

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((255,255,255))


    screen.blit(scaled_oven, (100, 600))

    pygame.display.flip()


pygame.quit()
sys.exit()
