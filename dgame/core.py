# coding=utf-8
'''
dgame is just a playground for python and pygame.
'''
from __future__ import division
import pygame
import sys, os, logging, math
import collections, random, yaml
from dgame.event import EventDispatcher, ActorMixin
from dgame.generator import EnvironmentGenerator

PROFILE = False
DEBUG = False

class Configuration(dict):
    '''Game configuration based on YAML files.'''

    def __init__(self, default_config = 'data/config.yaml', user_config = 'data/user_config.yaml'):
        self.user_file_path = user_config
        default_file = file(default_config, 'rb')
        user_file = file(self.user_file_path, 'rb')
        self.update(yaml.load(default_file))
        self._user_config = yaml.load(user_file)
        user_file.close()
        self.update(self._user_config)

    def update_user_config(self, *args, **kwargs):
        self._user_config.update(*args, **kwargs)
        user_file = file(self.user_file_path, 'w+')
        yaml.dump(self._user_config, user_file)
        user_file.close()
        self.update(self._user_config)

    def update(self, u):
        return self.update_dict(self, u)

    def update_dict(self, d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = self.update_dict(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d


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

    def __init__(self, offset, size, tile_size, zoom_level = 1.0, zoom_levels = []):
        self._offset = self._x, self._y = offset
        self._size = self._width, self._height = size
        self._tile_size = self._tile_width, self._tile_height = tile_size
        self.zoom_level = zoom_level
        self.zoom_levels = zoom_levels
        self._orig_width = size[0] / tile_size[0]
        self._orig_height = size[1] / tile_size[1]

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, v):
        self._offset = self._x, self._y = v

    @property
    def x(self):
        return self._x - ((self.width - self._orig_width) / 2)

    @x.setter
    def x(self, v):
        self._offset[0] = self._x = v

    @property
    def y(self):
        return self._y - ((self.height - self._orig_height) / 2)

    @y.setter
    def y(self, v):
        self._offset[1] = self._y = v

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, v):
        self._size = self._width, self._height = v

    @property
    def width(self):
        return self._width / self.tile_width

    @width.setter
    def width(self, v):
        self._size[0] = self._width = v

    @property
    def height(self):
        return self._height / self.tile_height

    @height.setter
    def height(self, v):
        self._size[1] = self._height = v

    @property
    def tile_size(self):
        return [self._tile_width * self.zoom_level, self._tile_height * self.zoom_level]

    @tile_size.setter
    def tile_size(self, v):
        self._tile_size = self._tile_width, self._tile_height = v

    @property
    def tile_width(self):
        return self._tile_width * self.zoom_level

    @tile_width.setter
    def tile_width(self, v):
        self._tile_size[0] = self._tile_width = v

    @property
    def tile_height(self):
        return self._tile_height * self.zoom_level

    @tile_height.setter
    def tile_height(self, v):
        self._tile_size[1] = self._tile_height = v

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

    SCROLL_UP = 1
    SCROLL_DOWN = 2
    SCROLL_LEFT = 3
    SCROLL_RIGHT = 4

    key = True

    def __init__(self, rect, env, offset = [0.0, 0.0], zoom_levels = [1.0], zoom_level = 1.0, scroll_speed = 0.5):
        super(Camera, self).__init__()
        self.env = env
        self.rect = rect
        self.image = pygame.Surface(rect.size).convert()
        self.scroll_speed = scroll_speed
        self.viewport = Viewport(offset, rect.size, env.tile_size, zoom_level, zoom_levels)

    def update(self):
        self.image.fill((200, 200, 200))
        for tile in self._get_visibile():
            self.viewport.blit_tile(self.image, tile)

    def handle_key(self, event):
        '''Handles all keyboard bound events.'''
        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            return self._scroll(self.SCROLL_UP)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            return self._scroll(self.SCROLL_DOWN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            return self._scroll(self.SCROLL_LEFT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self._scroll(self.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            return self._scroll(self.SCROLL_RIGHT)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_PLUS:
            return self.viewport.zoom(self.viewport.ZOOM_IN)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_KP_MINUS:
            return self.viewport.zoom(self.viewport.ZOOM_OUT)
        else:
            return False

    def _scroll(self, direction):
        '''Scrolls the map self.scroll_speed pixels in the given direction'''
        if direction == self.SCROLL_UP \
        and self.viewport.y - self.scroll_speed >= 0:
                self.viewport.y -= self.scroll_speed
        elif direction == self.SCROLL_DOWN \
        and self.viewport.y + self.scroll_speed <= self.env.height - self.viewport.height:
                self.viewport.y += self.scroll_speed
        elif direction == self.SCROLL_LEFT \
        and self.viewport.x - self.scroll_speed >= 0:
                self.viewport.x -= self.scroll_speed
        elif direction == self.SCROLL_RIGHT \
        and self.viewport.x + self.scroll_speed <= self.env.width - self.viewport.width:
                self.viewport.x += self.scroll_speed
        else: return False
        return True

    def _get_visibile(self):
        v = []
        x_max = self.viewport.x_max if self.viewport.x_max <= self.env.width else self.env.width
        y_max = self.viewport.y_max if self.viewport.y_max <= self.env.height else self.env.height
        for x in range(self.viewport.x_min, x_max):
            for y in range(self.viewport.y_min, y_max):
                v.append(self.env.tiles[x][y])
        return v


class Environment(object):

    def __init__(self, size, tile_size, biome):
        self.size = self.width, self.height = size
        self.tile_size = self.tile_width, self.tile_height = tile_size
        self.biome = biome
        self.tiles = [[self._default_tile(x, y) for y in range(self.height)] for x in range(self.width)]

    def _default_tile(self, x, y):
        return Tile(pygame.Rect((x, y), (1, 1)),
                    self.biome.unpassable)


class Tile(pygame.Rect):

    def __init__(self, rect, bg):
        super(Tile, self).__init__(rect)
        self.bg = bg


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


class Game(ActorMixin):
    '''Currently the launcher.

    TODO: seperate game from launch process, to allow saving.

    '''

    key = True

    def __init__(self):
        pygame.init()
        self.modes = pygame.display.list_modes()
        self.cfg = Configuration()
        logging.debug('cfg: {}'.format(self.cfg))

        self.screen_size = self.width , self.height = self.cfg['gfx']['resolution']
        if self.cfg['gfx']['fullscreen']:
            self.screen = pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        else:
            self.screen = pygame.display.set_mode(self.screen_size)
        self.background = pygame.Surface(self.screen_size)
        self.background.fill((200, 200, 200))
        self.screen.blit(self.background, (0, 0))

        self.font = pygame.font.SysFont('mono', 20, bold = True)
        self.clock = pygame.time.Clock()
        self.fps = self.cfg['gfx']['max_fps']
        self.playtime = 0.0

        self.biomes = self.init_biomes()
        self.dispatcher = EventDispatcher()
        self.env_generator = EnvironmentGenerator()
        self.env = self.env_generator.create(Environment(biome = self.biomes['default'],
                                                         size = self.cfg['environment']['map_size']['medium'],
                                                         tile_size = self.cfg['environment']['tile_size']))
        self.camera = Camera(pygame.Rect((0, 0), (self.width, self.height - 200)),
                             self.env,
                             zoom_levels = self.cfg['ui']['camera']['zoom_levels'],
                             zoom_level = self.cfg['ui']['camera']['zoom_level'],
                             scroll_speed = self.cfg['ui']['camera']['scroll_speed'])

        self.fps_ui = FpsLayer(self.font, self.clock, (self.width - 150, self.height - 30))

        self.dispatcher.register(self)
        self.dispatcher.register(self.camera)

        self.ui_group = pygame.sprite.LayeredUpdates(self.camera, self.fps_ui)

    def handle_key(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return True

    def run(self):
        running = True
        pygame.key.set_repeat(100, 10)
        while running:
            for event in pygame.event.get():
                running = self.dispatcher.dispatch(event)
            milliseconds = self.clock.tick(self.fps)
            self.playtime += milliseconds / 1000.0
            self.ui_group.clear(self.screen, self.background)
            self.ui_group.update()
            pygame.display.update(self.ui_group.draw(self.screen))

    def init_biomes(self):
        _b = {}
        for name, config in self.cfg['ui']['biomes'].iteritems():
            _b[name] = Biome(name, config, self.cfg['ui']['camera']['zoom_levels'])
        return _b


if __name__ == '__main__':
    def profile(function, *args, **kwargs):
        """ Returns performance statistics (as a string) for the given function."""
        def _run():
            function(*args, **kwargs)
        import cProfile as profile
        import pstats
        sys.modules['__main__'].__profile_run__ = _run
        identifier = function.__name__ + '()'
        profile.run('__profile_run__()', identifier)
        p = pstats.Stats(identifier)
        p.stream = open(identifier, 'w')
        p.sort_stats('time').print_stats(50)
        p.stream.close()
        s = open(identifier).read()
        os.remove(identifier)
        return s
    if DEBUG:
        logging.basicConfig(level = logging.DEBUG)
    if PROFILE:
        profile_result = profile(Game().run)
        print(profile_result)
    else:
        Game().run()
