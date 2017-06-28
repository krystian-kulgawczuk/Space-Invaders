import os
import random
import types
import pygame
from collections import namedtuple
from settings import window
from settings import object_size
from pygame.locals import *

SCORE = 0
DIFFICULTY = 'EASY'

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data')
screenrect = Rect(0, 0, window.width, window.height)

def load_image(name):
    """load_image(name) -> (surface, rect)"""
    image_path = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(image_path)
    except pygame.error:
        print('Cannot load image, path: {}'.format(image_path))
        raise SystemExit(str(geterror()))
    image = image.convert()
    return image, image.get_rect()

def difficulty_generator():
    """
    Generator that produces difficulties.

    warning: only use with next or functools (infinite loop)
    """
    difficulties = ['EASY', 'MEDIUM', 'HARD']
    index = 0
    while True:
        yield difficulties[index%3]
        index += 1


class SingletonMetaClass(type):
    """Metaclass that restricts object creation to only one instance."""
    def __init__(cls, name, bases, dict):
        super(SingletonMetaClass, cls).__init__(name, bases, dict)
        original_new = cls.__new__
        def my_new(cls, *args, **kwargs):
            if cls.instance == None:
                cls.instance = original_new(cls, *args, **kwargs)
            return cls.instance
        cls.instance = None
        cls.__new__ = staticmethod(my_new)


class Player(pygame.sprite.Sprite, metaclass=SingletonMetaClass):
    speed = 6
    gun_offset = 20
    beam_limit = 3
    beam_speed = 8
    beam_power = 1

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image, self.rect = load_image('player.gif')
        self.rect.topleft = 0, 0
        self.reloading = 0

    def move(self, left_right, up_down):
        """Moves player depending on which arrowkeys were pressed."""
        self.rect.move_ip(left_right*self.speed, up_down*self.speed)
        self.rect = self.rect.clamp(screenrect)
        return self

    def beam_pos(self):
        """Gets beam starting position."""
        return (self.rect.right + self.gun_offset, self.rect.centery)

    def destroy(self):
        self.kill()


class Indestructable:
    """
    Player decorator.

    If player touches enemy, only the enemy is destroyed and score is
    still assigned. Object changes transparency when it's in this state.
    """
    alpha = 63
    change = 4
    time_left = 9

    def __init__(self, decorated):
        self.decorated = decorated

    def move(self, left_right, up_down):
        """
        Changed behaviour of move method.

        Indestructable is visible as a change in transparency.
        """
        self.alpha += self.change
        if self.alpha == 255 or self.alpha == 63:
            self.time_left -= 1
            self.change = -self.change
        self.decorated.image.set_alpha(self.alpha)
        self.decorated.move(left_right, up_down)
        if self.time_left == 0:
            return self.decorated
        return self

    def beam_pos(self):
        return self.decorated.beam_pos()

    def destroy(self):
        """Player object is not destroyed when it collides with an object."""
        pass

    @property
    def reloading(self):
        return self.decorated.reloading

    @reloading.setter
    def reloading(self, value):
        self.decorated.reloading = value

    @property
    def beam_limit(self):
        return self.decorated.beam_limit

    @beam_limit.setter
    def beam_limit(self, value):
        self.decorated.beam_limit = value

    @property
    def beam_speed(self):
        return self.decorated.beam_speed

    @beam_speed.setter
    def beam_speed(self, value):
        self.decorated.beam_speed = value

    @property
    def beam_power(self):
        return self.decorated.beam_power

    @beam_power.setter
    def beam_power(self, value):
        self.decorated.beam_power = value

    @property
    def rect(self):
        return self.decorated.rect

    @rect.setter
    def rect(self, value):
        self.decorated.rect = value

    @property
    def image(self):
        return self.decorated.image

    @image.setter
    def imgae(self, value):
        self.decorated.image = value



class Beam(pygame.sprite.Sprite):
    """Object that is shot by player and enemies."""
    def __init__(self, pos, direction=1, speed=8):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = load_image('normal_beam.gif')[0]
        self.rect = self.image.get_rect(midright=pos)
        self.speed = speed * direction

    def update(self):
        """Changes position of the beam."""
        self.rect.move_ip(self.speed, 0)
        if self.rect.left >= 1024:
            self.kill()
        elif self.rect.right <= 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """Object that is shown when player or enemy is destroyed."""
    defaultlife = 12
    animcycle = 3
    images = []
    def __init__(self, actor):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.life = self.defaultlife

    def update(self):
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0: self.kill()


