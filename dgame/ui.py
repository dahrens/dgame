# coding=utf-8
'''
The ui module includes components that are visible in the game.
'''
from __future__ import division
import pygame
import math


class Viewport(object):
    '''The viewport of the main camera object that shows the map.'''

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
        '''Move the viewport self.scroll_speed pixels in the given direction'''
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

    def zoom(self, direction):
        '''Zoom the viewport related to the defined zoom_levels in the given direction'''
        i = self.zoom_levels.index(self.zoom_level)
        if direction == self.ZOOM_IN and len(self.zoom_levels) > i + 1:
                self.zoom_level = self.zoom_levels[i + 1]
        elif direction == self.ZOOM_OUT and 0 <= i - 1:
                self.zoom_level = self.zoom_levels[i - 1]

    def blit(self, surface, tile):
        '''Blit an image on the viewport.'''
        surface.blit(tile.image[self.zoom_level],
                     self.get_rect(tile.x, tile.y))

    def get_rect(self, x, y):
        return pygame.Rect(((x - self.x) * self.tile_width,
                            (y - self.y) * self.tile_height),
                           (int(self.tile_width),
                            int(self.tile_height)))


class Camera(pygame.sprite.Sprite):
    '''The camera shows a part of the current game environment aka map.'''

    def __init__(self, rect, env, offset = [0.0, 0.0], zoom_levels = [1.0], zoom_level = 1.0, scroll_speed = 0.5):
        super(Camera, self).__init__()
        self.env = env
        self.rect = rect
        self.image = pygame.Surface(rect.size).convert()
        self.overlay = pygame.Surface(rect.size).convert()
        self.overlay.set_alpha(64)
        self.viewport = Viewport(offset, rect.size, env.tile_size, env.size, zoom_level, zoom_levels, scroll_speed)

    @property
    def hover_tile(self):
        '''Calc and return the currently hovered tile if any else False'''
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x > self.viewport._width or mouse_y > self.viewport._height:
            return False
        x = int(((mouse_x / self.viewport.tile_width)) + self.viewport.x)
        y = int(((mouse_y / self.viewport.tile_height)) + self.viewport.y)
        return self.env.tiles[x][y]

    def update(self):
        '''Update the camera.'''
        self.image.fill((200, 200, 200))
        v_tiles, v_positions = self._get_visible()
        # draw floor
        for tile in v_tiles:
            self.viewport.blit(self.image, tile)
        # draw creatures
        for pos in self.env.creatures:
            if pos in v_positions:
                self.viewport.blit(self.image, self.env.creatures[pos].entity)
        self.update_overlay()

    def update_overlay(self):
        '''Update ui response elements.'''
        self.overlay.fill(0)
        # mark active hero
        x, y = self.env.player.active_hero.position
        pygame.draw.rect(self.overlay, (200, 200, 100), self.viewport.get_rect(x, y), 2)
        # draw possible moves
        for x, y in self.env.player.active_hero.reachable_positions:
            pygame.draw.rect(self.overlay, (155, 155, 155), self.viewport.get_rect(x, y))
        # calc and show path from active hero to hovered tile
        self.highlight_path(self.env.player.active_hero.position, self.hover_tile)
        self.image.blit(self.overlay, (0, 0))

    def highlight_path(self, start, end, color = (255, 255, 255)):
        '''Highlight a path. with color'''
        if end:
            start = self.env.get_tile(start)
            p = self.env.path_finder.findPath(start, end)
            if p:
                for n in p.nodes:
                    pygame.draw.rect(self.overlay, color, self.viewport.get_rect(n.location.x, n.location.y))

    def _get_visible(self):
        '''Get the current visible tiles.'''
        v_tiles = []
        v_positions = set()
        x_max = self.viewport.x_max if self.viewport.x_max <= self.env.width else self.env.width
        y_max = self.viewport.y_max if self.viewport.y_max <= self.env.height else self.env.height
        for x in range(self.viewport.x_min, x_max):
            for y in range(self.viewport.y_min, y_max):
                v_tiles.append(self.env.tiles[x][y])
                v_positions.add((x, y))
        return v_tiles, v_positions

    def zoom_in(self):
        self.viewport.zoom(self.viewport.ZOOM_IN)

    def zoom_out(self):
        self.viewport.zoom(self.viewport.ZOOM_OUT)

    def scroll_up(self):
        self.viewport.scroll(self.viewport.SCROLL_UP)

    def scroll_down(self):
        self.viewport.scroll(self.viewport.SCROLL_DOWN)

    def scroll_left(self):
        self.viewport.scroll(self.viewport.SCROLL_LEFT)

    def scroll_right(self):
        self.viewport.scroll(self.viewport.SCROLL_RIGHT)


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


class Entity(pygame.Rect):
    '''An entity represents moving creatures on the map.'''

    def __init__(self, rect, image):
        super(Entity, self).__init__(rect)
        self.image = image


class Floor(pygame.Rect):
    '''A tile is field on the map.'''

    def __init__(self, rect, image):
        super(Floor, self).__init__(rect)
        self.image = image
