import asyncio
import pygame
import random
from game.settings import WIDTH, HEIGHT, FPS
from game.player import Player
from game.boss import Boss
from game.bullet import Bullet
from game.utils import draw_hearts, ScreenShake, Impact
from game.ui import Button, draw_title_screen, draw_death_screen

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

    all_sprites = pygame.sprite.Group()
    boss_bullets = pygame.sprite.Group()
    player_bullets = pygame.sprite.Group()
    impact_sprites = pygame.sprite.Group()

    player = Player(WIDTH/2, HEIGHT - 50)
    all_sprites.add(player)
    boss = Boss(WIDTH/2, 100)

    player_fire_delay = 0.2
    player_fire_timer = 0

    screen_shake = ScreenShake()
    render_offset = pygame.math.Vector2(0, 0)
    
    game_surface = pygame.Surface((WIDTH, HEIGHT))

    boss.start_game(boss_bullets)

    game_state = "title"  # Can be "title", "playing", or "death"
    
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
                    player.hearts = 3
                    boss.health = 700
                    boss.state = "intro"
                    boss.intro_timer = 3.0
                    boss.pos = boss.intro_start_pos.copy()
                elif exit_button.handle_event(event):
                    running = False
            
            elif game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.can_roll():
                        if player.last_dir.length() != 0:
                            player.rolling = True
                            player.roll_timer = 0.35
                            player.roll_direction = player.last_dir.copy()
                            player.image.fill(player.roll_color)

        # Update sprites (pass dt to update methods)
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
                    player_fire_timer = player_fire_delay
            else:
                player_fire_timer = 0
        else:
            player_fire_timer = 0

        boss.update(player, boss_bullets, dt)
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
                    boss.take_damage()  # Use the new take_damage method
                    # 30% chance to spawn impact effect
                    if random.random() < 0.3:
                        impact = Impact(bullet.pos)
                        impact_sprites.add(impact)
                bullet.kill()

        # Check collisions: boss bullets vs. player
        if not player.is_invulnerable():
            # Check bullet collisions
            collided = pygame.sprite.spritecollide(player, boss_bullets, True)
            if collided:
                if player.take_damage():
                    print("Player hit! Hearts left:", player.hearts)
                    # Add screen shake when hit
                    screen_shake.start_shake(0.2, 10.0)  # 0.2 seconds, intensity 10
                    if player.hearts <= 0:
                        print("Game Over!")
                        game_state = "death"

            # Check if player died from melee damage
            if player.hearts <= 0:
                print("Game Over!")
                game_state = "death"

        # Draw everything to game_surface instead of screen
        game_surface.blit(bg, (0, 0))
        all_sprites.draw(game_surface)
        boss.draw(game_surface)
        boss_bullets.draw(game_surface)
        player_bullets.draw(game_surface)
        
        # Draw impacts
        for impact in impact_sprites:
            impact.draw(game_surface)
        
        draw_hearts(game_surface, player.hearts, max_hearts=3)
        
        # Draw game_surface to screen with shake offset
        screen.fill((0, 0, 0))  # Clear screen
        screen.blit(game_surface, render_offset)
        
        pygame.display.flip()
        
        # Add this for web compatibility
        await asyncio.sleep(0)

        if game_state == "death":
            draw_death_screen(screen, death_buttons)

        if game_state == "playing":
            # Check for death condition
            if boss.health <= 0 or player.hearts <= 0:
                game_state = "death"

    pygame.quit()

asyncio.run(main())
