import pygame

# --- Global Constants ---
WIDTH, HEIGHT = 768, 768
FPS = 60

# Colors
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
RED     = (255, 0, 0)
GREEN   = (0, 255, 0)
BLUE    = (65, 65, 255)
YELLOW  = (255, 255, 0)
PURPLE  = (200, 0, 200)

# Collision boundary (scaled)
COLLISION_RATIO = 837 / 1024
collision_width = int(WIDTH * COLLISION_RATIO)
collision_height = int(HEIGHT * COLLISION_RATIO)
collision_x = (WIDTH - collision_width) // 2
collision_y = (HEIGHT - collision_height) // 2
COLLISION_RECT = pygame.Rect(collision_x, collision_y, collision_width, collision_height)
