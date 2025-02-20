import pygame
from .settings import WIDTH, HEIGHT, COLLISION_RECT, BLUE, WHITE, RED

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.base_color = BLUE
        self.roll_color = WHITE
        self.image = pygame.Surface((20, 20))
        self.image.fill(self.base_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.rolling = False
        self.roll_timer = 0
        self.roll_cooldown = 0  # New: track roll cooldown
        self.roll_cooldown_duration = 0.8  # New: 0.8 seconds cooldown
        self.roll_direction = pygame.math.Vector2(0, 0)
        self.last_dir = pygame.math.Vector2(0, 0)
        self.hearts = 3
        self.invulnerable_timer = 0  # Changed from 0.5s to 1.5s after hit
        self.post_roll_invulnerable = 0  # New timer for post-roll invulnerability
        self.damage_flash_time = 0
        self.original_image = self.image.copy()
        self.debug_invulnerable = False  # Add debug flag

    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if not self.rolling:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -self.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = self.speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -self.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = self.speed

            move_vector = pygame.math.Vector2(dx, dy)
            if move_vector.length() != 0:
                self.last_dir = move_vector.normalize()
            self.rect.x += dx
            self.rect.y += dy
            
            # Update post-roll invulnerability
            if self.post_roll_invulnerable > 0:
                self.post_roll_invulnerable -= dt
        else:
            roll_speed = self.speed * 1.5
            self.rect.x += self.roll_direction.x * roll_speed
            self.rect.y += self.roll_direction.y * roll_speed
            self.roll_timer -= dt
            if self.roll_timer <= 0:
                self.rolling = False
                self.image.fill(self.base_color)
                self.post_roll_invulnerable = 0.5  # Add 0.5s invulnerability after roll
                self.roll_cooldown = self.roll_cooldown_duration  # Start cooldown when roll ends

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

        # Update damage flash
        if self.damage_flash_time > 0:
            self.damage_flash_time -= dt
            if int(self.damage_flash_time * 15) % 2:  # Flash red rapidly
                self.image.fill(RED)
            else:
                self.image.fill(self.base_color)
        
        # Make player flash when invulnerable
        if (self.invulnerable_timer > 0 or self.rolling or self.post_roll_invulnerable > 0):
            if int(pygame.time.get_ticks() / 100) % 2:
                self.image.set_alpha(128)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        # Clamp within the collision boundary
        self.rect.clamp_ip(COLLISION_RECT)

        # Update roll cooldown
        if self.roll_cooldown > 0:
            self.roll_cooldown -= dt

    def take_damage(self):
        if self.debug_invulnerable:
            return False
        
        if self.invulnerable_timer <= 0:
            self.hearts -= 1
            self.invulnerable_timer = 1.5
            self.damage_flash_time = 0.3
            return True
        return False

    def is_invulnerable(self):
        return (self.invulnerable_timer > 0 or 
                self.rolling or 
                self.post_roll_invulnerable > 0)

    def can_roll(self):
        return not self.rolling and self.roll_cooldown <= 0

    def reset(self):
        """Reset player to initial state"""
        # Reset position
        self.rect.centerx = WIDTH/2
        self.rect.bottom = HEIGHT - 50
        
        # Reset state
        self.hearts = 3
        self.rolling = False
        self.roll_timer = 0
        self.roll_cooldown = 0
        self.roll_direction = pygame.math.Vector2(0, 0)
        self.last_dir = pygame.math.Vector2(0, 0)
        self.invulnerable_timer = 0
        self.post_roll_invulnerable = 0
        self.damage_flash_time = 0
        
        # Reset appearance
        self.image.fill(self.base_color)
        self.image.set_alpha(255)
