import sys
import pygame

# Initialize all core Pygame modules
pygame.init()

# Setup game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Create the display window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My First Pygame Project")

# Define color constants (RGB format)
BG_COLOR = (40, 40, 50) # Dark grayish-blue

# Create a clock object to manage frame rate
clock = pygame.time.Clock()

def main():
    
    running = True
    
    # --- MAIN GAME LOOP ---
    while running:
        # 1. Event Handling (Inputs)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # 2. Game Logic / State Updates Updates go here
        
        # 3. Drawing / Rendering
        screen.fill(BG_COLOR) # Clear screen with background color
        
        # (Draw your game objects here)
        
        pygame.display.flip() # Swap buffers to display the new frame
        
        # Cap the frame rate
        clock.tick(FPS)

    # Clean up and exit cleanly
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
