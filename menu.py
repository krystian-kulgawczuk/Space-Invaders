import pygame
from pygame.locals import *

if not pygame.display.get_init():
    pygame.display.init()

if not pygame.font.get_init():
    pygame.font.init()


def get_scores(filename):
    scores = []
    with open('data/' + filename + '.txt') as f:
        for line in f:
            scores.append(int(line))
    scores.sort()
    return scores

def display_highscore(filename, dest_surface):
    scores = get_scores(filename)
    font_size = 15
    myfont = pygame.font.SysFont("monospace", font_size)
    label = myfont.render('Highscore:', 1, (255, 255, 0))
    dest_surface.blit(label, (10, 10))
    for i, score in enumerate(reversed(scores)):
        label = myfont.render(str(i + 1) + ': ' + str(score), 1, (255, 255, 0))
        dest_surface.blit(label, (10, 10 + font_size + font_size*i))

def save_score(filename, score):
    scores = get_scores(filename)
    if len(scores) == 5 and score > min(scores):
        scores[0] = score
    elif len(scores) < 5:
        scores.append(score)
    with open('data/' + filename + '.txt', 'w') as f:
        for i in scores:
            f.write(str(i) + '\n')

class Menu:
    lst = []
    fields = []
    font_size = 32
    font_path = 'data/coders_crux/coders_crux.ttf'
    font = pygame.font.Font
    dest_surface = pygame.Surface
    field_count = 0
    background_color = (51, 51, 51)
    text_color =  (255, 255, 153)
    select_color = (153, 102, 255)
    select_position = 0
    paste_position = (0, 0)
    menu_width = 0
    menu_height = 0

    class Field:
        text = ''
        field = pygame.Surface
        field_rect = pygame.Rect
        select_rect = pygame.Rect

    def __init__(self, lst, dest_surface):
        self.lst = lst
        self.dest_surface = dest_surface
        self.field_count = len(self.lst)
        self.create_structure()

    def move_menu(self, top, left):
        self.paste_position = (top, left)

    def set_colors(self, text, selection, background):
        self.background_color = background
        self.text_color =  text
        self.select_color = selection

    def set_fontsize(self,font_size):
        self.font_size = font_size

    def set_font(self, path):
        self.font_path = path

    def get_position(self):
        return self.select_position

    def draw(self, move=0):
        if move:
            self.select_position += move
            if self.select_position == -1:
                self.select_position = self.field_count - 1
            self.select_position %= self.field_count
        menu = pygame.Surface((self.menu_width, self.menu_height))
        menu.fill(self.background_color)
        select_rect = self.fields[self.select_position].select_rect
        pygame.draw.rect(menu, self.select_color, select_rect)

        for i in range(self.field_count):
            menu.blit(self.fields[i].field, self.fields[i].field_rect)
        self.dest_surface.blit(menu, self.paste_position)
        return self.select_position

    def create_structure(self):
        shift = 0
        self.menu_height = 0
        self.font = pygame.font.Font(self.font_path, self.font_size)
        for i in range(self.field_count):
            self.fields.append(self.Field())
            self.fields[i].text = self.lst[i]
            self.fields[i].field = self.font.render(self.fields[i].text, 1, self.text_color)

            self.fields[i].field_rect = self.fields[i].field.get_rect()
            shift = int(self.font_size * 0.2)

            height = self.fields[i].field_rect.height
            self.fields[i].field_rect.left = shift
            self.fields[i].field_rect.top = shift + (shift * 2 + height) * i

            width = self.fields[i].field_rect.width + shift * 2
            height = self.fields[i].field_rect.height + shift * 2
            left = self.fields[i].field_rect.left - shift
            top = self.fields[i].field_rect.top - shift

            self.fields[i].select_rect = (left, top , width, height)
            if width > self.menu_width:
                    self.menu_width = width
            self.menu_height += height
        x = self.dest_surface.get_rect().centerx - self.menu_width / 2
        y = self.dest_surface.get_rect().centery - self.menu_height / 2
        mx, my = self.paste_position
        self.paste_position = (x + mx, y + my)



if __name__ == "__main__":
    import sys
    surface = pygame.display.set_mode((1024,480))
    surface.fill((51,51,51))
    menu = Menu(['Start','Change Difficulty','Quit'], surface)
    menu.draw()#necessary
    save_score('highscore', 56)
    display_highscore('highscore', surface)
    pygame.key.set_repeat(199,69)#(delay,interval)
    pygame.display.update()
    while 1:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_UP:
                    menu.draw(-1) #here is the Menu class function
                if event.key == K_DOWN:
                    menu.draw(1) #here is the Menu class function
                if event.key == K_RETURN:
                    if menu.get_position() == 2:#here is the Menu class function
                        pygame.display.quit()
                        sys.exit()
                if event.key == K_ESCAPE:
                    pygame.display.quit()
                    sys.exit()
                pygame.display.update()
            elif event.type == QUIT:
                pygame.display.quit()
                sys.exit()
        pygame.time.wait(8)

