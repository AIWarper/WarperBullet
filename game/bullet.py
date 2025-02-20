import pygame
import math
from .settings import WIDTH

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, color, radius=5):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(velocity)
        self._radius = radius  # Use private variable for radius
        self.color = color
        self._update_image()  # Create initial image
        self.rect = self.image.get_rect(center=self.pos)

    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value):
        self._radius = value
        self._update_image()  # Update image when radius changes
        
    def _update_image(self):
        # Create a larger surface to accommodate the glow
        glow_radius = self._radius * 2
        self.image = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        
        # Draw the outer glow
        glow_color = (*self.color[:3], 40)
        pygame.draw.circle(self.image, glow_color, (glow_radius, glow_radius), glow_radius)
        
        # Draw a medium glow
        medium_radius = int(self._radius * 1.5)
        medium_color = (*self.color[:3], 90)
        pygame.draw.circle(self.image, medium_color, (glow_radius, glow_radius), medium_radius)
        
        # Draw the main bullet
        pygame.draw.circle(self.image, self.color, (glow_radius, glow_radius), self._radius)
        
        # Update rect size
        self.rect = self.image.get_rect(center=self.pos)

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        if (self.pos.x < -10 or self.pos.x > WIDTH+10 or
            self.pos.y < -10 or self.pos.y > WIDTH+10):
            self.kill()