class PlayerBeam(Beam):
    pass

class EnemyBeam(Beam):
    pass


class EnemyFactory:
    """Factory that produces enemies based on random chance and level."""
    generator = []
    enemy_tracks = [i for i in range(0, window.height, object_size.height)]
    enemies = ['basic_enemy', 'mid_enemy', 'bulky_enemy']
    last_level = 0

    class _Enemy(pygame.sprite.Sprite):
        speed = -1
        health = 1
        score = 1
        gun_offset = -20

        def __init__(self, enemy_type, position,
                     multiplier):
            pygame.sprite.Sprite.__init__(self, self.containers)
            self.image, self.rect = load_image(enemy_type + '.gif')
            self.rect.topleft = position
            self.speed *= multiplier
            self.health *= multiplier
            self.score *= multiplier

        def update(self):
            """Changes position of the enemy."""
            self.rect.move_ip(self.speed, 0)
            if self.rect.right <= 0 or self.health <= 0:
                self.kill()

        def _beam_pos(self):
            """Gets beam starting position."""
            return (self.rect.left + self.gun_offset, self.rect.centery)

        def shot(self):
            pass

    @classmethod
    def create_enemy(cls, level, objects):
        if cls.last_level != level:
            cls.last_level = level
            if level < 4:
                cls.generator.append(0)
            elif level < 8:
                cls.generator.append(1)
            else:
                cls.generator.append(2)
        enemy_choice = random.choice(cls.generator)
        rects = [i.rect.top for i in objects]
        pos = random.choice(cls.enemy_tracks)
        if pos in rects:
            return
        chance_for_enemy = random.randrange(0, 10)
        if chance_for_enemy <= level - 1:
            return cls._Enemy(cls.enemies[enemy_choice],
                              (window.width, pos),
                               multiplier=enemy_choice + 1)

    @classmethod
    def change_enemy_strategy(cls, game_mode):
        if game_mode == 'EASY':
            cls._Enemy.shot = cls._easy_strategy
        elif game_mode == 'NORMAL':
            cls._Enemy.shot = cls._normal_strategy
        elif game_mode == 'HARD':
            cls._Enemy.shot = cls._hard_strategy


    def _easy_strategy(self):
        if random.randrange(0, 200) == 0:
            EnemyBeam(self._beam_pos(), direction=-1)

    def _normal_strategy(self):
        if random.randrange(0, 150) == 0:
            EnemyBeam(self._beam_pos(), direction=-1)

    def _hard_strategy(self):
        if random.randrange(0, 100) == 0:
            EnemyBeam(self._beam_pos(), direction=-1)



class BonusFactory:
    bonuses = []
    window_margin = 60

    class _Bonus(pygame.sprite.Sprite):
        """Base class for bonuses only to be subclassed."""
        pickup_time = 6
        alpha = 63
        change = 4

        def __init__(self):
            pygame.sprite.Sprite.__init__(self, self.containers)

        def update(self):
            self.alpha += self.change
            if self.alpha == 255 or self.alpha == 63:
                self.pickup_time -= 1
                self.change = -self.change
            if self.pickup_time == 0:
                self.kill()
            self.image.set_alpha(self.alpha)

        def set_position(self, position):
            self.rect.topleft = position

    class _BonusBeamLimit(_Bonus):
        def __init__(self, position):
            super(BonusFactory._BonusBeamLimit, self).__init__()
            self.image, self.rect = load_image('beamlimit.gif')
            self.set_position(position)

        def upgrade(self, player):
            player.beam_limit += 1
            return player

    class _BonusBeamSpeed(_Bonus):
        def __init__(self, position):
            super(BonusFactory._BonusBeamSpeed, self).__init__()
            self.image, self.rect = load_image('beamspeed.gif')
            self.set_position(position)

        def upgrade(self, player):
            player.beam_speed += 1
            return player

    class _BonusBeamPower(_Bonus):
        def __init__(self, position):
            super(BonusFactory._BonusBeamPower, self).__init__()
            self.image, self.rect = load_image('beampower.gif')
            self.set_position(position)

        def upgrade(self, player):
            player.beam_power += 1
            return player

    class _BonusIndestructable(_Bonus):
        def __init__(self, position):
            super(BonusFactory._BonusIndestructable, self).__init__()
            self.image, self.rect = load_image('indestructable.gif')
            self.set_position(position)

        def upgrade(self, player):
            return Indestructable(player)

    @classmethod
    def create_bonus(cls):
        bonus_probability = random.randrange(0, 1000)
        if bonus_probability == 0:
            width = random.randrange(cls.window_margin,
                                     window.width - cls.window_margin)
            height = random.randrange(cls.window_margin,
                                      window.height - cls.window_margin)
            position = (width, height)
            bonus = random.choice(cls.bonuses)
            return bonus(position)


