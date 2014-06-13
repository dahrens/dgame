# coding=utf-8
from __future__ import division
import pygame
import os, math, random
from dgame.event import ActorMixin

class SpriteDict(dict):
    '''
    Load a folder with images into itself.

    You can access them like this:
        sd = SpriteDict(*path)
        sd['filenamewithoutextension']

    '''

    def __init__(self, path, image_format = 'png', zoom_levels = []):
        self.folder = os.path.join(*path)
        for f in os.listdir(self.folder):
            if f.endswith('.' + image_format):
                img = pygame.image.load(os.path.join(*[self.folder, f])).convert()
                name = f.split('.')[0]
                self[name] = {}
                for zl in zoom_levels:
                    z_size = (int(img.get_rect().width * zl), int(img.get_rect().height * zl))
                    self[name][zl] = pygame.transform.scale(img, z_size)


class Biome(object):
    '''A Biome is colletion of images, that are abstracted to their use'''

    def __init__(self, name, config, zoom_levels):
        self._name = name
        self._config = config
        self._config['_all'] = []
        self.zoom_levels = zoom_levels
        for imgs in self._config.itervalues():
            self._config['_all'].extend(imgs)
        self._sheet = SpriteDict(['data', 'sprites', 'biomes', name], zoom_levels = zoom_levels)

    @property
    def unpassable(self):
        return self._sheet[self._config['unpassable'][random.randrange(0, len(self._config['unpassable']))]]

    @property
    def passable(self):
        return self._sheet[self._config['passable'][random.randrange(0, len(self._config['passable']))]]

    @property
    def wall(self):
        return self._sheet[self._config['wall'][random.randrange(0, len(self._config['wall']))]]

    @property
    def rand(self):
        return self._sheet[self._config['_all'][random.randrange(0, len(self._config['_all']))]]


class Viewport(object):

    ZOOM_IN = 1
    ZOOM_OUT = 2

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    def __init__(self, offset, size, tile_size, env_size, zoom_level = 1.0, zoom_levels = [], scroll_speed = 0.5):
        self._x, self._y = offset
        self._width, self._height = size
        self._tile_width, self._tile_height = tile_size
        self.env_width, self.env_height, = env_size
        self.zoom_level = zoom_level
        self.zoom_levels = zoom_levels
        self.scroll_speed = scroll_speed
        self._orig_width = size[0] / tile_size[0]
        self._orig_height = size[1] / tile_size[1]

    @property
    def x(self):
        x = self._x - ((self.width - self._orig_width) / 2)
        if x <= 0.0:
            return 0.0
        if x >= self.env_width - self.width:
            return self.env_width - self.width
        return x

    @x.setter
    def x(self, v):
        self._x = v

    @property
    def y(self):
        y = self._y - ((self.height - self._orig_height) / 2)
        if y <= 0.0:
            return 0.0
        if y >= self.env_height - self.height:
            return self.env_height - self.height
        return y

    @y.setter
    def y(self, v):
        self._y = v

    @property
    def width(self):
        return self._width / self.tile_width

    @width.setter
    def width(self, v):
        self._width = v

    @property
    def height(self):
        return self._height / self.tile_height

    @height.setter
    def height(self, v):
        self._height = v

    @property
    def tile_width(self):
        return self._tile_width * self.zoom_level

    @tile_width.setter
    def tile_width(self, v):
        self._tile_width = v

    @property
    def tile_height(self):
        return self._tile_height * self.zoom_level

    @tile_height.setter
    def tile_height(self, v):
        self._tile_height = v

    @property
    def x_min(self):
        return int(math.floor(self.x))

    @property
    def x_max(self):
        return int(math.ceil(self.x + (self.width)))

    @property
    def y_min(self):
        return int(math.floor(self.y))

    @property
    def y_max(self):
        return int(math.ceil(self.y + (self.height)))

    def scroll(self, direction):
        '''Scrolls the map self.scroll_speed pixels in the given direction'''
        if direction == self.SCROLL_UP \
        and self.y - self.scroll_speed >= 0:
                self._y -= self.scroll_speed
        elif direction == self.SCROLL_DOWN \
        and self.y + self.scroll_speed <= self.env_height - self.height:
                self._y += self.scroll_speed
        elif direction == self.SCROLL_LEFT \
        and self.x - self.scroll_speed >= 0:
                self._x -= self.scroll_speed
        elif direction == self.SCROLL_RIGHT \
        and self.x + self.scroll_speed <= self.env_width - self.width:
                self._x += self.scroll_speed
        else: return False
        return True

    def zoom(self, direction):
        i = self.zoom_levels.index(self.zoom_level)
        if direction == self.ZOOM_IN and len(self.zoom_levels) > i + 1:
                self.zoom_level = self.zoom_levels[i + 1]
        elif direction == self.ZOOM_OUT and 0 <= i - 1:
                self.zoom_level = self.zoom_levels[i - 1]
        else: return False
        return True

    def blit_tile(self, image, tile):
        image.blit(tile.bg[self.zoom_level],
                   pygame.Rect(((tile.x - self.x) * self.tile_width,
                                (tile.y - self.y) * self.tile_height),
                               (int(self.tile_width),
                                int(self.tile_height))))

class Camera(pygame.sprite.Sprite, ActorMixin):

    key = True

    def __init__(self, rect, env, offset = [0.0, 0.0], zoom_levels = [1.0], zoom_level = 1.0, scroll_speed = 0.5):
        super(Camera, self).__init__()
        self.env = env
        self.rect = rect
        self.image = pygame.Surface(rect.size).convert()
        self.viewport = Viewport(offset, rect.size, env.tile_size, env.size, zoom_level, zoom_levels, scroll_speed)

    def update(self):
        self.image.fill((200, 200, 200))
        for tile in self._get_visibile():
            self.viewport.blit_tile(self.image, tile)

    def handle_key(self, event):
        '''Handles all keyboard bound events.'''
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            return self.viewport.scroll(self.viewport.SCROLL_UP)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            return self.viewport.scroll(self.viewport.SCROLL_DOWN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            return self.viewport.scroll(self.viewport.SCROLL_LEFT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self.viewport.scroll(self.viewport.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self.viewport.scroll(self.viewport.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_PLUS:
            return self.viewport.zoom(self.viewport.ZOOM_IN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_MINUS:
            return self.viewport.zoom(self.viewport.ZOOM_OUT)
        else:
            return False

    def _get_visibile(self):
        v = []
        x_max = self.viewport.x_max if self.viewport.x_max <= self.env.width else self.env.width
        y_max = self.viewport.y_max if self.viewport.y_max <= self.env.height else self.env.height
        for x in range(self.viewport.x_min, x_max):
            for y in range(self.viewport.y_min, y_max):
                v.append(self.env.tiles[x][y])
        return v


class FpsLayer(pygame.sprite.Sprite):
    '''Sprite to show the FPS'''

    def __init__(self, font, clock, position):
        super(FpsLayer, self).__init__()
        self.font = font
        self.clock = clock
        self.position = position
        self.update()

    def update(self, *args):
        self.image = self.font.render(str(math.ceil(self.clock.get_fps() * 1000) / 1000) + ' fps', True, (10, 10, 10))
        self.rect = pygame.Rect(self.position, self.image.get_rect().size)


class Tile(pygame.Rect):

    def __init__(self, rect, bg):
        super(Tile, self).__init__(rect)
        self.bg = bg
