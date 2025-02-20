import pygame
from .settings import WIDTH, HEIGHT, WHITE, BLACK

class Button:
    def __init__(self, x, y, width, height, text, font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.color = WHITE
        self.hover_color = (200, 200, 200)
        self.text_color = BLACK
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)  # Border
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

def draw_title_screen(surface):
    # Draw title
    font_big = pygame.font.Font(None, 64)
    font_small = pygame.font.Font(None, 32)
    
    title = font_big.render("Boss Battle", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH/2, HEIGHT/4))
    
    # Instructions
    instructions = [
        "Left Click - Shoot",
        "WASD/Arrow Keys - Move",
        "Spacebar - Roll (with immunity)",
        "",
        "Click anywhere to start"
    ]
    
    surface.fill(BLACK)
    surface.blit(title, title_rect)
    
    for i, text in enumerate(instructions):
        instruction = font_small.render(text, True, WHITE)
        instruction_rect = instruction.get_rect(
            center=(WIDTH/2, HEIGHT/2 + i * 40)
        )
        surface.blit(instruction, instruction_rect)

def draw_death_screen(surface, buttons):
    # Draw "Game Over" text
    font_big = pygame.font.Font(None, 64)
    game_over = font_big.render("Game Over", True, WHITE)
    game_over_rect = game_over.get_rect(center=(WIDTH/2, HEIGHT/3))
    
    surface.fill(BLACK)
    surface.blit(game_over, game_over_rect)
    
    # Draw buttons
    for button in buttons:
        button.draw(surface)

def draw_win_screen(surface):
    font = pygame.font.Font(None, 74)
    text = font.render("Congratulations!", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2))
    surface.blit(text, text_rect)
    
    font = pygame.font.Font(None, 36)
    subtext = font.render("You defeated the boss!", True, (255, 255, 255))
    subtext_rect = subtext.get_rect(center=(WIDTH/2, HEIGHT/2 + 50))
    surface.blit(subtext, subtext_rect) 