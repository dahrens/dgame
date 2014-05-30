import pygame
from pygame.locals import *
import logging

class Launcher(object):

    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.mouse.set_visible(1)

        self.modes = pygame.display.list_modes()
        self.mode = self.modes[0]
        self.screen = None
        self.fullscreen = False
        self.done = False

        self.init_screen()

        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((0, 0, 0))
        self.clock = pygame.time.Clock()
        self.tick = 10

        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

        self.menu_options = ("Start Game",
                             "Quit")
        self.menu = Menu(self.menu_options)
        self.menu.draw_menu()

    def run(self):
        while not self.done:
            self.clock.tick(self.tick)
            for event in pygame.event.get():
                self.menu.handleEvent(event)
                if event.type == QUIT:
                    self.done = True
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.menu.activate()
                elif event.type == Menu.MENUCLICKEDEVENT:
                    if event.text == "Quit":
                        self.done = True
                    elif event.item == 0:
                        self.menu.deactivate()

                if self.menu.isActive():
                    self.menu.draw_menu()
                else:
                    self.background.fill((0, 0, 0))

                pygame.display.flip()

    def init_screen(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.mode, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.mode)


class MenuItem (pygame.font.Font):
    '''
    The Menu Item should be derived from the pygame Font class
    '''
    def __init__(self, text, position, fontSize = 36, color = (255, 255, 255), hover_color = (255, 0, 255), background = None, antialias = 1):
        self.text = text
        self.position = position
        self._color = color
        self._hover_color = hover_color
        self.hover = False
        self.background = background
        self.antialias = antialias
        super(MenuItem, self).__init__(None, fontSize)
        self.draw()

    def draw(self):
        if self.background == None:
            self.surface = self.render(self.text, self.antialias, self.color)
        else:
            self.surface = self.render(self.text, self.antialias, self.color, self.background)
        self.rect = self.surface.get_rect(centerx = self.position[0], centery = self.position[1])

    @property
    def color(self):
        return self._color if self.hover == False else self._hover_color

    @color.setter
    def color(self, color):
        self._color = color

class Menu:
    '''
    The Menu should be initalized with a list of menu entries
    it then creates a menu accordingly and manages the different
    print Settings needed
    '''

    MENUCLICKEDEVENT = USEREVENT + 1

    def __init__(self, menu_labels, font_size = 36, font_space = 4):
        '''
        The constructer uses a list of string for the menu entries,
        which need  to be created
        and a menu center if non is defined, the center of the screen is used
        '''
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.background = pygame.Surface(screen.get_size()).convert()
        self.background.fill((0, 0, 0))

        self.font_size = font_size
        self.font_space = font_space

        self.menu_height = (self.font_size + self.font_space) * len(menu_labels)

        self.start_y = self.background.get_height() / 2 - self.menu_height / 2
        self.center_x = self.background.get_width() / 2

        self.menu_items = list()
        self.active = True

        y = self.start_y + self.font_size + self.font_space
        for label in menu_labels:
            self.menu_items.append(MenuItem(label, (self.center_x, y), self.font_size))
            y = y + self.font_size + self.font_space

    def draw_menu_content(self):
        for menu_item in self.menu_items:
            if menu_item.rect.collidepoint(pygame.mouse.get_pos()):
                menu_item.hover = True
            else:
                menu_item.hover = False
            menu_item.draw()
            self.background.blit(menu_item.surface, menu_item.rect)

    def draw_menu(self):
        self.background.fill((0, 0, 0))
        self.draw_menu_content()
        screen = pygame.display.get_surface()
        screen.blit(self.background, (0, 0))

    def isActive(self):
        return self.active

    def activate(self,):
        self.active = True

    def deactivate(self):
        self.active = False

    def handleEvent(self, event):
        # only send the event if menu is active
        if event.type == MOUSEBUTTONDOWN and self.isActive():
            logging.warning('i react')
            # initiate with menu Item 0
            curItem = 0
            # get x and y of the current event
            eventX = event.pos[0]
            eventY = event.pos[1]
            # for each text position
            for menu_item in self.menu_items:
                text_rect = menu_item.rect
                # check if current event is in the text area
                if eventX > text_rect.left and eventX < text_rect.right \
                and eventY > text_rect.top and eventY < text_rect.bottom:
                    # if so fire new event, which states which menu item was clicked
                    menuEvent = pygame.event.Event(self.MENUCLICKEDEVENT, item = curItem, text = menu_item.text)
                    pygame.event.post(menuEvent)
                curItem = curItem + 1


if __name__ == "__main__":
    l = Launcher()
    l.run()
