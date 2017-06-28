#!/usr/bin/env python

import random, math, pygame
from pygame.locals import *
from settings import window

#constants
NUMSTARS = 200
STAR_COLOR = 255, 240, 200
SKY_COLOR = 20, 20, 40


def init_star():
    """Creates new star values."""
    dir = -random.random()
    velmult = 20
    vel = [dir * velmult, 0]
    return vel, [window.width, random.randrange(window.height)]


def initialize_stars():
    """Creates a new starfield."""
    stars = []
    for x in range(NUMSTARS):
        star = init_star()
        stars.append(star)
    move_stars(stars)
    return stars


def draw_stars(surface, stars, color):
    """Used to draw (and clear) the stars."""
    for vel, pos in stars:
        pos = (int(pos[0]), int(pos[1]))
        surface.set_at(pos, color)


def move_stars(stars):
    """Animate the star values."""
    for vel, pos in stars:
        pos[0] = pos[0] + vel[0]
        pos[1] = pos[1] + vel[1]
        if not 0 <= pos[0] <= window.width:
            vel[:], pos[:] = init_star()


def test():
    """Test for starfield."""
    random.seed()
    stars = initialize_stars()
    clock = pygame.time.Clock()
    #initialize and prepare screen
    pygame.init()
    screen = pygame.display.set_mode(window)
    pygame.display.set_caption('Starfield test')
    screen.fill(SKY_COLOR)

    done = 0
    while not done:
        draw_stars(screen, stars, SKY_COLOR)
        move_stars(stars)
        draw_stars(screen, stars, STAR_COLOR)
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = 1
                break
        clock.tick(50)

if __name__ == '__main__':
    test()


