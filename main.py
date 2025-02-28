# /// script
# dependencies = ["pygame"]
# pygame_sdl2_flags = ["PYGAME_SDL2_AUDIODRIVER=1"]
# ///

import asyncio
import pygame
import random
import sys
from game.settings import WIDTH, HEIGHT, FPS
from game.player import Player
from game.boss import Boss
from game.bullet import Bullet
from game.utils import draw_hearts, ScreenShake, Impact
from game.ui import Button, draw_title_screen, draw_death_screen, draw_win_screen

if sys.platform == 'emscripten':
    try:
        import platform
        # Add pixelated rendering while we're at it
        platform.window.canvas.style.imageRendering = "pixelated"
    except Exception as e:
        print("Platform setup failed:", e)

async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boss Battle Simulation")
    clock = pygame.time.Clock()

    # Load background image from assets/art folder
    try:
        bg = pygame.image.load("assets/art/background.jpg").convert()
    except:
        print("Error loading background image")
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill((0, 0, 0))
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

    # Create a function to load sounds after user interaction
    async def load_sounds():
        try:
            sounds = {
                'player_gun': "assets/sfx/player_gun.ogg",
                'boss_explosion': "assets/sfx/green_gun.ogg", 
                'yellow_gun': "assets/sfx/yellow_gun.ogg",
                'laser': "assets/sfx/lazer.ogg",
                'red_gun': "assets/sfx/red_gun.ogg",
                'machine_gun': "assets/sfx/machine_gun.ogg"
            }
            
            loaded_sounds = {}
            for name, path in sounds.items():
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(0.3)  # Default volume
                    loaded_sounds[name] = sound
                except Exception as e:
                    print(f"Failed to load sound {name}: {e}")
                    loaded_sounds[name] = None
                
            return loaded_sounds
        except Exception as e:
            print(f"Error in load_sounds: {e}")
            return {}

    # Initialize sound variables
    player_gun_sound = None
    boss_explosion_sound = None
    yellow_gun_sound = None
    laser_sound = None
    red_gun_sound = None
    machine_gun_sound = None
    sounds_loaded = False

    all_sprites = pygame.sprite.Group()
    boss_bullets = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    impact_sprites = pygame.sprite.Group()

    player = Player(WIDTH/2, HEIGHT - 50)
    all_sprites.add(player)
    boss = Boss(WIDTH/2, 100)
    boss.explosion_sound = boss_explosion_sound
    boss.yellow_gun_sound = yellow_gun_sound
    boss.laser_sound = laser_sound
    boss.red_gun_sound = red_gun_sound
    boss.machine_gun_sound = machine_gun_sound

    player_fire_delay = 0.2
    player_fire_timer = 0

    screen_shake = ScreenShake()
    render_offset = pygame.math.Vector2(0, 0)
    
    game_surface = pygame.Surface((WIDTH, HEIGHT))

    boss.start_game(boss_bullets)

    game_state = "title"  # Can be "title", "playing", "death" or "win"
    
    # Create buttons for death screen
    button_width = 200
    button_height = 50
    button_y = HEIGHT * 2/3
    retry_button = Button(
        WIDTH/2 - button_width - 20, button_y,
        button_width, button_height,
        "Try Again"
    )
    exit_button = Button(
        WIDTH/2 + 20, button_y,
        button_width, button_height,
        "Exit"
    )
    death_buttons = [retry_button, exit_button]

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_state == "title":
                if event.type == pygame.MOUSEBUTTONDOWN and not sounds_loaded:
                    # Load sounds after first click
                    sound_dict = await load_sounds()
                    player_gun_sound = sound_dict.get('player_gun')
                    boss_explosion_sound = sound_dict.get('boss_explosion')
                    yellow_gun_sound = sound_dict.get('yellow_gun')
                    laser_sound = sound_dict.get('laser')
                    red_gun_sound = sound_dict.get('red_gun')
                    machine_gun_sound = sound_dict.get('machine_gun')
                    
                    # Update boss sounds
                    boss.explosion_sound = boss_explosion_sound
                    boss.yellow_gun_sound = yellow_gun_sound
                    boss.laser_sound = laser_sound
                    boss.red_gun_sound = red_gun_sound
                    boss.machine_gun_sound = machine_gun_sound
                    sounds_loaded = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game_state = "playing"
                    # Reset game state if needed
                    player.hearts = 3
                    boss.health = 700
                    boss.state = "intro"
                    boss.intro_timer = 3.0
                    boss.pos = boss.intro_start_pos.copy()
            
            elif game_state == "death":
                if retry_button.handle_event(event):
                    game_state = "playing"
                    # Reset game state
                    player.reset()
                    boss.reset()
                    # Clear all bullets
                    boss_bullets.empty()
                    player_bullets.empty()
                elif exit_button.handle_event(event):
                    running = False
            
            elif game_state == "win":
                draw_win_screen(screen)
                # Optional: Add a way to restart or exit
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            # Reset game state
                            game_state = "title"
                            player.reset()
                            boss.reset()
                            boss_bullets.empty()
                            player_bullets.empty()
            
            elif game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.can_roll():
                        if player.last_dir.length() != 0:
                            player.rolling = True
                            player.roll_timer = 0.35
                            player.roll_direction = player.last_dir.copy()
                            player.image.fill(player.roll_color)

        # Clear screen at start of frame
        screen.fill((0, 0, 0))

        if game_state == "title":
            draw_title_screen(screen)
        
        elif game_state == "death":
            draw_death_screen(screen, death_buttons)
        
        elif game_state == "win":
            draw_win_screen(screen)
        
        elif game_state == "playing":
            # Update game logic only when playing
            all_sprites.update(dt)
            
            if not player.rolling:
                mouse_pressed = pygame.mouse.get_pressed()[0]
                if mouse_pressed:
                    player_fire_timer -= dt
                    if player_fire_timer <= 0:
                        mouse_pos = pygame.mouse.get_pos()
                        direction = pygame.math.Vector2(mouse_pos) - pygame.math.Vector2(player.rect.center)
                        if direction.length() != 0:
                            direction = direction.normalize()
                        bullet_speed = 10
                        velocity = direction * bullet_speed
                        bullet = Bullet(player.rect.center, velocity, color=player.base_color, radius=5)
                        player_bullets.add(bullet)
                        if player_gun_sound and sounds_loaded:
                            try:
                                player_gun_sound.play()
                            except Exception as e:
                                print(f"Error playing sound: {e}")
                        player_fire_timer = player_fire_delay
                else:
                    player_fire_timer = 0
            else:
                player_fire_timer = 0

            # Move boss update after player input but before collision checks
            boss_state = boss.update(player, boss_bullets, dt)
            if boss_state == "death":
                game_state = "death"
                continue

            boss_bullets.update()
            player_bullets.update()

            # Update screen shake
            render_offset = screen_shake.update(dt)

            # Update impacts
            impact_sprites.update(dt)

            # Check collisions: player bullets vs. boss
            boss_rect = pygame.Rect(boss.pos.x - boss.radius, boss.pos.y - boss.radius, boss.radius*2, boss.radius*2)
            for bullet in player_bullets:
                if boss_rect.colliderect(bullet.rect):
                    if not boss.in_gauntlet:
                        result = boss.take_damage()
                        if result == "win":
                            game_state = "win"
                            break
                        if random.random() < 0.3:
                            impact = Impact(bullet.pos)
                            impact_sprites.add(impact)
                    bullet.kill()

            # Check collisions: boss bullets vs. player
            if not player.is_invulnerable():
                collided = pygame.sprite.spritecollide(player, boss_bullets, True)
                if collided:
                    if player.take_damage():
                        print("Player hit! Hearts left:", player.hearts)
                        screen_shake.start_shake(0.2, 10.0)
                        if player.hearts <= 0:
                            print("Game Over!")
                            game_state = "death"

            # Draw game elements
            game_surface.blit(bg, (0, 0))
            all_sprites.draw(game_surface)
            boss.draw(game_surface)
            boss_bullets.draw(game_surface)
            player_bullets.draw(game_surface)
            
            for impact in impact_sprites:
                impact.draw(game_surface)
            
            draw_hearts(game_surface, player.hearts, max_hearts=3)
            
            # Draw game_surface to screen with shake offset
            screen.blit(game_surface, render_offset)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())
