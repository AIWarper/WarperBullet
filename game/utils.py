import pygame
import random
import math
from .settings import RED, WHITE

def draw_heart(surface, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surface, color, (int(x - r), int(y - r)), r)
    pygame.draw.circle(surface, color, (int(x + r), int(y - r)), r)
    point1 = (int(x - size/2), int(y - r/2))
    point2 = (int(x), int(y + size/2))
    point3 = (int(x + size/2), int(y - r/2))
    pygame.draw.polygon(surface, color, [point1, point2, point3])

def draw_hearts(surface, hearts, max_hearts=3):
    heart_size = 30
    spacing = 5
    for i in range(max_hearts):
        pos_x = 10 + i*(heart_size + spacing) + heart_size//2
        pos_y = 10 + heart_size//2
        if i < hearts:
            draw_heart(surface, pos_x, pos_y, heart_size, RED)
        else:
            draw_heart(surface, pos_x, pos_y, heart_size, (100, 100, 100))

class ScreenShake:
    def __init__(self):
        self.duration = 0
        self.intensity = 0
        self.offset = pygame.math.Vector2(0, 0)

    def start_shake(self, duration, intensity):
        self.duration = duration
        self.intensity = intensity

    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            # Generate random offset based on intensity
            self.offset.x = random.uniform(-self.intensity, self.intensity)
            self.offset.y = random.uniform(-self.intensity, self.intensity)
            if self.duration <= 0:
                self.offset = pygame.math.Vector2(0, 0)
        return self.offset

class Impact(pygame.sprite.Sprite):
    def __init__(self, pos, color=WHITE):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.lifetime = 0.2  # Effect lasts 0.2 seconds
        self.particles = []
        
        # Create 8 particles in a star pattern
        for angle in range(0, 360, 45):
            speed = random.uniform(2, 5)
            rad = math.radians(angle + random.uniform(-10, 10))
            velocity = pygame.math.Vector2(
                speed * math.cos(rad),
                speed * math.sin(rad)
            )
            size = random.randint(2, 4)
            self.particles.append({
                'pos': self.pos.copy(),
                'vel': velocity,
                'size': size,
                'alpha': 255
            })

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        fade_speed = 255 / 0.2  # Fade from 255 to 0 over lifetime
        
        for p in self.particles:
            p['pos'] += p['vel']
            p['alpha'] = max(0, p['alpha'] - fade_speed * dt)

    def draw(self, surface):
        for p in self.particles:
            alpha = int(p['alpha'])
            if alpha <= 0:
                continue
                
            particle_surface = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surface,
                (*WHITE, alpha),
                (p['size']//2, p['size']//2),
                p['size']//2
            )
            surface.blit(particle_surface, p['pos'])