class TextObject(pygame.sprite.Sprite):
    font_size = 28
    font_path = 'data/coders_crux/coders_crux.ttf'

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(self.font_path, self.font_size)
        self.color = Color(255, 255, 0)


class Score(TextObject):
    def __init__(self):
        super(Score, self).__init__()
        self.last = -1
        self.score = 0
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if self.score != self.last:
            self.last = self.score
            msg = 'Score: {}'.format(self.score)
            self.image = self.font.render(msg, 0, self.color)


class Difficulty(TextObject):
    def __init__(self):
        super(Difficulty, self).__init__()
        self.last = ''
        self.difficulty = 'EASY'
        self.update()
        self.rect = self.image.get_rect().move(10, 450)

    def update(self):
        if self.difficulty != self.last:
            self.last = self.difficulty
            msg = 'Difficulty: {}'.format(self.difficulty)
            self.image = self.font.render(msg, 0, self.color)


# initialize bonuses
BonusFactory.bonuses = [
                            BonusFactory._BonusBeamLimit,
                            BonusFactory._BonusBeamSpeed,
                            BonusFactory._BonusBeamPower,
                            BonusFactory._BonusIndestructable
                       ]
# initialize strategy
difficulty_gen = difficulty_generator()
EnemyFactory.change_enemy_strategy(next(difficulty_gen))

def _player_test():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((window.width, window.height))
    pygame.display.set_caption('player test')
    screen.fill((255, 255, 255))

    all = pygame.sprite.RenderUpdates()
    beams = pygame.sprite.Group()

    Player.containers = all
    Beam.containers = all, beams

    player = Player()

    done = 0
    while not done:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = 1
                break

        # handle player
        keystate = pygame.key.get_pressed()
        left_right = keystate[K_RIGHT] - keystate[K_LEFT]
        up_down = keystate[K_DOWN] - keystate[K_UP]
        firing = keystate[K_SPACE]
        if not player.reloading and firing and \
           player.beam_limit > len(beams):
            Beam(player.beam_pos())
        player.reloading = firing

        player.move(left_right, up_down)
        all.update()
        screen.fill((255, 255, 255))
        dirty = all.draw(screen)
        pygame.display.update(dirty)
        pygame.display.flip()
        clock.tick(60)

def _enemy_test():
    global SCORE
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(window)
    pygame.display.set_caption('player test')
    screen.fill((255, 255, 255))
    img = load_image('explosion.gif')[0]
    Explosion.images = [img, pygame.transform.flip(img, 1, 1)]

    all = pygame.sprite.RenderUpdates()
    enemy_beams = pygame.sprite.Group()
    player_beams = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    EnemyFactory._Enemy.containers = all, enemies
    BonusFactory._Bonus.containers = all
    PlayerBeam.containers = all, player_beams
    EnemyBeam.containers = all, enemy_beams
    Player.containers = all
    Explosion.containers = all
    TextObject.containers = all

    if pygame.font:
        all.add(Difficulty())
        all.add(Score())

    player = Player()
    player = Indestructable(player)

    EnemyFactory.change_enemy_strategy('EASY')
    done = 0
    while not done:
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = 1
                break
        if not int(random.random() * 10):
            EnemyFactory.create_enemy(level=1,
                                      objects=all)
            BonusFactory.create_bonus()
            for i in enemies:
                i.shot()

        for alien in pygame.sprite.spritecollide(player, enemies, 1):
            Explosion(alien)
            if not isinstance(player, Indestructable):
                Explosion(player)
            player.destroy()
            SCORE += alien.score


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

        all.update()
        screen.fill((255, 255, 255))
        dirty = all.draw(screen)
        pygame.display.update(dirty)
        # pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    _enemy_test()

