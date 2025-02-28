import pygame
import math
import random
from .settings import WIDTH, HEIGHT, PURPLE, RED, GREEN, YELLOW, WHITE, COLLISION_RECT
from .bullet import Bullet

class Boss:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 40
        self.health = 700
        self.state = "intro"
        self.state_timer = 0
        self.attack_cooldown = 0
        self.charge_time = 0
        self.exploded = False
        self.in_gauntlet = False
        self.gauntlet_timer = 0
        self.gauntlet_fire_interval = 0.2
        self.gauntlet_fire_timer = 0
        self.gauntlet_angle = 0
        self.gauntlet_direction = 1
        self.gauntlet_switch_timer = 2
        self.last_attack = None
        self.attack_repeat_count = 0
        self.phase2 = False
        self.intermission_delay = 0
        self.melee_cooldown = 0
        self.melee_flash_timer = 0
        self.hit_flash = 0
        self.base_color = (200, 0, 200)
        self.current_color = [200, 0, 200]
        
        # Particle division attributes
        self.particle_division_stage = 0
        self.particle_timers = []
        self.particle_positions = []
        self.particle_velocities = []
        self.spiral_angles = []
        self.corner_particles = []
        self.corner_positions = []
        self.corner_pulse_timer = 0
        self.corner_pulse_scale = 1.0
        self.is_pulsing = False
        
        # Attack selection system
        self.all_attacks = ["random_spread", "wide_spread", "charge_attack", "particle_division"]
        self.available_attacks = self.all_attacks.copy()  # Now this will work
        
        # Add intro sequence attributes
        self.intro_timer = 3.0  # 3 second intro
        self.intro_start_pos = pygame.math.Vector2(x, 50)  # Start higher up
        self.intro_target_pos = pygame.math.Vector2(WIDTH/2, HEIGHT/2)  # Center position
        self.pos = self.intro_start_pos.copy()  # Start at intro position
        
        # Add state tracking
        self.current_attack = None
        self.transitioning = False  # Flag for phase transition
        self.health_threshold_hit = False  # Track if we've hit phase 2 threshold
        self.explosion_sound = None  # For green attack
        self.yellow_gun_sound = None  # For yellow attack
        self.laser_sound = None  # For particle division laser beams
        self.red_gun_sound = None  # Add this for wide spread attack
        self.machine_gun_sound = None  # Add this for gauntlet phase
        self.gauntlet_sound_started = False  # Add this flag
        self.wide_spread_counter = 0  # Change from toggle to counter
        self.fade_out_started = False  # Add this flag

    def update(self, player, bullet_group, dt):
        # Handle intro sequence first
        if self.state == "intro":
            self.intro_timer -= dt
            # Calculate progress (0 to 1) using smooth step for nicer motion
            progress = 1 - (self.intro_timer / 3.0)
            # Smooth step formula for more dramatic movement
            progress = progress * progress * (3 - 2 * progress)
            
            # Interpolate position
            self.pos = self.intro_start_pos + (self.intro_target_pos - self.intro_start_pos) * progress
            
            # End intro when timer is done
            if self.intro_timer <= 0:
                self.state = "idle"
                self.pos = self.intro_target_pos.copy()
                print("Boss intro complete - fight begins!")
            return  # Skip rest of update during intro

        # Phase transition check - move before other updates
        if self.health <= 350 and not self.phase2 and not self.health_threshold_hit:
            self.health_threshold_hit = True  # Prevent multiple triggers
            if not self.in_gauntlet:
                self.transitioning = True
                self.start_gauntlet()
                self.intermission_delay = 2
                return
        
        if self.transitioning:
            if self.intermission_delay > 0:
                self.intermission_delay -= dt
                return
            if self.in_gauntlet:
                self.update_gauntlet(bullet_group, dt)
                return

        self.state_timer -= dt
        self.attack_cooldown -= dt
        if self.melee_cooldown > 0:
            self.melee_cooldown -= dt
        if self.melee_flash_timer > 0:
            self.melee_flash_timer -= dt

        if self.state == "idle":
            direction = pygame.math.Vector2(player.rect.center) - self.pos
            if direction.length() != 0:
                self.pos += direction.normalize() * 1
            if self.attack_cooldown <= 0:  # Only try to choose attack if cooldown is done
                self.choose_attack()
        elif self.state == "random_spread":
            if self.state_timer <= 0:
                self.state = "idle"
                self.current_attack = None
                self.attack_cooldown = 2 if not self.phase2 else 1.5
            else:
                if random.random() < 0.15:
                    self.fire_random_spread(bullet_group)
        elif self.state == "wide_spread":
            if self.state_timer <= 0:
                self.state = "idle"
                self.current_attack = None  # Clear current attack
                self.attack_cooldown = 2 if not self.phase2 else 1.5
            else:
                if random.random() < 0.1:
                    self.fire_wide_spread(bullet_group, player)
        elif self.state == "charge_attack":
            if self.charge_time > 0:
                self.charge_time -= dt
            else:
                if not self.exploded:
                    self.fire_charge_explosion(bullet_group)
                    self.exploded = True
                if self.state_timer <= 0:
                    self.state = "idle"
                    self.current_attack = None  # Clear current attack
                    self.attack_cooldown = 3 if not self.phase2 else 2
        elif self.state == "particle_division":
            if self.state_timer <= 0:
                self.state = "idle"
                self.current_attack = None  # Clear current attack
                self.attack_cooldown = 3 if not self.phase2 else 2
                self.is_pulsing = False
            else:
                if not self.is_pulsing and self.state_timer > 3.0:
                    self.start_particle_division(bullet_group)
                self.update_particle_division(bullet_group, dt)

        melee_range = self.radius + 30
        dist = self.pos.distance_to(pygame.math.Vector2(player.rect.center))
        if dist < melee_range and not player.rolling and self.melee_cooldown <= 0:
            print("Boss melee swing!")
            self.melee_cooldown = 2
            self.melee_flash_timer = 0.3
            if player.invulnerable_timer <= 0:
                if player.take_damage():
                    print("Player hit by melee! Hearts left:", player.hearts)
                    if player.hearts <= 0:
                        print("Game Over!")
                        return "death"  # Return death state

        # Update hit flash
        if self.hit_flash > 0:
            self.hit_flash -= dt
            flash_amount = min(1.0, self.hit_flash / 0.1)
            # Create white flash effect
            self.current_color = [
                min(255, int(200 + (255 - 200) * flash_amount)),  # R
                min(255, int(0 + (255 - 0) * flash_amount)),      # G
                min(255, int(200 + (255 - 200) * flash_amount))   # B
            ]
        else:
            self.current_color = [200, 0, 200]  # Reset to original purple

        # Update wave spawning section
        if hasattr(self, 'firing_waves') and self.firing_waves:
            self.wave_timer += dt
            
            waves_to_remove = []
            for wave in self.pending_waves:
                if self.wave_timer >= wave['delay']:
                    # Play sound if this is the wave that should trigger it
                    if wave.get('play_sound') and self.explosion_sound:
                        if self.explosion_sound and hasattr(self.explosion_sound, 'play'):
                            try:
                                self.explosion_sound.play()
                            except Exception as e:
                                print(f"Error playing boss sound: {e}")
                    
                    # Spawn all bullets in this wave
                    for bullet_data in wave['bullets']:
                        bullet = Bullet(
                            bullet_data['pos'],
                            bullet_data['velocity'],
                            bullet_data['color'],
                            bullet_data['radius']
                        )
                        bullet_group.add(bullet)
                    waves_to_remove.append(wave)
            
            # Remove spawned waves
            for wave in waves_to_remove:
                self.pending_waves.remove(wave)
                
            if not self.pending_waves:
                self.firing_waves = False
                self.wave_timer = 0

        # Add return value at end of update
        return None  # Return None if game should continue

    def choose_attack(self):
        # Don't choose a new attack if we're still in cooldown
        if self.attack_cooldown > 0:
            return
        
        # If we've used all attacks, reset the pool
        if not self.available_attacks:
            print("Resetting attack pool!")
            self.available_attacks = self.all_attacks.copy()
        
        # Choose a random attack from the remaining ones
        chosen = random.choice(self.available_attacks)
        self.available_attacks.remove(chosen)
        print(f"Chose attack: {chosen}. Remaining attacks: {self.available_attacks}")
        
        self.current_attack = chosen
        self.state = chosen
        
        # Set timers based on phase
        if chosen in ["random_spread", "wide_spread"]:
            self.state_timer = 3 if not self.phase2 else 2
            # Only play yellow gun sound at start of random spread
            if chosen == "random_spread" and self.yellow_gun_sound:
                if self.yellow_gun_sound and hasattr(self.yellow_gun_sound, 'play'):
                    try:
                        self.yellow_gun_sound.play()
                    except Exception as e:
                        print(f"Error playing boss sound: {e}")
        elif chosen == "charge_attack":
            self.state_timer = 2 if not self.phase2 else 1.5
            self.charge_time = 1.5 if not self.phase2 else 1.0
            self.exploded = False
        elif chosen == "particle_division":
            self.state_timer = 6 if not self.phase2 else 4
            self.is_pulsing = False

    def start_gauntlet(self):
        self.transitioning = True
        self.current_attack = None
        self.state = "gauntlet"
        self.pos = pygame.math.Vector2(WIDTH/2, HEIGHT/2)
        self.in_gauntlet = True
        self.gauntlet_timer = 10
        self.gauntlet_fire_timer = 0
        self.gauntlet_angle = 30
        self.gauntlet_direction = 1
        self.gauntlet_switch_timer = 2
        self.gauntlet_sound_started = False  # Reset the flag
        print("Boss teleports to center and enters intermission gauntlet! Immune for 10 seconds.")

    def update_gauntlet(self, bullet_group, dt):
        """Separate method to handle gauntlet phase"""
        self.gauntlet_timer -= dt
        self.gauntlet_fire_timer -= dt
        self.gauntlet_switch_timer -= dt
        
        # Start fading out sound in the last 0.5 seconds
        if self.gauntlet_timer <= 0.5 and not self.fade_out_started and self.machine_gun_sound:
            self.machine_gun_sound.fadeout(500)  # 500ms fade out
            self.fade_out_started = True
        
        if self.gauntlet_switch_timer <= 0:
            self.gauntlet_direction *= -1
            self.gauntlet_switch_timer = 2
        
        if self.gauntlet_fire_timer <= 0:
            self.fire_complex_gauntlet(bullet_group)
            self.gauntlet_fire_timer = self.gauntlet_fire_interval
        
        if self.gauntlet_timer <= 0:
            self.in_gauntlet = False
            self.phase2 = True
            self.transitioning = False
            self.state = "idle"
            self.attack_cooldown = 3
            self.fade_out_started = False  # Reset the flag
            print("Phase 2 begins!")

    def fire_complex_gauntlet(self, bullet_group):
        # Start machine gun sound on first bullet wave
        if not self.gauntlet_sound_started and self.machine_gun_sound:
            if self.machine_gun_sound and hasattr(self.machine_gun_sound, 'play'):
                try:
                    self.machine_gun_sound.play(-1)
                except Exception as e:
                    print(f"Error playing boss sound: {e}")
            self.gauntlet_sound_started = True

        multiplier = 1.0
        num_bullets1 = 16
        for i in range(num_bullets1):
            angle = self.gauntlet_angle + (360/num_bullets1)*i
            rad = math.radians(angle)
            speed = 8 * multiplier
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)
            bullet = Bullet(self.pos, (vx, vy), color=PURPLE, radius=5)
            bullet_group.add(bullet)
        num_bullets2 = 8
        offset = 360/(num_bullets2*2)
        for i in range(num_bullets2):
            angle = self.gauntlet_angle + offset + (360/num_bullets2)*i
            rad = math.radians(angle)
            speed = 6 * multiplier
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)
            bullet = Bullet(self.pos, (vx, vy), color=PURPLE, radius=5)
            bullet_group.add(bullet)
        self.gauntlet_angle = (self.gauntlet_angle + self.gauntlet_direction * 20) % 360

    def fire_random_spread(self, bullet_group):
        multiplier = 1.2 if self.phase2 else 1.0
        base_angles = [i * (360/12) for i in range(12)]
        for angle in base_angles:
            varied_angle = angle + random.uniform(-20, 20)
            rad = math.radians(varied_angle)
            speed = random.uniform(3, 5) * multiplier
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)
            bullet = Bullet(self.pos, (vx, vy), color=YELLOW, radius=5)
            bullet_group.add(bullet)

    def fire_wide_spread(self, bullet_group, player):
        # Play sound effect for every third spread
        if self.wide_spread_counter == 0 and self.red_gun_sound:
            if self.red_gun_sound and hasattr(self.red_gun_sound, 'play'):
                try:
                    self.red_gun_sound.play()
                except Exception as e:
                    print(f"Error playing boss sound: {e}")
        self.wide_spread_counter = (self.wide_spread_counter + 1) % 3  # Cycle 0,1,2
            
        multiplier = 1.5 if self.phase2 else 1.0
        direction = pygame.math.Vector2(player.rect.center) - self.pos
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        base_angle = math.degrees(math.atan2(direction.y, direction.x))
        spread = 60
        num_bullets = 12
        start_angle = base_angle - spread / 2
        angle_step = spread / (num_bullets - 1)
        for i in range(num_bullets):
            angle = start_angle + i * angle_step
            rad = math.radians(angle)
            speed = 4 * multiplier
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)
            bullet = Bullet(self.pos, (vx, vy), color=RED, radius=5)
            bullet_group.add(bullet)

    def fire_charge_explosion(self, bullet_group):
        # Move sound to play when first wave appears
        first_wave_delay = 0  # Adjust this to control when sound plays relative to bullets
        
        if not self.phase2:
            bullets_per_wave = 24
            num_waves = 8
            wave_delay = 0.15  # Delay between waves
            base_speed = 4
            bullet_radius = 4
            angle_offset = 0
        else:
            bullets_per_wave = 32
            num_waves = 10
            wave_delay = 0.12
            base_speed = 5
            bullet_radius = 3
            angle_offset = 5

        # Store the wave configuration for delayed spawning
        self.pending_waves = []
        for wave in range(num_waves):
            wave_bullets = []
            wave_angle_offset = (angle_offset * wave)
            
            for i in range(bullets_per_wave):
                angle = (360 / bullets_per_wave) * i + wave_angle_offset
                rad = math.radians(angle)
                speed = base_speed + (wave * 0.5)
                vx = speed * math.cos(rad)
                vy = speed * math.sin(rad)
                wave_bullets.append({
                    'pos': self.pos,
                    'velocity': (vx, vy),
                    'color': GREEN,
                    'radius': bullet_radius
                })
            
            # Add sound to first wave
            if wave == 0:
                self.pending_waves.append({
                    'bullets': wave_bullets,
                    'delay': first_wave_delay,
                    'play_sound': True  # New flag to indicate sound should play
                })
            else:
                self.pending_waves.append({
                    'bullets': wave_bullets,
                    'delay': wave * wave_delay,
                    'play_sound': False
                })

        self.firing_waves = True
        self.wave_timer = 0

    def take_damage(self):
        # Don't take damage during intro or transitions
        if self.state == "intro" or self.transitioning:
            return
        
        self.hit_flash = 0.1
        self.health -= 3
        
        # Check for win condition
        if self.health <= 0:
            print("Boss defeated!")
            return "win"  # Return win state

    def draw(self, surface):
        # Draw the boss
        color = (
            max(0, min(255, self.current_color[0])),
            max(0, min(255, self.current_color[1])),
            max(0, min(255, self.current_color[2]))
        )
        pygame.draw.circle(surface, color, (int(self.pos.x), int(self.pos.y)), self.radius)
        
        # Add immunity visual effects
        if self.state == "intro" or self.in_gauntlet:
            # Draw pulsing shield ring
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.5 + 0.5  # 0.5 to 1.0 pulse
            ring_radius = int(self.radius * (1.3 + pulse * 0.3))  # Pulsing ring size
            
            # Draw multiple shield rings for gauntlet phase
            if self.in_gauntlet:
                # Outer shield ring
                pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), ring_radius + 5, 2)
                # Inner shield ring rotating opposite direction
                shield_angle = pygame.time.get_ticks() * 0.1  # Rotation speed
                for i in range(8):  # Draw 8 arc segments
                    start_angle = shield_angle + (i * 45)
                    pygame.draw.arc(surface, (200, 200, 255), 
                                  (self.pos.x - ring_radius, self.pos.y - ring_radius,
                                   ring_radius * 2, ring_radius * 2),
                                  math.radians(start_angle), 
                                  math.radians(start_angle + 30), 2)
            else:
                # Simple ring for intro phase
                pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), ring_radius, 2)

        # Draw large health bar at top of screen
        bar_width = WIDTH * 0.7  # 70% of screen width
        bar_height = 20
        margin_top = 20  # Distance from top of screen
        
        # Background/border for health bar
        border_width = 2
        border_rect = pygame.Rect(
            (WIDTH - bar_width) / 2 - border_width,
            margin_top - border_width,
            bar_width + border_width * 2,
            bar_height + border_width * 2
        )
        pygame.draw.rect(surface, WHITE, border_rect)
        
        # Empty health bar background
        bar_rect = pygame.Rect(
            (WIDTH - bar_width) / 2,
            margin_top,
            bar_width,
            bar_height
        )
        pygame.draw.rect(surface, RED, bar_rect)
        
        # Current health
        health_ratio = self.health / 700
        current_width = bar_width * health_ratio
        current_rect = pygame.Rect(
            (WIDTH - bar_width) / 2,
            margin_top,
            current_width,
            bar_height
        )
        pygame.draw.rect(surface, GREEN, current_rect)
        
        # Draw phase indicator
        if self.phase2:
            phase_text = "PHASE 2"
            font = pygame.font.Font(None, 36)
            text_surface = font.render(phase_text, True, WHITE)
            text_rect = text_surface.get_rect(
                midtop=(WIDTH / 2, margin_top + bar_height + 5)
            )
            surface.blit(text_surface, text_rect)
        
        # Draw melee range indicator
        if self.melee_flash_timer > 0:
            melee_range = self.radius + 30
            pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), melee_range, 3)
        
        # Enhanced corner particle drawing
        if self.corner_particles:
            for i, particle in enumerate(self.corner_particles):
                pos = (int(particle.pos.x), int(particle.pos.y))
                radius = int(15 * self.corner_pulse_scale)
                
                # Draw warning effects when pulsing
                if self.is_pulsing:
                    # Draw expanding rings
                    ring_count = 3
                    max_ring_size = radius * 3
                    for ring in range(ring_count):
                        ring_progress = (pygame.time.get_ticks() * 0.001 + ring/ring_count) % 1.0
                        ring_radius = radius + (max_ring_size - radius) * ring_progress
                        ring_alpha = int(255 * (1 - ring_progress))
                        ring_surface = pygame.Surface((ring_radius*2, ring_radius*2), pygame.SRCALPHA)
                        pygame.draw.circle(ring_surface, (*PURPLE, ring_alpha), 
                                        (ring_radius, ring_radius), ring_radius, 2)
                        surface.blit(ring_surface, 
                                   (pos[0] - ring_radius, pos[1] - ring_radius))
                    
                    # Draw warning lines connecting to boss
                    if not self.corner_exploded[i]:
                        boss_center = (int(self.pos.x), int(self.pos.y))
                        line_alpha = int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 255)
                        line_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        pygame.draw.line(line_surface, (*WHITE, line_alpha), 
                                       pos, boss_center, 2)
                        surface.blit(line_surface, (0, 0))
                
                # Draw the main particle
                pygame.draw.circle(surface, particle.color, pos, radius)

    def start_particle_division(self, bullet_group):
        # Start the pulse warning
        self.is_pulsing = True
        # Play laser sound when channeling starts
        if self.laser_sound:
            if self.laser_sound and hasattr(self.laser_sound, 'play'):
                try:
                    self.laser_sound.play()
                except Exception as e:
                    print(f"Error playing boss sound: {e}")
        self.corner_pulse_timer = 0
        self.corner_pulse_scale = 1.0
        # Set up random explosion delays for each corner
        self.explosion_delays = [random.uniform(0.2, 1.5) for _ in range(4)]
        self.corner_exploded = [False] * 4  # Track which corners have exploded

    def update_particle_division(self, bullet_group, dt):
        if self.is_pulsing:
            # Update pulse effect with more dramatic pulsing
            self.corner_pulse_timer += dt
            pulse_freq = 8.0  # Faster pulsing
            # More dramatic size change (1.0 to 2.0 instead of 1.0 to 1.3)
            self.corner_pulse_scale = 1.0 + abs(math.sin(self.corner_pulse_timer * pulse_freq))
            
            # Flash color between purple and white
            flash_amount = abs(math.sin(self.corner_pulse_timer * pulse_freq))
            for particle in self.corner_particles:
                particle.radius = int(15 * self.corner_pulse_scale)
                # Interpolate between purple and white for the color
                particle.color = (
                    int(PURPLE[0] + (255 - PURPLE[0]) * flash_amount),
                    int(PURPLE[1] + (255 - PURPLE[1]) * flash_amount),
                    int(PURPLE[2] + (255 - PURPLE[2]) * flash_amount)
                )
            
            # Check for explosions
            for i in range(4):
                if not self.corner_exploded[i]:
                    self.explosion_delays[i] -= dt
                    if self.explosion_delays[i] <= 0:
                        self._create_corner_explosion(i, bullet_group)
                        self.corner_exploded[i] = True
            
            # End attack when all corners have exploded
            if all(self.corner_exploded):
                self.is_pulsing = False
                self.state = "idle"
                self.attack_cooldown = 3 if not self.phase2 else 2
                # Reset corner particles to normal
                for particle in self.corner_particles:
                    particle.radius = 15
                self.corner_pulse_scale = 1.0

    def _create_corner_explosion(self, corner_index, bullet_group):
        pos = self.corner_positions[corner_index]
        num_particles = 22 if self.phase2 else 16
        speed_range = (4, 6) if self.phase2 else (3, 5)
        
        # Create explosion particles in a circular pattern
        for i in range(num_particles):
            angle = (360 / num_particles) * i + random.uniform(-10, 10)
            speed = random.uniform(*speed_range)
            rad = math.radians(angle)
            velocity = pygame.math.Vector2(
                speed * math.cos(rad),
                speed * math.sin(rad)
            )
            
            bullet = Bullet(
                pos,
                (velocity.x, velocity.y),
                color=RED,
                radius=5
            )
            bullet_group.add(bullet)

    def start_game(self, bullet_group):
        # Called when the game starts to setup corner particles
        margin = 50
        self.corner_positions = [
            pygame.math.Vector2(COLLISION_RECT.left + margin, COLLISION_RECT.top + margin),
            pygame.math.Vector2(COLLISION_RECT.right - margin, COLLISION_RECT.top + margin),
            pygame.math.Vector2(COLLISION_RECT.left + margin, COLLISION_RECT.bottom - margin),
            pygame.math.Vector2(COLLISION_RECT.right - margin, COLLISION_RECT.bottom - margin)
        ]
        
        # Create persistent corner particles
        for pos in self.corner_positions:
            bullet = Bullet(pos, (0, 0), color=PURPLE, radius=15)
            self.corner_particles.append(bullet)
            bullet_group.add(bullet)
            self.spiral_angles.append(0)

    def reset(self):
        """Reset boss to initial state"""
        self.health = 700
        self.state = "intro"
        self.intro_timer = 3.0
        self.pos = self.intro_start_pos.copy()
        
        # Reset attack system
        self.state_timer = 0
        self.attack_cooldown = 0
        self.current_attack = None
        self.available_attacks = self.all_attacks.copy()
        
        # Reset phase transition flags
        self.phase2 = False
        self.health_threshold_hit = False
        self.transitioning = False
        self.in_gauntlet = False
        
        # Reset all timers and states
        self.charge_time = 0
        self.exploded = False
        self.gauntlet_timer = 0
        self.gauntlet_fire_timer = 0
        self.gauntlet_angle = 0
        self.melee_cooldown = 0
        self.melee_flash_timer = 0
        self.hit_flash = 0
        
        # Reset particle division state
        self.is_pulsing = False
        self.particle_division_stage = 0
        self.corner_pulse_timer = 0
        self.corner_pulse_scale = 1.0
