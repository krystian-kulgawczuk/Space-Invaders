import sys
import pygame
import random
from pygame.locals import *
from game_objects import *
from starfield import *
from menu import *
from settings import *
from settings import window

pygame.display.init()
random.seed()

SCORE = 0
DIFFICULTY = 'EASY'
LEVEL = 1
ENEMY_APPEAR_CHANCE = 20
ENEMY_SHOT_CHANCE = 20

class Game():
    """It's a facade for all game modules."""
    menu_options = ['Start', 'Change difficulty', 'Quit']
    score = Score()
    difficulty = Difficulty()
    stars = initialize_stars()
    last_score = None

    @classmethod
    def draw_game_background(cls, dest_surface):
        dest_surface.fill(SKY_COLOR)
        draw_stars(dest_surface, cls.stars, SKY_COLOR)
        move_stars(cls.stars)
        draw_stars(dest_surface, cls.stars, STAR_COLOR)

    @classmethod
    def get_menu(cls, dest_surface):
        dest_surface.fill((51,51,51))
        menu = Menu(cls.menu_options, dest_surface)
        menu.draw()
        display_highscore(HIGHSCORE, dest_surface)
        return menu

    @classmethod
    def change_difficulty(cls, dest_surface):
        pygame.draw.rect(dest_surface, (51, 51, 51), [10, 450, 200, 30])
        DIFFICULTY = next(difficulty_gen)
        cls.difficulty.difficulty = DIFFICULTY
        EnemyFactory.change_enemy_strategy(DIFFICULTY)

    @classmethod
    def update_score(cls):
        cls.score.score = SCORE

    @classmethod
    def create_enemy(cls, objects):
        if random.randrange(0, ENEMY_APPEAR_CHANCE) == 0:
            EnemyFactory.create_enemy(LEVEL, objects)

    @classmethod
    def create_bonus(cls):
        BonusFactory.create_bonus()



if __name__ == '__main__':
    # initialize surface
    surface = pygame.display.set_mode(window)

    # initialize clock
    clock = pygame.time.Clock()

    # initialize game groups
    all = pygame.sprite.RenderUpdates()
    enemy_beams = pygame.sprite.Group()
    player_beams = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bonuses = pygame.sprite.Group()

    # assign default groups to each sprite class
    EnemyFactory._Enemy.containers = all, enemies
    BonusFactory._Bonus.containers = all, bonuses
    PlayerBeam.containers = all, player_beams
    EnemyBeam.containers = all, enemy_beams
    Player.containers = all
    Explosion.containers = all
    TextObject.containers = all

    #load image explosion
    img = load_image('explosion.gif')[0]
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]

    # init menu
    menu = Game.get_menu(surface)
    all.add(Game.difficulty)
    in_menu = True

    while True:
        # Game.draw_game_background(surface)
        if in_menu:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_UP:
                        menu.draw(-1)
                    if event.key == K_DOWN:
                        menu.draw(1)
                    if event.key == K_RETURN:
                        if menu.get_position() == 0:
                            in_menu = False
                            Game.difficulty.kill()
                            all.add(Game.score)
                            start_ticks = pygame.time.get_ticks()
                            player = Player()
                            last_second = 0
                        if menu.get_position() == 1:
                            Game.change_difficulty(surface)
                        if menu.get_position() == 2:
                            pygame.display.quit()
                            sys.exit()
                    if event.key == K_ESCAPE:
                        pygame.display.quit()
                        sys.exit()
                    menu.draw()
                    pygame.display.update()
                elif event.type == QUIT:
                    pygame.display.quit()
                    sys.exit()
        else:
            # calculate how many seconds passed
            seconds = int((pygame.time.get_ticks()-start_ticks) / 1000)
            # every x seconds level goes up
            if seconds % 5 == 0 and seconds != last_second:
                last_second = seconds
                LEVEL += 1

            Game.draw_game_background(surface)
            Game.create_enemy(all)
            Game.create_bonus()

            # handle player
            keystate = pygame.key.get_pressed()
            left_right = keystate[K_RIGHT] - keystate[K_LEFT]
            up_down = keystate[K_DOWN] - keystate[K_UP]
            firing = keystate[K_SPACE]
            if not player.reloading and firing and \
               player.beam_limit > len(player_beams):
                PlayerBeam(player.beam_pos())
            player.reloading = firing
            player = player.move(left_right, up_down)

            # handle enemies
            for i in enemies:
                i.shot()

            # handle collisions
            for alien in pygame.sprite.spritecollide(player, enemies, 1):
                Explosion(alien)
                if not isinstance(player, Indestructable):
                    Explosion(player)
                    save_score('highscore', SCORE)
                    for i in all:
                        i.kill()
                    all.add(Game.difficulty)
                    SCORE = 0
                    in_menu = True
                    pygame.time.wait(3000)
                    menu = Game.get_menu(surface)
                player.destroy()
                SCORE += alien.score

            for alien in pygame.sprite.groupcollide(
              enemies, player_beams, 0, 1).keys():
                if alien.health - player.beam_power <= 0:
                    alien.kill()
                    Explosion(alien)
                    SCORE += alien.score
                alien.health -= player.beam_power

            for enemy_beam in pygame.sprite.spritecollide(
              player, enemy_beams, 1):
                Explosion(enemy_beam)
                if not isinstance(player, Indestructable):
                    Explosion(player)
                    save_score('highscore', SCORE)
                    for i in all:
                        i.kill()
                    all.add(Game.difficulty)
                    SCORE = 0
                    in_menu = True
                    pygame.time.wait(3000)
                    menu = Game.get_menu(surface)
                player.destroy()

            for bonus in pygame.sprite.spritecollide(player, bonuses, 1):
                player = bonus.upgrade(player)
                SCORE += 1

            Game.update_score()


        all.update()
        dirty = all.draw(surface)
        pygame.display.update(dirty)
        pygame.display.flip()
        pygame.event.pump()
        clock.tick(60)
