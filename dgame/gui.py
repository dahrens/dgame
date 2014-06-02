import pygame
from pygame.locals import *

from weakref import WeakKeyDictionary
from cPickle import dumps

import logging

class UpdateMonitor():
    def __init__(self):
        self.objects = WeakKeyDictionary()
        self.changed_objs = []
    def is_changed(self, obj):
        current_pickle = dumps(obj, -1)
        changed = False
        if obj in self.objects:
            changed = current_pickle != self.objects[obj]
        self.objects[obj] = current_pickle
        if changed:
            self.changed_objs.append(obj)
        return changed

    def reset(self):
        self.changed_objs = []

update_monitor = UpdateMonitor()

class Launcher(object):

    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.mouse.set_visible(1)

        self.modes = pygame.display.list_modes()
        self.mode = self.modes[0]
        self.fullscreen = False

        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.mode, pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.mode)

        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((0, 0, 0))
        self.clock = pygame.time.Clock()
        self.tick = 10

        self.screen.blit(self.background, (0, 0))
        pygame.display.update()

        self.menu_options = ("Start Game",
                             "Options",
                             "Quit")
        self.menu = Menu(self.menu_options, active = False)

    def run(self):
        self.game = Game((25, 25))
        self.game.update()
        done = False
        while not done:
            self.clock.tick(self.tick)
            for event in pygame.event.get():
                self.menu.handle(event)
                self.game.handle(event)
                if event.type == QUIT:
                    done = True
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.menu.activate()
                    self.game.pause = True
                elif event.type == Menu.MENUCLICKEDEVENT:
                    if event.text == "Quit":
                        done = True
                    elif event.item == 0:
                        self.game = Game((10, 10))
                        self.menu.deactivate()

                if self.menu.active:
                    self.background.fill((255, 255, 255))
                    self.menu.draw()
                else:
                    self.game.update()


            for r in update_monitor.changed_objs: pygame.display.update(r)
            update_monitor.reset()
            pygame.event.pump()


class Game(object):

    def __init__(self, size):
        self.map = Map(size)
        self.active = True

    def update(self):
        self.map.update()

    def handle(self, event):
        self.map.handle(event)

    def pause(self):
        self.pause = True

class Map (object):

    def __init__(self, size):
        self.dimension = pygame.display.get_surface().get_size()
        self.width = size[0]
        self.height = size[1]
        self.size = size
        self.tile_border = 1
        self.tile_width = self.tile_height = self.dimension[0] / (self.width + self.tile_border)
        self._map = [[Tile((x, y)) for y in range(self.height)] for x in range(self.width)]
        self.background = pygame.Surface(self.dimension).convert()
        self.background.fill((88, 88, 88))
        self.drawed = False

    @property
    def tile_size(self):
        return (self.tile_width, self.tile_height)

    def draw(self):
        pos = (self.tile_border, self.tile_border)
        logging.warning('draw called')
        for row in self._map:
            for tile in row:
                tile.rect = pygame.rect.Rect(pos, self.tile_size)
                self.background.fill(tile.color, tile.rect)
                pos = (pos[0] + self.tile_width + self.tile_border, pos[1])
            pos = (self.tile_border, pos[1] + self.tile_height + self.tile_border)

        self.drawed = True

    def update(self):
        if self.drawed == False: self.draw()
        else:
            for tile in self:
                if update_monitor.is_changed(tile):
                    self.background.fill(tile.color, tile.rect)
        screen = pygame.display.get_surface()
        screen.blit(self.background, (0, 0))

    def handle(self, event):
        for tile in self:
            tile.handle(event)

    def __iter__(self):
        from itertools import chain
        return chain.from_iterable(zip(*self._map))

class Tile(object):

    hover = False

    def __init__(self, map_position, rect = None):
        self.rect = rect
        self.map_position = map_position
        self._color = (255, 255, 255)
        self._hover_color = (255, 144, 144)

    @property
    def color(self):
        return self._color if self.hover == False else self._hover_color

    @color.setter
    def color(self, color):
        self._color = color

    def handle(self, event):
        if not self.rect: return
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.hover = True
        else:
            self.hover = False

class Menu:
    '''
    The Menu should be initalized with a list of menu entries
    it then creates a menu accordingly and manages the different
    print Settings needed
    '''

    MENUCLICKEDEVENT = USEREVENT + 1

    def __init__(self, menu_labels, font_size = 36, font_space = 4, active = True):
        '''
        The constructer uses a list of string for the menu entries,
        which need  to be created
        and a menu center if non is defined, the center of the screen is used
        '''
        screen = pygame.display.get_surface()
        self.background = pygame.Surface(screen.get_size()).convert()
        self.background.fill((0, 0, 0))

        self.font_size = font_size
        self.font_space = font_space

        self.menu_height = (self.font_size + self.font_space) * len(menu_labels)

        self.start_y = self.background.get_height() / 2 - self.menu_height / 2
        self.center_x = self.background.get_width() / 2

        self.menu_items = list()
        self.active = active

        y = self.start_y + self.font_size + self.font_space
        for label in menu_labels:
            self.menu_items.append(MenuItem(label, (self.center_x, y), self.font_size))
            y = y + self.font_size + self.font_space

    def draw_menu(self):
        for menu_item in self.menu_items:
            if menu_item.rect.collidepoint(pygame.mouse.get_pos()):
                menu_item.hover = True
            else:
                menu_item.hover = False
            menu_item.draw()
            self.background.blit(menu_item.surface, menu_item.rect)

    def draw(self):
        self.background.fill((0, 0, 0))
        self.draw_menu()
        screen = pygame.display.get_surface()
        screen.blit(self.background, (0, 0))

    def activate(self,):
        self.active = True

    def deactivate(self):
        self.active = False

    def handle(self, event):
        # only send the event if menu is active
        if event.type == MOUSEBUTTONDOWN and self.active:
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


class MenuItem (pygame.font.Font):
    '''
    The Menu Item should be derived from the pygame Font class
    '''
    def __init__(self, text, position, fontSize = 36, color = (255, 255, 255), hover_color = (0, 255, 0), background = None, antialias = 1):
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


if __name__ == "__main__":
    l = Launcher()
    l.run()
